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
