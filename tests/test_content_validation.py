import pytest

from fe_daily.content_validation import (
    ContentValidationError,
    validate_learning_content_quality,
    validate_question_facts,
)
from fe_daily.output_schema import DailyLearningContent


def runtime_detail():
    return {
        "url": "https://example.test/q1",
        "questionText": "Question text",
        "choices": {"ア": "A", "イ": "B"},
        "answer": "ア",
        "explanation": "Explanation",
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }


def generated_content(**question_overrides):
    question = {
        "source_url": "https://example.test/q1",
        "question_text": "Question text",
        "choices": {"ア": "A", "イ": "B"},
        "answer": "ア",
        "explanation": "Explanation",
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }
    question.update(question_overrides)
    return DailyLearningContent.model_validate(
        {
            "date": "2026-06-13",
            "title": "Daily FE Study",
            "main_theme": "SQL",
            "plan_reference": {
                "date": "2026-06-13",
                "reading_assignment": "Ch.4.3 SQL p.129-133",
                "practice_focus": "SQL 10",
            },
            "time_table": [{"minutes": 10}, {"minutes": 20}, {"minutes": 20}, {"minutes": 10}],
            "terms": [{"term": f"term-{index}", "meaning": "meaning"} for index in range(10)],
            "questions": [question],
            "tomorrow_suggestion": {"theme": "Transaction"},
        }
    )


def test_validate_question_facts_accepts_matching_runtime_details():
    validate_question_facts(generated_content(), [runtime_detail()])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_url", "https://example.test/changed"),
        ("question_text", "Changed question"),
        ("choices", {"ア": "Changed"}),
        ("answer", "イ"),
        ("explanation", "Changed explanation"),
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
