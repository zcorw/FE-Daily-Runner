from fe_daily.config import RunMode
from fe_daily.run_modes import OutputKind, plan_for_run_mode


def test_dry_run_only_allows_temporary_preview_outputs():
    plan = plan_for_run_mode(RunMode.DRY_RUN)

    assert plan.mode is RunMode.DRY_RUN
    assert plan.allowed_outputs == frozenset(
        {
            OutputKind.TEMP_JSON,
            OutputKind.TEMP_PAGE_PREVIEW,
            OutputKind.RUN_LOG,
        }
    )
    assert plan.writes_formal_outputs is False
    assert plan.sends_telegram is False
    assert plan.requires_successful_write_before_notify is False


def test_write_allows_formal_outputs_without_telegram():
    plan = plan_for_run_mode(RunMode.WRITE)

    assert OutputKind.DAILY_PAGE in plan.allowed_outputs
    assert OutputKind.INDEX_PAGE in plan.allowed_outputs
    assert OutputKind.PROGRESS in plan.allowed_outputs
    assert OutputKind.STATE in plan.allowed_outputs
    assert OutputKind.RUN_LOG in plan.allowed_outputs
    assert OutputKind.TELEGRAM_MESSAGE not in plan.allowed_outputs
    assert plan.writes_formal_outputs is True
    assert plan.sends_telegram is False
    assert plan.requires_successful_write_before_notify is False


def test_notify_runs_write_outputs_then_telegram_after_success():
    plan = plan_for_run_mode(RunMode.NOTIFY)

    assert OutputKind.DAILY_PAGE in plan.allowed_outputs
    assert OutputKind.INDEX_PAGE in plan.allowed_outputs
    assert OutputKind.PROGRESS in plan.allowed_outputs
    assert OutputKind.STATE in plan.allowed_outputs
    assert OutputKind.RUN_LOG in plan.allowed_outputs
    assert OutputKind.TELEGRAM_MESSAGE in plan.allowed_outputs
    assert plan.writes_formal_outputs is True
    assert plan.sends_telegram is True
    assert plan.requires_successful_write_before_notify is True
