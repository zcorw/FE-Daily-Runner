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
            "title": "FE Daily 学習タスク",
            "main_theme": "SQL集計",
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "goals": ["科目Aの問題を練習する"],
            "time_table": [{"minutes": 20, "task": "読解"}, {"minutes": 40, "task": "演習"}],
            "terms": [
                {
                    "term": f"term-{index}",
                    "meaning": "意味を確認する",
                    "exam_note": f"試験での注意点 {index}",
                    "trap": f"混同しやすい点 {index}",
                }
                for index in range(10)
            ],
            "daily_explanation": [
                {"title": f"今日の要点 {index}", "body": "試験で問われる判断基準を整理します。"}
                for index in range(1, 5)
            ],
            "knowledge_points": [{"title": "GROUP BY句", "body": "集計前に行をグループ化する。"}],
            "questions": [
                {
                    "source_url": f"https://example.test/q{index}",
                    "question_text": f"問題 {index}",
                    "choices": {"A": "アルファ", "B": "ベータ", "C": "ガンマ", "D": "デルタ"},
                    "answer": "A",
                    "explanation": f"正答は条件に合うため適切です {index}",
                    "knowledge_point": "SQL",
                    "distractor_explanations": {
                        "B": f"Bは条件に合わないため誤りです {index}",
                        "C": f"Cは条件に合わないため誤りです {index}",
                        "D": f"Dは条件に合わないため誤りです {index}",
                    },
                    "images": [{"publicPath": f"/assets/fe-siken/q{index}.png"}],
                }
                for index in range(1, 11)
            ],
            "review_table_template": [{"question_no": index} for index in range(1, 11)],
            "tomorrow_suggestion": {"theme": "トランザクション"},
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
    assert soup.select_one('[data-section="daily-explanation"]')
    assert soup.select_one('[data-section="knowledge-points"]')
    assert soup.select_one('[data-section="questions"]')
    assert soup.select_one('[data-section="review"]')
    assert soup.select_one('[data-section="tomorrow"]')
    assert len(soup.select("[data-question]")) == 10


def test_render_daily_page_uses_refined_figma_layout_structure():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")

    assert soup.select_one(".daily-shell")
    assert soup.select_one(".hero")
    assert len(soup.select(".hero-stat")) == 3
    assert soup.select_one('[data-section="practice-mix"]')
    assert len(soup.select(".practice-mix__row")) == 1
    assert soup.select_one(".time-card-grid")
    assert len(soup.select(".time-card")) == 2
    assert soup.select_one(".terms-table")
    assert len(soup.select(".terms-table tbody tr")) == 10
    assert len(soup.select(".terms-table thead th")) == 4
    assert soup.select_one(".question-list")
    assert len(soup.select(".question-card")) == 10
    assert soup.select_one(".review-grid")
    assert soup.select_one(".term-pills")


def test_render_daily_page_includes_sticky_quick_navigation():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.select_one('nav.quick-nav[aria-label="ページ内ナビゲーション"]')

    assert nav is not None
    assert soup.select_one(".hero + .quick-nav")
    assert "position: sticky" in html
    expected_targets = [
        "#daily-goals",
        "#practice-mix",
        "#time-table",
        "#reading-assignment",
        "#study-checklist",
        "#terms",
        "#daily-explanation",
        "#questions",
        "#knowledge-points",
        "#review",
        "#tomorrow",
    ]
    assert [link["href"] for link in nav.select("a.quick-nav__link")] == expected_targets


