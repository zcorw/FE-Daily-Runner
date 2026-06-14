from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Protocol

from fe_daily.config import DailyRunnerSettings, RunMode
from fe_daily.content_validation import validate_daily_html, validate_learning_content_quality, validate_question_facts
from fe_daily.dry_run import DryRunArtifactPaths, write_dry_run_artifacts
from fe_daily.health_check import HealthStatus, check_runtime_health
from fe_daily.output_schema import DailyLearningContent
from fe_daily.output_writer import atomic_write_text
from fe_daily.page_renderer import render_daily_page, render_index_page
from fe_daily.paths import ExistingOutputDecision, output_targets, resolve_existing_output
from fe_daily.progress_context import upsert_progress_entry
from fe_daily.prompt_builder import build_generation_payload
from fe_daily.question_details import load_required_details
from fe_daily.question_selection import (
    build_candidate_search_payloads,
    parse_practice_focus,
    select_subject_a_questions,
)
from fe_daily.study_plan import StudyPlanEntry, select_study_plan_entry
from fe_daily.run_log import write_run_log
from fe_daily.state import update_daily_state
from fe_daily.telegram_notifier import TelegramNotifier, render_telegram_message


class WorkflowQuestionClient(Protocol):
    def health(self) -> dict[str, Any]:
        pass

    def search_candidates(self, payload: dict[str, Any]) -> dict[str, Any]:
        pass

    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        pass


class WorkflowGenerator(Protocol):
    def generate(self, payload: dict[str, Any]) -> DailyLearningContent:
        pass


class WorkflowNotifier(Protocol):
    def send_html_message(self, html: str) -> Any:
        pass


@dataclass(frozen=True)
class WorkflowResult:
    status: str
    target_date: date
    plan_source: str
    dry_run_artifacts: DryRunArtifactPaths | None = None
    notification_status: str = "not-run"


