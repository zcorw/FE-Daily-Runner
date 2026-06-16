import pytest

from fe_daily.prompt_builder import PromptBoundaryError, build_generation_payload


def question_detail(url="https://example.test/q1"):
    return {
        "url": url,
        "questionText": "Question text",
        "choices": {"ア": "A", "イ": "B", "ウ": "C", "エ": "D"},
        "answer": "ア",
        "explanation": "Explanation",
        "images": [{"publicPath": "/assets/fe-siken/r7/q1.png"}],
    }


def test_build_generation_payload_contains_plan_context_without_question_facts():
    payload = build_generation_payload(
        plan={
            "date": "2026-06-13",
            "main_theme": "データベース: 集計・結合",
            "reading_assignment": "Ch.4.3 SQL集計/結合 p.129-133",
            "practice_focus": "SQL join/group 4, DB design 2, transaction 2, law 2",
        },
        weak_points="- SQL\n- transaction",
        progress_summary="Recent DB review",
        mistake_log="No daily misses yet",
        questions=[question_detail()],
    )

    assert payload["plan"]["main_theme"] == "データベース: 集計・結合"
    assert payload["personal_context"]["weak_points"] == "- SQL\n- transaction"
    assert "questions" not in payload
    assert payload["generation_rules"]["openai_must_not_generate_question_content"] is True
    assert payload["generation_rules"]["output_must_copy_plan_fields_exactly"] == [
        "date",
        "main_theme",
        "reading_assignment",
        "practice_focus",
    ]
    assert payload["generation_rules"]["page_structure_language"] == "Japanese"
    assert payload["generation_rules"]["generated_learning_content_language"] == "Japanese"
    assert payload["generation_rules"]["japanese_content_fields"] == [
        "goals",
        "time_table.task",
        "terms.meaning",
        "terms.exam_note",
        "terms.trap",
        "knowledge_points.title",
        "knowledge_points.body",
        "tomorrow_suggestion.theme",
    ]
    assert payload["generation_rules"]["page_format_reference"] == "FE Daily Study Task markdown"
    assert payload["generation_rules"]["minimum_key_terms"] == 10
    assert payload["generation_rules"]["key_terms_table_fields"] == [
        "term",
        "meaning",
        "exam_note",
        "trap",
    ]
    assert payload["generation_rules"]["key_terms_must_have_unique_exam_notes_and_traps"] is True


@pytest.mark.parametrize(
    "secret_text",
    [
        "OPENAI_API_KEY=sk-test",
        "TELEGRAM_BOT_TOKEN=secret",
        "ADMIN_API_TOKEN=secret",
        ".env contents",
    ],
)
def test_build_generation_payload_rejects_secret_markers(secret_text):
    with pytest.raises(PromptBoundaryError):
        build_generation_payload(
            plan={"date": "2026-06-13", "main_theme": "SQL"},
            weak_points=secret_text,
            progress_summary="progress",
            mistake_log="mistakes",
            questions=[question_detail()],
        )


def test_build_generation_payload_does_not_include_runtime_question_fields():
    detail = question_detail()

    payload = build_generation_payload(
        plan={"date": "2026-06-13", "main_theme": "SQL"},
        weak_points="weak",
        progress_summary="progress",
        mistake_log="mistakes",
        questions=[detail],
    )

    rendered = repr(payload)
    assert "questions" not in payload
    assert detail["url"] not in rendered
    assert detail["questionText"] not in rendered
    assert detail["answer"] not in rendered
    assert detail["explanation"] not in rendered
