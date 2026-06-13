from datetime import date, datetime, timezone

from fe_daily.run_log import write_run_log


def test_write_run_log_records_success_metadata(tmp_path):
    path = write_run_log(
        log_root=tmp_path / "logs" / "daily_publish",
        target_date=date(2026, 6, 13),
        started_at=datetime(2026, 6, 13, 6, 0, tzinfo=timezone.utc),
        run_mode="dry-run",
        question_count=10,
        output_paths=["site/tmp/dry-run/2026-06-13/preview.html"],
        plan_source="june-study-plan",
        notification_status="skipped",
        status="success",
        errors=[],
    )

    text = path.read_text(encoding="utf-8")
    assert path == tmp_path / "logs" / "daily_publish" / "2026-06-13.md"
    assert "run_mode: dry-run" in text
    assert "question_count: 10" in text
    assert "plan_source: june-study-plan" in text
    assert "notification_status: skipped" in text
    assert "site/tmp/dry-run/2026-06-13/preview.html" in text


def test_write_run_log_records_failure_errors(tmp_path):
    path = write_run_log(
        log_root=tmp_path / "logs" / "daily_publish",
        target_date=date(2026, 6, 13),
        started_at=datetime(2026, 6, 13, 6, 0, tzinfo=timezone.utc),
        run_mode="write",
        question_count=0,
        output_paths=[],
        plan_source="fallback",
        notification_status="not-run",
        status="failed",
        errors=["question bank unavailable"],
    )

    text = path.read_text(encoding="utf-8")
    assert "status: failed" in text
    assert "question bank unavailable" in text
