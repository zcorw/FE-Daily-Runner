import pytest

from fe_daily.content_validation import ContentValidationError, validate_question_facts
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
            "questions": [question],
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
