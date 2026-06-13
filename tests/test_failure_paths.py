from datetime import date

import pytest

from fe_daily.failure_paths import record_failure_path


@pytest.mark.parametrize(
    "stage",
    [
        "health",
        "candidate_selection",
        "details",
        "openai_validation",
        "page_write",
    ],
)
def test_record_failure_path_writes_log_and_returns_nonzero(stage, tmp_path):
    result = record_failure_path(
        log_root=tmp_path / "logs" / "daily_publish",
        target_date=date(2026, 6, 13),
        run_mode="write",
        stage=stage,
        error_summary="simulated failure",
    )

    text = result.log_path.read_text(encoding="utf-8")
    assert result.exit_code == 1
    assert result.status == "failed"
    assert stage in text
    assert "simulated failure" in text


def test_record_failure_path_treats_telegram_failure_as_optional(tmp_path):
    result = record_failure_path(
        log_root=tmp_path / "logs" / "daily_publish",
        target_date=date(2026, 6, 13),
        run_mode="notify",
        stage="telegram",
        error_summary="telegram failed",
        optional=True,
    )

    text = result.log_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert result.status == "success"
    assert "telegram failed" in text
