from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from fe_daily.output_schema import DailyLearningContent
from fe_daily.page_renderer import (
    TemplateLoadError,
    load_template_environment,
    render_daily_page,
)


ROOT = Path(__file__).resolve().parents[1]


def test_required_templates_exist():
    for template_name in [
        "base.html.j2",
        "daily_page.html.j2",
        "index_page.html.j2",
        "progress_entry.md.j2",
        "telegram_message.html.j2",
    ]:
        assert (ROOT / "templates" / template_name).is_file()


def test_load_template_environment_loads_required_template():
    environment = load_template_environment(ROOT / "templates")

    assert environment.get_template("daily_page.html.j2").name == "daily_page.html.j2"


def test_load_template_environment_reports_missing_template_directory(tmp_path):
    with pytest.raises(TemplateLoadError):
        load_template_environment(tmp_path / "missing")


def daily_content() -> DailyLearningContent:
    return DailyLearningContent.model_validate(
        {
            "date": "2026-06-13",
            "title": "Daily FE Study",
            "main_theme": "SQL aggregation",
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "goals": ["Practice subject A questions"],
            "time_table": [{"minutes": 20, "task": "Read"}, {"minutes": 40, "task": "Practice"}],
            "terms": [{"term": f"term-{index}", "meaning": "meaning"} for index in range(10)],
            "knowledge_points": [{"title": "GROUP BY", "body": "Group rows before filtering."}],
            "questions": [
                {
                    "source_url": f"https://example.test/q{index}",
                    "question_text": f"Question {index}",
                    "choices": {"A": "alpha", "B": "beta", "C": "gamma", "D": "delta"},
                    "answer": "A",
                    "explanation": f"Explanation {index}",
                    "knowledge_point": "SQL",
                    "images": [{"publicPath": f"/assets/fe-siken/q{index}.png"}],
                }
                for index in range(1, 11)
            ],
            "review_table_template": [{"question_no": index} for index in range(1, 11)],
            "tomorrow_suggestion": {"theme": "Transactions"},
        }
    )


def test_render_daily_page_outputs_required_sections_and_exactly_10_questions():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")

    assert soup.select_one('[data-section="daily-goals"]')
    assert soup.select_one('[data-section="time-table"]')
    assert soup.select_one('[data-section="reading-assignment"]')
    assert soup.select_one('[data-section="study-checklist"]')
    assert soup.select_one('[data-section="terms"]')
    assert soup.select_one('[data-section="knowledge-points"]')
    assert soup.select_one('[data-section="questions"]')
    assert soup.select_one('[data-section="review"]')
    assert soup.select_one('[data-section="tomorrow"]')
    assert len(soup.select("[data-question]")) == 10
