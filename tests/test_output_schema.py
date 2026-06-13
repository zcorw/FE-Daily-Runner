from datetime import date

import pytest
from pydantic import ValidationError

from fe_daily.output_schema import DailyLearningContent, PlanReference, QuestionLearningBlock


def valid_question():
    return {
        "source_url": "https://example.test/q1",
        "question_text": "Question text",
        "choices": {"ア": "A", "イ": "B", "ウ": "C", "エ": "D"},
        "answer": "ア",
        "explanation": "Explanation",
        "knowledge_point": "SQL",
    }


def valid_content_payload():
    return {
        "date": "2026-06-13",
        "title": "Daily FE Study",
        "main_theme": "データベース: 集計・結合",
        "plan_reference": {
            "date": "2026-06-13",
            "reading_assignment": "Ch.4.3 SQL集計/結合 p.129-133",
            "practice_focus": "SQL join/group 4, DB design 2, transaction 2, law 2",
        },
        "goals": ["Review SQL joins"],
        "time_table": [{"minutes": 20, "task": "Practice"}],
        "terms": [{"term": "GROUP BY", "meaning": "集計"}],
        "knowledge_points": [{"title": "SQL", "body": "Use grouping carefully."}],
        "questions": [valid_question()],
        "review_table_template": [{"question_no": 1}],
        "tomorrow_suggestion": {"theme": "Transaction"},
        "progress_summary": {"summary": "Studied SQL"},
    }


def test_daily_learning_content_accepts_valid_payload():
    content = DailyLearningContent.model_validate(valid_content_payload())

    assert content.date == date(2026, 6, 13)
    assert content.plan_reference.date == date(2026, 6, 13)
    assert content.questions[0].answer == "ア"


@pytest.mark.parametrize("field", ["date", "main_theme", "plan_reference", "questions"])
def test_daily_learning_content_rejects_missing_required_top_level_fields(field):
    payload = valid_content_payload()
    payload.pop(field)

    with pytest.raises(ValidationError):
        DailyLearningContent.model_validate(payload)


@pytest.mark.parametrize("field", ["source_url", "question_text", "choices", "answer", "explanation"])
def test_question_learning_block_rejects_missing_required_fields(field):
    payload = valid_question()
    payload.pop(field)

    with pytest.raises(ValidationError):
        QuestionLearningBlock.model_validate(payload)


def test_plan_reference_requires_daily_plan_fields():
    with pytest.raises(ValidationError):
        PlanReference.model_validate({"date": "2026-06-13"})
