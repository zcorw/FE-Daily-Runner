import argparse
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from fe_daily.config import RunMode, load_settings
from fe_daily.health_check import check_runtime_health
from fe_daily.openai_generator import OpenAIGenerator
from fe_daily.question_bank_client import QuestionBankClient
from fe_daily.telegram_notifier import TelegramNotifier
from fe_daily.workflow import run_daily_workflow


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def resolve_target_date(
    args: argparse.Namespace,
    *,
    timezone_name: str = "Asia/Tokyo",
    now: datetime | None = None,
) -> date:
    if args.target_date is not None:
        return args.target_date

    if args.today:
        timezone = ZoneInfo(timezone_name)
        current_time = now or datetime.now(tz=timezone)
        return current_time.astimezone(timezone).date()

    raise ValueError("target date is not set")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="daily_publish.py",
        description="Generate FE daily study pages.",
    )

    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument("--date", dest="target_date", type=parse_date)
    date_group.add_argument("--today", action="store_true")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", dest="run_mode", action="store_const", const=RunMode.DRY_RUN)
    mode_group.add_argument("--write", dest="run_mode", action="store_const", const=RunMode.WRITE)
    mode_group.add_argument("--notify", dest="run_mode", action="store_const", const=RunMode.NOTIFY)

    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--input", dest="input_path", type=Path)

    parser.set_defaults(run_mode=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.render_only and args.input_path is None:
        parser.error("--render-only requires --input")

    if args.input_path is not None and not args.render_only:
        parser.error("--input requires --render-only")

    maintenance_operation = args.health_check or args.validate_config or args.render_only
    if maintenance_operation and args.run_mode is not None:
        parser.error("--dry-run, --write, and --notify cannot be combined with maintenance operations")

    command_without_date = args.health_check or args.validate_config or args.render_only
    if not command_without_date and args.target_date is None and not args.today:
        parser.error("one of --date or --today is required")

    if args.run_mode is None:
        args.run_mode = RunMode.DRY_RUN

    return args


def validate_config(settings_overrides: dict[str, Any] | None = None) -> int:
    overrides = settings_overrides or {}
    try:
        settings = load_settings(**overrides)
    except ValidationError as exc:
        print(f"Config invalid: {exc}")
        return 2

    print(f"QUESTION_BANK_SERVICE_URL={settings.question_bank_service_url}")
    print(f"RUN_MODE={settings.run_mode.value}")
    print(f"EXISTING_PAGE_POLICY={settings.existing_page_policy.value}")

    if settings.openai_api_key is None:
        print("OPENAI_API_KEY missing; real generation will be unavailable outside dry-run validation.")

    if settings.telegram_bot_token is None or settings.telegram_chat_id is None:
        print("Telegram config missing; notifications will be skipped.")

    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    settings_overrides: dict[str, Any] | None = None,
    question_bank_client_factory: Any | None = None,
    generator_factory: Any | None = None,
    telegram_notifier_factory: Any | None = None,
    workflow_runner: Any | None = None,
) -> int:
    args = parse_args(argv)

    if args.validate_config:
        return validate_config(settings_overrides)

    if args.health_check:
        overrides = settings_overrides or {}
        try:
            settings = load_settings(**overrides)
        except ValidationError as exc:
            print(f"Config invalid: {exc}")
            return 2

        factory = question_bank_client_factory or (
            lambda loaded_settings: QuestionBankClient(
                loaded_settings.question_bank_service_url,
                timeout=loaded_settings.question_bank_timeout_seconds,
            )
        )
        client = factory(settings)
        try:
            result = check_runtime_health(client)
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()
        print(result.message)
        return result.exit_code

    if args.render_only:
        print(f"Render-only is not implemented yet: {args.input_path}")
        return 0

    overrides = settings_overrides or {}
    try:
        settings = load_settings(**overrides)
        target_date = resolve_target_date(args, timezone_name=settings.tz)
    except (ValidationError, ValueError) as exc:
        print(f"Config invalid: {exc}")
        return 2

    factory = question_bank_client_factory or (
        lambda loaded_settings: QuestionBankClient(
            loaded_settings.question_bank_service_url,
            timeout=loaded_settings.question_bank_timeout_seconds,
        )
    )
    generator_builder = generator_factory or (lambda loaded_settings: OpenAIGenerator(settings=loaded_settings))
    notifier_builder = telegram_notifier_factory or _build_telegram_notifier
    runner = workflow_runner or run_daily_workflow

    client = factory(settings)
    try:
        result = runner(
            settings=settings,
            target_date=target_date,
            run_mode=args.run_mode,
            plan_path=settings.study_plan_path,
            weak_points=settings.weak_points_path.read_text(encoding="utf-8"),
            mistake_log=settings.mistake_log_path.read_text(encoding="utf-8"),
            recent_progress=settings.progress_context_path.read_text(encoding="utf-8"),
            question_client=client,
            generator=generator_builder(settings),
            telegram_notifier=notifier_builder(settings),
        )
    except Exception as exc:
        print(f"Workflow failed: {exc}")
        return 1
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    print(f"Workflow {result.status}: {result.target_date.isoformat()}")
    if result.notification_status != "not-run":
        print(f"Notification: {result.notification_status}")
    return 0


def _build_telegram_notifier(settings: Any) -> TelegramNotifier | None:
    if settings.telegram_bot_token is None or settings.telegram_chat_id is None:
        return None
    return TelegramNotifier(
        bot_token=settings.telegram_bot_token.get_secret_value(),
        chat_id=settings.telegram_chat_id.get_secret_value(),
    )