def run_daily_workflow(
    *,
    settings: DailyRunnerSettings,
    target_date: date,
    run_mode: RunMode,
    plan_path: str,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
    question_client: WorkflowQuestionClient,
    generator: WorkflowGenerator,
    telegram_notifier: WorkflowNotifier | None = None,
) -> WorkflowResult:
    target_paths = output_targets(settings.output_dir, target_date)
    if run_mode in (RunMode.WRITE, RunMode.NOTIFY):
        existing_decision = resolve_existing_output(target_paths.daily_page, settings.existing_page_policy)
        if existing_decision is ExistingOutputDecision.SKIP:
            return WorkflowResult(
                status="skipped",
                target_date=target_date,
                plan_source="not-run",
            )

    health = check_runtime_health(question_client)
    if health.status is not HealthStatus.OK:
        raise RuntimeError(health.message)

    plan_entry = select_study_plan_entry(
        plan_path,
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )
    plan_payload = _plan_payload(plan_entry)

    focus_targets = parse_practice_focus(plan_entry.practice_focus)
    candidate_payloads = build_candidate_search_payloads(focus_targets)
    candidate_groups = [
        question_client.search_candidates(payload).get("questions", [])
        for payload in candidate_payloads
    ]
    selected_questions = select_subject_a_questions(candidate_groups, required_count=10)
    details = load_required_details(
        question_client,
        [question["url"] for question in selected_questions],
    )

    generation_payload = build_generation_payload(
        plan=plan_payload,
        weak_points=weak_points,
        progress_summary=recent_progress,
        mistake_log=mistake_log,
        questions=details,
    )
    content = generator.generate(generation_payload)
    _restore_plan_fields(content, plan_entry)

    validate_question_facts(content, details)
    validate_learning_content_quality(content, _expected_plan(plan_entry))
    page_url = f"/daily/{target_date:%Y-%m-%d}/"
    html = render_daily_page(content, page_url=page_url, template_dir=settings.template_dir)
    validate_daily_html(html, content, page_url=page_url)

    if run_mode is RunMode.DRY_RUN:
        artifacts = write_dry_run_artifacts(
            output_dir=settings.output_dir,
            target_date=target_date,
            raw_output=content.model_dump(mode="json"),
            validated_output=content.model_dump(mode="json"),
            preview_html=html,
        )
        return WorkflowResult(
            status="success",
            target_date=target_date,
            plan_source=plan_entry.plan_source,
            dry_run_artifacts=artifacts,
        )

    if run_mode in (RunMode.WRITE, RunMode.NOTIFY):
        atomic_write_text(target_paths.daily_page, html)
        workspace_root = settings.output_dir.parent
        index_html = render_index_page(
            [
                {
                    "date": target_date.isoformat(),
                    "title": content.main_theme,
                    "url": page_url,
                }
            ],
            current_strategy=plan_entry.practice_focus,
            updated_at=datetime.now(timezone.utc).isoformat(),
            template_dir=settings.template_dir,
        )
        atomic_write_text(target_paths.index_page, index_html)
        upsert_progress_entry(workspace_root / "personal" / "progress.md", content, page_url=page_url)
        update_daily_state(
            state_path=workspace_root / "state" / "daily_state.json",
            legacy_state_path=workspace_root / ".codex" / "daily_state.json",
            target_date=target_date,
            daily_page=page_url,
            topics=[content.main_theme],
            question_count=len(content.questions),
            status="success",
        )
        notification_status = "not-run"
        if run_mode is RunMode.NOTIFY and (
            settings.telegram_bot_token is None or settings.telegram_chat_id is None
        ):
            notification_status = "skipped: missing env"
        elif run_mode is RunMode.NOTIFY:
            notifier = telegram_notifier or TelegramNotifier(
                bot_token=settings.telegram_bot_token.get_secret_value(),
                chat_id=settings.telegram_chat_id.get_secret_value(),
            )
            message = render_telegram_message(
                date=target_date.isoformat(),
                main_theme=content.main_theme,
                page_url=_absolute_page_url(settings, page_url),
                template_dir=settings.template_dir,
            )
            send_result = notifier.send_html_message(message)
            notification_status = getattr(send_result, "status", "sent")
        write_run_log(
            log_root=workspace_root / "logs" / "daily_publish",
            target_date=target_date,
            started_at=datetime.now(timezone.utc),
            run_mode=run_mode.value,
            question_count=len(content.questions),
            output_paths=[str(target_paths.daily_page), str(target_paths.index_page)],
            plan_source=plan_entry.plan_source,
            notification_status=notification_status,
            status="success",
            errors=[],
        )
        return WorkflowResult(
            status="success",
            target_date=target_date,
            plan_source=plan_entry.plan_source,
            notification_status=notification_status,
        )

    raise NotImplementedError(f"workflow run mode is not implemented yet: {run_mode.value}")


def _plan_payload(plan_entry: StudyPlanEntry) -> dict[str, Any]:
    return {
        "date": plan_entry.date.isoformat(),
        "main_theme": plan_entry.main_theme,
        "reading_assignment": plan_entry.reading_assignment,
        "practice_focus": plan_entry.practice_focus,
        "plan_source": plan_entry.plan_source,
    }


def _expected_plan(plan_entry: StudyPlanEntry) -> dict[str, Any]:
    return {
        "date": plan_entry.date.isoformat(),
        "main_theme": plan_entry.main_theme,
        "reading_assignment": plan_entry.reading_assignment,
        "practice_focus": plan_entry.practice_focus,
    }


def _restore_plan_fields(content: DailyLearningContent, plan_entry: StudyPlanEntry) -> None:
    content.date = plan_entry.date
    content.main_theme = plan_entry.main_theme
    content.plan_reference.date = plan_entry.date
    content.plan_reference.reading_assignment = plan_entry.reading_assignment
    content.plan_reference.practice_focus = plan_entry.practice_focus


def _absolute_page_url(settings: DailyRunnerSettings, page_url: str) -> str:
    if settings.page_base_url is None:
        return page_url
    return settings.page_base_url.rstrip("/") + page_url