def test_render_daily_page_has_mobile_compact_term_cards_without_removing_desktop_table():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")

    assert soup.select_one(".terms-table")
    assert len(soup.select(".terms-table tbody tr")) == 10
    cards = soup.select(".term-card")
    assert len(cards) == 10
    first_card = cards[0]
    assert first_card.select_one(".term-card__term").get_text(strip=True) == "term-0"
    assert first_card.select_one('[data-term-field="meaning"] .term-card__body').get_text(strip=True) == "意味を確認する"
    assert first_card.select_one('[data-term-field="exam-note"] .term-card__body').get_text(strip=True) == "試験での注意点 0"
    assert first_card.select_one('[data-term-field="trap"] .term-card__body').get_text(strip=True) == "混同しやすい点 0"
    assert "@media (max-width: 640px)" in html
    assert ".terms-table-wrap { display: none;" in html
    assert ".term-card-list { display: grid;" in html


def test_render_daily_page_uses_japanese_template_language():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")
    headings = [heading.get_text(" ", strip=True) for heading in soup.find_all(["h1", "h2", "h3"])]
    body_text = soup.get_text(" ", strip=True)

    assert headings[:10] == [
        "FE Daily 学習タスク",
        "今日の目標",
        "演習構成",
        "時間配分",
        "書籍の読解範囲",
        "学習チェックリスト",
        "重要用語",
        "今日知识点讲解",
        "科目A 練習問題",
        "問題 1",
    ]
    assert headings.index("重要用語") < headings.index("科目A 練習問題")
    assert headings.index("今日知识点讲解") < headings.index("科目A 練習問題")
    assert "知識メモ" in headings
    assert "正答" in body_text
    assert "他の選択肢が誤りである理由" in body_text
    assert "復習欄" in headings
    assert "明日の提案" in headings


def test_render_daily_page_does_not_emit_repeated_term_placeholders():
    content = daily_content()
    html = render_daily_page(content, template_dir=ROOT / "templates")

    assert "Connect this term to the planned practice topic." not in html
    assert "Do not confuse the term with a neighboring concept." not in html
    assert "試験での注意点 0" in html
    assert "混同しやすい点 0" in html


def test_render_daily_page_uses_question_specific_distractor_explanations():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")

    assert "This option does not match the required concept" not in html
    assert "Bは条件に合わないため誤りです 1" in html
    assert "Cは条件に合わないため誤りです 1" in html
    assert "Dは条件に合わないため誤りです 1" in html


def test_render_daily_page_places_question_images_in_answer_explanation_area():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")

    first_question = soup.select_one('[data-question="1"]')
    assert first_question is not None
    question_body = first_question.select_one('[data-question-field="question-body"]')
    explanation_area = first_question.select_one('[data-question-field="answer-explanation"]')

    assert question_body is not None
    assert explanation_area is not None
    assert question_body.select("img") == []
    assert explanation_area.select_one('img[src="/assets/fe-siken/q1.png"]')


def test_render_daily_page_supports_interactive_question_answers():
    html = render_daily_page(daily_content(), template_dir=ROOT / "templates")
    soup = BeautifulSoup(html, "html.parser")

    first_question = soup.select_one('[data-question="1"]')
    assert first_question is not None
    assert first_question["data-answer"] == "A"
    choice_buttons = first_question.select("button.choice-button[data-choice-option]")
    reveal_button = first_question.select_one("button.answer-toggle[data-answer-toggle]")
    answer_area = first_question.select_one('[data-question-field="answer-explanation"]')
    status = first_question.select_one("[data-choice-status]")

    assert [button["data-choice-label"] for button in choice_buttons] == ["A", "B", "C", "D"]
    assert [button.get_text(" ", strip=True) for button in choice_buttons] == [
        "A アルファ",
        "B ベータ",
        "C ガンマ",
        "D デルタ",
    ]
    assert all(button["aria-pressed"] == "false" for button in choice_buttons)
    assert reveal_button is not None
    assert reveal_button.get_text(strip=True) == "解答を表示"
    assert answer_area is not None
    assert "answer-panel" in answer_area["class"]
    assert status is not None
    assert status["aria-live"] == "polite"
    assert "js-enabled" in html
    assert "data-choice-option" in html
    assert "data-answer-toggle" in html


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
    assert "title: FE Daily 学習タスク" in markdown
