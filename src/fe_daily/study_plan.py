from dataclasses import dataclass
import calendar
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
    path = Path(plan_path)
    if not path.exists():
        return None
    rows = _parse_markdown_table(path.read_text(encoding="utf-8"))
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
    ensure_monthly_plan(
        plan_path,
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )
    planned_entry = load_study_plan_entry(plan_path, target_date)
    if planned_entry is not None:
        return planned_entry

    return build_fallback_plan_entry(
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )


def ensure_monthly_plan(
    plan_path: str | Path,
    target_date: date,
    *,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
) -> bool:
    path = Path(plan_path)
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""
    rows = _parse_markdown_table(existing_text)
    if _has_plan_for_month(rows, target_date):
        return False

    generated = generate_monthly_plan_markdown(
        target_date,
        weak_points=weak_points,
        mistake_log=mistake_log,
        recent_progress=recent_progress,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    separator = "\n\n" if existing_text.strip() else ""
    path.write_text(f"{existing_text.rstrip()}{separator}{generated}\n", encoding="utf-8")
    return True


def generate_monthly_plan_markdown(
    target_date: date,
    *,
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
) -> str:
    _, last_day = calendar.monthrange(target_date.year, target_date.month)
    rows = [
        f"## Auto-generated Study Plan - {target_date:%Y-%m}",
        "",
        "Generated because no study-plan rows existed for this month.",
        "",
        "| Date | Main Theme | 20-Minute Reading Assignment | Practice Focus |",
        "|---|---|---|---|",
    ]
    topics = _monthly_topic_rotation(weak_points, mistake_log, recent_progress)
    for day in range(1, last_day + 1):
        current = date(target_date.year, target_date.month, day)
        theme, reading, focus = topics[(day - 1) % len(topics)]
        rows.append(f"| {current.isoformat()} | {theme} | {reading} | {focus} |")
    return "\n".join(rows)


def _has_plan_for_month(rows: list[dict[str, str]], target_date: date) -> bool:
    month_prefix = f"{target_date:%Y-%m}-"
    return any(row.get("Date", "").startswith(month_prefix) for row in rows)


def _monthly_topic_rotation(
    weak_points: str,
    mistake_log: str,
    recent_progress: str,
) -> list[tuple[str, str, str]]:
    context_topic = _first_context_item(weak_points) or _first_context_item(mistake_log) or _first_context_item(
        recent_progress
    )
    topics = [
        ("情報セキュリティ復習", "Review security concepts and recent marked mistakes.", "security 10"),
        ("データベース / SQL", "Review database operations, joins, and aggregation.", "SQL 6, transaction 2, law 2"),
        ("ネットワーク基礎", "Review network protocols and communication concepts.", "network 6, security 4"),
        ("システム評価指標", "Review availability, MTBF/MTTR, and performance calculations.", "availability 10"),
        ("会計・財務計算", "Review break-even, ROI, sales, and profit calculations.", "Break-even 3, ROI 3, sales/profit 2, law 2"),
        ("マネジメント / 監査", "Review project management, service management, and audit concepts.", "Project 3, service management 3, audit 2, security 2"),
        ("アルゴリズム / データ構造", "Review algorithms, data structures, and logic questions.", "Sort/search 3, Tree/list/stack 3, bit/logic 2, security 2"),
    ]
    if context_topic is not None:
        topics.insert(
            0,
            (
                f"弱点補強: {context_topic}",
                "Review weak points, mistake log, and recent progress before solving questions.",
                "security 4, SQL 2, availability 2, network 2",
            ),
        )
    return topics


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
