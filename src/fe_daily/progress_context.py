from pathlib import Path

from fe_daily.output_schema import DailyLearningContent


def upsert_progress_entry(
    progress_path: str | Path,
    content: DailyLearningContent,
    *,
    page_url: str,
) -> None:
    path = Path(progress_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Progress\n"

    entry = _render_progress_block(content, page_url=page_url)
    start_marker = _start_marker(content.date.isoformat())
    end_marker = _end_marker(content.date.isoformat())

    start = existing.find(start_marker)
    end = existing.find(end_marker)
    if start != -1 and end != -1 and end > start:
        updated = existing[:start] + entry + existing[end + len(end_marker) :]
    else:
        separator = "\n\n" if existing.strip() else ""
        updated = existing.rstrip() + separator + entry

    path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def _render_progress_block(content: DailyLearningContent, *, page_url: str) -> str:
    target_date = content.date.isoformat()
    gains = content.progress_summary.get("gains") or content.progress_summary.get("summary") or ""
    weak_points = content.progress_summary.get("weak_points") or ""
    tomorrow = content.tomorrow_suggestion.get("theme", "")

    return "\n".join(
        [
            _start_marker(target_date),
            f"## {target_date}",
            "",
            f"- Theme: {content.main_theme}",
            f"- Questions: {len(content.questions)}",
            f"- Gains: {gains}",
            f"- Weak points: {weak_points}",
            f"- Tomorrow: {tomorrow}",
            f"- Page: {page_url}",
            _end_marker(target_date),
        ]
    )


def _start_marker(target_date: str) -> str:
    return f"<!-- fe-daily:{target_date}:start -->"


def _end_marker(target_date: str) -> str:
    return f"<!-- fe-daily:{target_date}:end -->"
