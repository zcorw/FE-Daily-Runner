from datetime import date

from fe_daily.output_schema import DailyLearningContent
from fe_daily.progress_context import upsert_progress_entry


def daily_content(theme: str = "SQL") -> DailyLearningContent:
    return DailyLearningContent.model_validate(
        {
            "date": "2026-06-13",
            "title": "Daily FE Study",
            "main_theme": theme,
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "questions": [
                {
                    "source_url": f"https://example.test/q{index}",
                    "question_text": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta"},
                    "answer": "A",
                    "explanation": f"Explanation {index}",
                }
                for index in range(1, 11)
            ],
            "progress_summary": {
                "gains": "Grouped SQL review",
                "weak_points": "HAVING vs WHERE",
            },
            "tomorrow_suggestion": {"theme": "Transactions"},
        }
    )


def test_upsert_progress_entry_appends_daily_summary(tmp_path):
    progress_path = tmp_path / "personal" / "progress.md"

    upsert_progress_entry(progress_path, daily_content(), page_url="/daily/2026-06-13/")

    text = progress_path.read_text(encoding="utf-8")
    assert "2026-06-13" in text
    assert "SQL" in text
    assert "Questions: 10" in text
    assert "Grouped SQL review" in text
    assert "HAVING vs WHERE" in text
    assert "/daily/2026-06-13/" in text


def test_upsert_progress_entry_updates_same_day_without_duplicate(tmp_path):
    progress_path = tmp_path / "personal" / "progress.md"

    upsert_progress_entry(progress_path, daily_content("SQL"), page_url="/daily/2026-06-13/")
    upsert_progress_entry(progress_path, daily_content("Transactions"), page_url="/daily/2026-06-13/")

    text = progress_path.read_text(encoding="utf-8")
    assert text.count("<!-- fe-daily:2026-06-13:start -->") == 1
    assert "Transactions" in text
    assert "SQL\n" not in text
