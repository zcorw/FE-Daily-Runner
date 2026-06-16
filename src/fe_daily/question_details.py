from typing import Any, Protocol

from fe_daily.image_paths import normalize_image_src


class QuestionDetailValidationError(ValueError):
    pass


class DetailsClient(Protocol):
    def details_batch(
        self,
        urls: list[str],
        *,
        include_answer: bool,
        include_explanation: bool,
    ) -> dict[str, Any]:
        pass


def load_required_details(client: DetailsClient, urls: list[str]) -> list[dict[str, Any]]:
    payload = client.details_batch(
        urls,
        include_answer=True,
        include_explanation=True,
    )
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise QuestionDetailValidationError("details response must contain questions list")

    if len(questions) != len(urls):
        raise QuestionDetailValidationError(
            f"details count mismatch: requested {len(urls)}, received {len(questions)}"
        )

    for index, detail in enumerate(questions):
        _validate_detail(detail, index)
        _normalize_detail_images(detail)

    return questions


def _validate_detail(detail: Any, index: int) -> None:
    if not isinstance(detail, dict):
        raise QuestionDetailValidationError(f"question detail {index} must be an object")

    required_text_fields = ["url", "questionText", "answer", "explanation"]
    for field in required_text_fields:
        value = detail.get(field)
        if not isinstance(value, str) or not value.strip():
            raise QuestionDetailValidationError(f"question detail {index} missing {field}")

    choices = detail.get("choices")
    if not isinstance(choices, dict) or not choices:
        raise QuestionDetailValidationError(f"question detail {index} missing choices")

    distractor_explanations = detail.get("distractor_explanations")
    if not isinstance(distractor_explanations, dict) or not distractor_explanations:
        raise QuestionDetailValidationError(f"question detail {index} missing distractor_explanations")


def _normalize_detail_images(detail: dict[str, Any]) -> None:
    images = detail.get("images", [])
    if not isinstance(images, list):
        return

    for image in images:
        if not isinstance(image, dict):
            continue
        public_path = image.get("publicPath")
        if isinstance(public_path, str):
            image["publicPath"] = normalize_image_src(public_path)
