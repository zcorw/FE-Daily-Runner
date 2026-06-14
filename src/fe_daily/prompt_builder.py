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
    payload = {
        "plan": plan,
        "personal_context": {
            "weak_points": weak_points,
            "progress_summary": progress_summary,
            "mistake_log": mistake_log,
        },
        "questions": [_question_fact_payload(question) for question in questions],
        "generation_rules": {
            "openai_must_not_change_question_facts": True,
            "output_must_copy_plan_fields_exactly": [
                "date",
                "main_theme",
                "reading_assignment",
                "practice_focus",
            ],
            "openai_must_not_decide_paths_or_secrets": True,
            "python_validates_output_schema": True,
        },
    }
    _reject_forbidden_markers(payload)
    return payload


def _question_fact_payload(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_url": question.get("url"),
        "question_text": question.get("questionText"),
        "choices": question.get("choices"),
        "answer": question.get("answer"),
        "explanation": question.get("explanation"),
        "images": question.get("images", []),
    }


def _reject_forbidden_markers(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False)
    for marker in FORBIDDEN_PROMPT_MARKERS:
        if marker in rendered:
            raise PromptBoundaryError(f"prompt payload contains forbidden marker: {marker}")
