from datetime import date, datetime
from pathlib import Path


def write_run_log(
    *,
    log_root: str | Path,
    target_date: date,
    started_at: datetime,
    run_mode: str,
    question_count: int,
    output_paths: list[str],
    plan_source: str,
    notification_status: str,
    status: str,
    errors: list[str],
) -> Path:
    root = Path(log_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{target_date:%Y-%m-%d}.md"

    lines = [
        "---",
        f"date: {target_date:%Y-%m-%d}",
        f"started_at: {started_at.isoformat()}",
        f"run_mode: {run_mode}",
        f"question_count: {question_count}",
        f"plan_source: {plan_source}",
        f"notification_status: {notification_status}",
        f"status: {status}",
        "---",
        "",
        "## Output Paths",
    ]
    lines.extend(f"- {output_path}" for output_path in output_paths)
    if not output_paths:
        lines.append("- none")

    lines.extend(["", "## Errors"])
    lines.extend(f"- {error}" for error in errors)
    if not errors:
        lines.append("- none")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
