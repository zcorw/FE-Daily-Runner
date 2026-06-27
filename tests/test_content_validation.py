import pytest
from bs4 import BeautifulSoup

from fe_daily.content_validation import (
    ContentValidationError,
    validate_daily_html,
    validate_learning_content_quality,
    validate_question_facts,
)
from fe_daily.output_schema import DailyLearningContent
from fe_daily.page_renderer import render_daily_page


def runtime_detail():
    return {
        "url": "https://example.test/q1",
        "questionText": "Question text",
        "choices": {"ア": "A", "イ": "B"},
        "answer": "ア",
        "explanation": "これは日本語の解説です。",
        "distractor_explanations": {"イ": "この選択肢は題意に合わないため誤りです。"},
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }


def generated_content(**question_overrides):
    question = {
        "source_url": "https://example.test/q1",
        "question_text": "Question text",
        "choices": {"ア": "A", "イ": "B"},
        "answer": "ア",
        "explanation": "これは日本語の解説です。",
        "distractor_explanations": {"イ": "この選択肢は題意に合わないため誤りです。"},
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }
    question.update(question_overrides)
    return DailyLearningContent.model_validate(
        {
            "date": "2026-06-13",
            "title": "FE Daily 学習タスク",
            "main_theme": "SQL",
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "goals": ["科目Aの問題を確認する。"],
            "time_table": [
                {"minutes": 10, "task": "読解する"},
                {"minutes": 20, "task": "重要語を整理する"},
                {"minutes": 20, "task": "問題を解く"},
                {"minutes": 10, "task": "誤答を復習する"},
            ],
            "terms": [
                {
                    "term": f"term-{index}",
                    "meaning": "意味を確認する。",
                    "exam_note": f"試験での注意点 {index}",
                    "trap": f"混同しやすい点 {index}",
                }
                for index in range(10)
            ],
            "daily_explanation": [
                {"title": f"今日の要点 {index}", "body": "試験で問われる判断基準を整理します。"}
                for index in range(1, 5)
            ],
            "questions": [question],
            "knowledge_points": [{"title": "SQLの要点", "body": "集計条件を確認する。"}],
            "tomorrow_suggestion": {"theme": "トランザクション"},
        }
    )


def generated_page_content() -> DailyLearningContent:
    base_question = {
        "source_url": "https://example.test/q1",
        "question_text": "Question text",
        "choices": {"A": "Alpha", "B": "Beta"},
        "answer": "A",
        "explanation": "これは日本語の解説です。",
        "distractor_explanations": {"B": "この選択肢は題意に合わないため誤りです。"},
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }
    return DailyLearningContent.model_validate(
        {
            "date": "2026-06-13",
            "title": "FE Daily 学習タスク",
            "main_theme": "SQL",
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "goals": ["科目Aの問題を確認する。"],
            "time_table": [{"minutes": 60, "task": "問題を解いて復習する"}],
            "terms": [
                {
                    "term": f"term-{index}",
                    "meaning": "意味を確認する。",
                    "exam_note": f"試験での注意点 {index}",
                    "trap": f"混同しやすい点 {index}",
                }
                for index in range(10)
            ],
            "daily_explanation": [
                {"title": f"今日の要点 {index}", "body": "試験で問われる判断基準を整理します。"}
                for index in range(1, 5)
            ],
            "knowledge_points": [{"title": "SQLの要点", "body": "集計条件を確認する。"}],
            "questions": [
                {
                    **base_question,
                    "source_url": f"https://example.test/q{index}",
                    "question_text": f"Question {index}",
                    "explanation": f"これは日本語の解説です {index}",
                    "images": [{"publicPath": f"/assets/fe-siken/r7/q{index}.png"}],
                }
                for index in range(1, 11)
            ],
            "review_table_template": [{"question_no": index} for index in range(1, 11)],
            "tomorrow_suggestion": {"theme": "トランザクション"},
        }
    )


