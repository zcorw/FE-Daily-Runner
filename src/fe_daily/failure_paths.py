from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from fe_daily.run_log import write_run_log


@dataclass(frozen=True)
class FailurePathResult:
    exit_code: int
    status: str
    log_path: Path


def record_failure_path(
    *,
    log_root: str | Path,
    target_date: date,
    run_mode: str,
    stage: str,
    error_summary: str,
    optional: bool = False,
) -> FailurePathResult:
    status = "success" if optional else "failed"
    exit_code = 0 if optional else 1
    log_path = write_run_log(
        log_root=log_root,
        target_date=target_date,
        started_at=datetime.now(timezone.utc),
        run_mode=run_mode,
        question_count=0,
        output_paths=[],
        plan_source="unknown",
        notification_status="failed" if stage == "telegram" else "not-run",
        status=status,
        errors=[f"{stage}: {error_summary}"],
    )
    return FailurePathResult(exit_code=exit_code, status=status, log_path=log_path)
