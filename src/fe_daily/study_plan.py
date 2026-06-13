from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class StudyPlanEntry:
    date: date
    main_theme: str
    reading_assignment: str
    practice_focus: str
    plan_source: str = "june-study-plan"


def load_study_plan_entry(plan_path: str | Path, target_date: date) -> StudyPlanEntry | None:
    rows = _parse_markdown_table(Path(plan_path).read_text(encoding="utf-8"))
    for row in rows:
        if row.get("Date") != target_date.isoformat():
            continue
        return StudyPlanEntry(
            date=target_date,
            main_theme=row["Main Theme"],
            reading_assignment=row["20-Minute Reading Assignment"],
            practice_focus=row["Practice Focus"],
        )
    return None


def select_study_plan_entry(
    plan_path: str | Path,
    target_date: date,
    *,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
) -> StudyPlanEntry:
    planned_entry = load_study_plan_entry(plan_path, target_date)
    if planned_entry is not None:
        return planned_entry

    return build_fallback_plan_entry(
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )


def build_fallback_plan_entry(
    target_date: date,
    *,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
) -> StudyPlanEntry:
    topic = _first_context_item(weak_points) or _first_context_item(mistake_log) or _first_context_item(recent_progress)
    if topic is None:
        topic = "Mixed FE review"

    return StudyPlanEntry(
        date=target_date,
        main_theme=topic,
        reading_assignment="No scheduled June plan. Review weak points, mistake log, and recent progress.",
        practice_focus=f"{topic} 10",
        plan_source="fallback",
    )


def _parse_markdown_table(markdown: str) -> list[dict[str, str]]:
    headers: list[str] | None = None
    rows: list[dict[str, str]] = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if _is_separator_row(cells):
            continue

        if headers is None:
            if set(cells) >= {"Date", "Main Theme", "20-Minute Reading Assignment", "Practice Focus"}:
                headers = cells
            continue

        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells, strict=True)))

    return rows


def _is_separator_row(cells: list[str]) -> bool:
    return all(cell.replace(":", "").replace("-", "").strip() == "" for cell in cells)


def _first_context_item(text: str) -> str | None:
    for line in text.splitlines():
        item = line.strip().lstrip("-*").strip()
        if item:
            return item
    return None
