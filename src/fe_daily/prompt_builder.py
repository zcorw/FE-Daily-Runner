import json
from typing import Any


FORBIDDEN_PROMPT_MARKERS = (
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "ADMIN_API_TOKEN",
    ".env",
)


class PromptBoundaryError(ValueError):
    pass


def build_generation_payload(
    *,
    plan: dict[str, Any],
    weak_points: str,
    progress_summary: str,
    mistake_log: str,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    _ = questions
    payload = {
        "plan": plan,
        "personal_context": {
            "weak_points": weak_points,
            "progress_summary": progress_summary,
            "mistake_log": mistake_log,
        },
        "generation_rules": {
            "openai_must_not_generate_question_content": True,
            "output_must_copy_plan_fields_exactly": [
                "date",
                "main_theme",
                "reading_assignment",
                "practice_focus",
            ],
            "page_structure_language": "Japanese",
            "generated_learning_content_language": "Japanese",
            "japanese_content_fields": [
                "goals",
                "time_table.task",
                "terms.meaning",
                "terms.exam_note",
                "terms.trap",
                "knowledge_points.title",
                "knowledge_points.body",
                "tomorrow_suggestion.theme",
            ],
            "page_format_reference": "FE Daily Study Task markdown",
            "minimum_key_terms": 10,
            "key_terms_table_fields": [
                "term",
                "meaning",
                "exam_note",
                "trap",
            ],
            "key_terms_must_have_unique_exam_notes_and_traps": True,
            "key_terms_instruction": (
                "Return at least 10 distinct key terms for the daily theme. Every key term must include "
                "a non-empty term, meaning, exam_note, and trap. The exam_note and trap values must be "
                "specific to that term, must not repeat across rows, and must be written in Japanese."
            ),
            "language_instruction": (
                "Write all generated learning content in Japanese. Do not generate practice questions, "
                "question text, choices, answers, explanations, or distractor explanations; those fields "
                "are injected from the Runtime question-bank response after OpenAI generation."
            ),
            "required_page_sections_in_order": [
                "今日の目標",
                "時間配分",
                "書籍の読解範囲",
                "学習チェックリスト",
                "重要用語",
                "知識メモ",
                "科目A 練習問題",
                "復習欄",
                "明日の提案",
            ],
            "openai_must_not_decide_paths_or_secrets": True,
            "python_validates_output_schema": True,
        },
    }
    _reject_forbidden_markers(payload)
    return payload


def _reject_forbidden_markers(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False)
    for marker in FORBIDDEN_PROMPT_MARKERS:
        if marker in rendered:
            raise PromptBoundaryError(f"prompt payload contains forbidden marker: {marker}")
