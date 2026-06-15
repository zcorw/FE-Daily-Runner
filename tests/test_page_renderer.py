from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from fe_daily.output_schema import DailyLearningContent
from fe_daily.page_renderer import (
    TemplateLoadError,
    load_template_environment,
    render_daily_page,
    render_index_page,
    render_progress_entry_markdown,
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
            "terms": [
                {
                    "term": f"term-{index}",
                    "meaning": "meaning",
                    "exam_note": f"exam note {index}",
                    "trap": f"trap {index}",
                }
                for index in range(10)
            ],
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


def test_render_daily_page_matches_reference_markdown_section_language():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")
    headings = [heading.get_text(" ", strip=True) for heading in soup.find_all(["h1", "h2", "h3"])]
    body_text = soup.get_text(" ", strip=True)

    assert headings[:9] == [
        "Daily FE Study",
        "Today's Goal",
        "Time Box",
        "Book Reading Range",
        "Study Checklist",
        "Key Terms",
        "Knowledge Notes",
        "Subject-A Practice Questions",
        "Question 1",
    ]
    assert "Correct answer" in body_text
    assert "Why the other choices are wrong" in body_text
    assert "Review Area" in headings
    assert "Tomorrow's Suggestion" in headings


def test_render_daily_page_does_not_emit_repeated_term_placeholders():
    content = daily_content()
    html = render_daily_page(content, template_dir=ROOT / "templates")

    assert "Connect this term to the planned practice topic." not in html
    assert "Do not confuse the term with a neighboring concept." not in html
    assert "exam note 0" in html
    assert "trap 0" in html


def test_render_index_page_links_current_day_once_when_entries_repeat():
    html = render_index_page(
        [
            {"date": "2026-06-13", "title": "SQL aggregation", "url": "/daily/2026-06-13/"},
            {"date": "2026-06-13", "title": "SQL aggregation", "url": "/daily/2026-06-13/"},
            {"date": "2026-06-12", "title": "Networks", "url": "/daily/2026-06-12/"},
        ],
        current_strategy="SQL 10-question focus",
        updated_at="2026-06-13T06:00:00+09:00",
        template_dir=ROOT / "templates",
    )
    soup = BeautifulSoup(html, "html.parser")

    assert len(soup.select('a[href="/daily/2026-06-13/"]')) == 1
    assert soup.select_one('[data-section="recent-daily-pages"]')
    assert soup.select_one('[data-section="latest-updated"]').get_text(strip=True)
    assert soup.select_one('[data-section="current-strategy"]').get_text(strip=True)


def test_render_progress_entry_markdown_includes_front_matter():
    markdown = render_progress_entry_markdown(
        daily_content(),
        page_url="/daily/2026-06-13/",
        template_dir=ROOT / "templates",
    )

    assert markdown.startswith("---\n")
    assert "date: 2026-06-13" in markdown
    assert "permalink: /daily/2026-06-13/" in markdown
    assert "title: Daily FE Study" in markdown
