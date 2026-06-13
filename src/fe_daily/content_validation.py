from typing import Any

from fe_daily.output_schema import DailyLearningContent


class ContentValidationError(ValueError):
    pass


def validate_question_facts(
    content: DailyLearningContent,
    runtime_details: list[dict[str, Any]],
) -> None:
    if len(content.questions) != len(runtime_details):
        raise ContentValidationError(
            f"question count mismatch: generated {len(content.questions)}, runtime {len(runtime_details)}"
        )

    for index, (generated, runtime) in enumerate(zip(content.questions, runtime_details, strict=True)):
        expected = {
            "source_url": runtime.get("url"),
            "question_text": runtime.get("questionText"),
            "choices": runtime.get("choices"),
            "answer": runtime.get("answer"),
            "explanation": runtime.get("explanation"),
            "images": runtime.get("images", []),
        }
        actual = {
            "source_url": str(generated.source_url).rstrip("/"),
            "question_text": generated.question_text,
            "choices": generated.choices,
            "answer": generated.answer,
            "explanation": generated.explanation,
            "images": generated.images,
        }
        for field, expected_value in expected.items():
            if actual[field] != expected_value:
                raise ContentValidationError(
                    f"question {index} {field} changed: expected {expected_value!r}, got {actual[field]!r}"
                )


def validate_learning_content_quality(
    content: DailyLearningContent,
    expected_plan: dict[str, Any],
) -> None:
    expected_theme = expected_plan.get("main_theme")
    if content.main_theme != expected_theme:
        raise ContentValidationError(
            f"main_theme mismatch: expected {expected_theme!r}, got {content.main_theme!r}"
        )

    expected_reading = expected_plan.get("reading_assignment")
    if content.plan_reference.reading_assignment != expected_reading:
        raise ContentValidationError(
            "reading_assignment mismatch: "
            f"expected {expected_reading!r}, got {content.plan_reference.reading_assignment!r}"
        )

    expected_focus = expected_plan.get("practice_focus")
    if content.plan_reference.practice_focus != expected_focus:
        raise ContentValidationError(
            f"practice_focus mismatch: expected {expected_focus!r}, got {content.plan_reference.practice_focus!r}"
        )

    if len(content.terms) < 10:
        raise ContentValidationError(f"terms must contain at least 10 items, got {len(content.terms)}")

    total_minutes = 0
    for entry in content.time_table:
        if isinstance(entry, dict):
            total_minutes += int(entry.get("minutes", 0))
    if total_minutes < 55 or total_minutes > 65:
        raise ContentValidationError(f"time_table must total about 60 minutes, got {total_minutes}")

    if not content.tomorrow_suggestion:
        raise ContentValidationError("tomorrow_suggestion must not be empty")