def rendered_daily_html(content: DailyLearningContent | None = None) -> str:
    return render_daily_page(content or generated_page_content(), page_url="/daily/2026-06-13/")


def test_validate_question_facts_accepts_matching_runtime_details():
    validate_question_facts(generated_content(), [runtime_detail()])


def test_validate_question_facts_accepts_generated_teaching_explanation():
    validate_question_facts(
        generated_content(explanation="これは日本語の詳しい解説です。"),
        [runtime_detail()],
    )


def test_validate_question_facts_rejects_non_japanese_generated_explanation():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_question_facts(generated_content(explanation="Generated teaching explanation"), [runtime_detail()])

    assert "explanation" in str(exc_info.value)


def test_validate_question_facts_accepts_runtime_image_metadata():
    detail = runtime_detail()
    detail["images"] = [
        {
            "publicPath": "/assets/fe-siken/r7/q1.png",
            "section": "question",
            "url": "https://example.test/q1.png",
            "width": "406",
            "height": "216",
        }
    ]

    validate_question_facts(generated_content(), [detail])


def test_validate_question_facts_accepts_runtime_images_split_between_question_and_explanation():
    validate_question_facts(
        generated_content(
            images=[],
            explanation_images=[{"publicPath": "/assets/fe-siken/r7/q1.png"}],
        ),
        [runtime_detail()],
    )


def test_validate_question_facts_rejects_blank_generated_explanation():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_question_facts(generated_content(explanation="   "), [runtime_detail()])

    assert "explanation" in str(exc_info.value)


def test_validate_question_facts_rejects_missing_distractor_explanation():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_question_facts(generated_content(distractor_explanations={}), [runtime_detail()])

    assert "distractor_explanations" in str(exc_info.value)


def test_validate_question_facts_rejects_repeated_distractor_explanations():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_question_facts(
            generated_content(
                choices={"A": "A", "B": "B", "C": "C"},
                answer="A",
                distractor_explanations={"B": "同じ誤答理由です。", "C": "同じ誤答理由です。"},
            ),
            [
                {
                    **runtime_detail(),
                    "choices": {"A": "A", "B": "B", "C": "C"},
                    "answer": "A",
                }
            ],
        )

    assert "distractor_explanations" in str(exc_info.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_url", "https://example.test/changed"),
        ("question_text", "Changed question"),
        ("choices", {"ア": "Changed"}),
        ("answer", "イ"),
        ("images", [{"publicPath": "/assets/fe-siken/changed.png"}]),
    ],
)
def test_validate_question_facts_rejects_model_changed_facts(field, value):
    with pytest.raises(ContentValidationError) as exc_info:
        validate_question_facts(generated_content(**{field: value}), [runtime_detail()])

    assert field in str(exc_info.value)


def expected_plan():
    return {
        "date": "2026-06-13",
        "main_theme": "SQL",
        "reading_assignment": "Ch.4.3 SQL p.129-133",
        "practice_focus": "SQL 10",
    }


def test_validate_learning_content_quality_accepts_matching_plan_content():
    validate_learning_content_quality(generated_content(), expected_plan())


def test_validate_learning_content_quality_requires_at_least_10_terms():
    content = generated_content()
    content.terms = content.terms[:9]

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "terms" in str(exc_info.value)


def test_validate_learning_content_quality_rejects_missing_term_exam_note_or_trap():
    content = generated_content()
    content.terms[0].pop("exam_note")

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "exam_note" in str(exc_info.value)


def test_validate_learning_content_quality_rejects_repeated_term_exam_notes_or_traps():
    content = generated_content()
    for term in content.terms:
        term["exam_note"] = "same note"

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "exam_note" in str(exc_info.value)


def test_validate_learning_content_quality_rejects_non_japanese_generated_learning_text():
    content = generated_content()
    content.terms[0]["meaning"] = "English meaning"

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "Japanese" in str(exc_info.value)


