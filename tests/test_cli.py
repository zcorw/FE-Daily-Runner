from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from fe_daily.cli import build_parser, main, parse_args, resolve_target_date
from fe_daily.config import RunMode
from fe_daily.workflow import WorkflowResult


def test_parse_date_and_dry_run_mode():
    args = parse_args(["--date", "2026-06-13", "--dry-run"])

    assert args.target_date == date(2026, 6, 13)
    assert args.today is False
    assert args.run_mode is RunMode.DRY_RUN


def test_parse_today_and_write_mode():
    args = parse_args(["--today", "--write"])

    assert args.target_date is None
    assert args.today is True
    assert args.run_mode is RunMode.WRITE


def test_resolve_target_date_uses_tokyo_date_for_today_at_utc_boundary():
    args = parse_args(["--today", "--dry-run"])

    assert resolve_target_date(
        args,
        timezone_name="Asia/Tokyo",
        now=datetime(2026, 6, 13, 15, 30, tzinfo=timezone.utc),
    ) == date(2026, 6, 14)


def test_resolve_target_date_uses_explicit_date_without_timezone_conversion():
    args = parse_args(["--date", "2026-06-13", "--dry-run"])

    assert resolve_target_date(args, timezone_name="Asia/Tokyo") == date(2026, 6, 13)


def test_date_and_today_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["--date", "2026-06-13", "--today", "--dry-run"])


def test_run_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["--date", "2026-06-13", "--dry-run", "--write"])


def test_render_only_requires_input():
    with pytest.raises(SystemExit):
        parse_args(["--render-only"])


def test_input_requires_render_only():
    with pytest.raises(SystemExit):
        parse_args(["--input", "tmp/daily.json"])


def test_maintenance_operations_conflict_with_run_modes():
    with pytest.raises(SystemExit):
        parse_args(["--health-check", "--dry-run"])

    with pytest.raises(SystemExit):
        parse_args(["--validate-config", "--notify"])


def test_validate_config_reports_openai_dry_run_limitation(capsys):
    exit_code = main(["--validate-config"], settings_overrides={"_env_file": None})

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000" in captured.out
    assert "OPENAI_API_KEY missing" in captured.out


def test_parser_exposes_expected_options():
    help_text = build_parser().format_help()

    for option in [
        "--date",
        "--today",
        "--dry-run",
        "--write",
        "--notify",
        "--health-check",
        "--validate-config",
        "--render-only",
        "--input",
    ]:
        assert option in help_text


def test_main_dry_run_calls_workflow_with_configured_input_documents(tmp_path):
    paths = write_input_documents(tmp_path)
    calls = []

    def workflow_runner(**kwargs):
        calls.append(kwargs)
        return WorkflowResult(
            status="success",
            target_date=kwargs["target_date"],
            plan_source="test-plan",
        )

    exit_code = main(
        ["--date", "2026-06-13", "--dry-run"],
        settings_overrides={
            "_env_file": None,
            "output_dir": tmp_path / "site",
            "template_dir": tmp_path / "templates",
            **paths,
        },
        question_bank_client_factory=lambda _settings: object(),
        generator_factory=lambda _settings: object(),
        workflow_runner=workflow_runner,
    )

    assert exit_code == 0
    assert len(calls) == 1
    call = calls[0]
    assert call["target_date"] == date(2026, 6, 13)
    assert call["run_mode"] is RunMode.DRY_RUN
    assert call["plan_path"] == paths["study_plan_path"]
    assert call["weak_points"] == "weak points"
    assert call["mistake_log"] == "mistake log"
    assert call["recent_progress"] == "recent progress"


def test_main_write_passes_write_mode_to_workflow(tmp_path):
    paths = write_input_documents(tmp_path)
    calls = []

    def workflow_runner(**kwargs):
        calls.append(kwargs)
        return WorkflowResult(
            status="success",
            target_date=kwargs["target_date"],
            plan_source="test-plan",
        )

    exit_code = main(
        ["--date", "2026-06-13", "--write"],
        settings_overrides={
            "_env_file": None,
            "output_dir": tmp_path / "site",
            "template_dir": tmp_path / "templates",
            **paths,
        },
        question_bank_client_factory=lambda _settings: object(),
        generator_factory=lambda _settings: object(),
        workflow_runner=workflow_runner,
    )

    assert exit_code == 0
    assert calls[0]["run_mode"] is RunMode.WRITE


def write_input_documents(tmp_path: Path) -> dict[str, Path]:
    study_plan_path = tmp_path / "study.md"
    weak_points_path = tmp_path / "weak.md"
    mistake_log_path = tmp_path / "mistakes.md"
    progress_context_path = tmp_path / "progress.md"
    study_plan_path.write_text("study plan", encoding="utf-8")
    weak_points_path.write_text("weak points", encoding="utf-8")
    mistake_log_path.write_text("mistake log", encoding="utf-8")
    progress_context_path.write_text("recent progress", encoding="utf-8")
    return {
        "study_plan_path": study_plan_path,
        "weak_points_path": weak_points_path,
        "mistake_log_path": mistake_log_path,
        "progress_context_path": progress_context_path,
    }