def test_validate_learning_content_quality_requires_approximately_60_minutes():
    content = generated_content()
    content.time_table = [{"minutes": 20}]

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "time_table" in str(exc_info.value)


def test_validate_learning_content_quality_rejects_plan_mismatch():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(
            generated_content(),
            {**expected_plan(), "main_theme": "Network"},
        )

    assert "main_theme" in str(exc_info.value)


def test_validate_learning_content_quality_requires_tomorrow_suggestion():
    content = generated_content()
    content.tomorrow_suggestion = {}

    with pytest.raises(ContentValidationError) as exc_info:
        validate_learning_content_quality(content, expected_plan())

    assert "tomorrow_suggestion" in str(exc_info.value)


def test_validate_daily_html_accepts_matching_page():
    content = generated_page_content()

    validate_daily_html(rendered_daily_html(content), content, page_url="/daily/2026-06-13/")


@pytest.mark.parametrize(
    ("field", "broken_html"),
    [
        ("date", lambda html: html.replace('data-date="2026-06-13"', 'data-date="2026-06-14"')),
        ("page_url", lambda html: html.replace('/daily/2026-06-13/', '/daily/2026-06-14/')),
        ("main_theme", lambda html: html.replace('data-main-theme="SQL"', 'data-main-theme="Network"')),
        (
            "reading_assignment",
            lambda html: html.replace("Ch.4.3 SQL p.129-133", "Ch.5 Network p.1-10"),
        ),
        ("source_url", lambda html: html.replace("https://example.test/q1", "https://example.test/changed")),
        ("answer", lambda html: html.replace("<strong>正答</strong>: A", "<strong>正答</strong>: B", 1)),
        ("explanation", lambda html: html.replace("これは日本語の解説です 1", "Changed explanation")),
        (
            "image",
            lambda html: html.replace("/assets/fe-siken/r7/q1.png", "question-bank-runtime/r7/q1.png"),
        ),
        ("secret", lambda html: html + " OPENAI_API_KEY=abc123"),
    ],
)
def test_validate_daily_html_rejects_invalid_page_rules(field, broken_html):
    content = generated_page_content()

    with pytest.raises(ContentValidationError) as exc_info:
        validate_daily_html(broken_html(rendered_daily_html(content)), content, page_url="/daily/2026-06-13/")

    assert field in str(exc_info.value)


def test_validate_daily_html_requires_exactly_10_questions():
    content = generated_page_content()
    soup = BeautifulSoup(rendered_daily_html(content), "html.parser")
    soup.select_one("[data-question]").decompose()

    with pytest.raises(ContentValidationError) as exc_info:
        validate_daily_html(str(soup), content, page_url="/daily/2026-06-13/")

    assert "question count" in str(exc_info.value)


@pytest.mark.parametrize(
    "bad_path",
    [
        "question-bank-runtime/assets/r7/q1.png",
        "C:/Users/example/docs/assets/fe-siken/r7/q1.png",
        "docs/assets/fe-siken/r7/q1.png",
    ],
)
def test_validate_daily_html_rejects_non_public_image_paths(bad_path):
    content = generated_page_content()
    html = rendered_daily_html(content).replace("/assets/fe-siken/r7/q1.png", bad_path)

    with pytest.raises(ContentValidationError) as exc_info:
        validate_daily_html(html, content, page_url="/daily/2026-06-13/")

    assert "image" in str(exc_info.value)


def test_validate_daily_html_accepts_explicitly_allowed_public_image_prefix():
    content = generated_page_content()
    html = rendered_daily_html(content).replace("/assets/fe-siken/r7/q1.png", "/static/fe-siken/r7/q1.png")

    validate_daily_html(
        html,
        content,
        page_url="/daily/2026-06-13/",
        allowed_image_prefixes=("/assets/fe-siken/", "/static/fe-siken/"),
    )
