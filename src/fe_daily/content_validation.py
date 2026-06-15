import re
from typing import Any

from bs4 import BeautifulSoup

from fe_daily.output_schema import DailyLearningContent


DEFAULT_PUBLIC_IMAGE_PREFIXES = ("/assets/fe-siken/",)
TERM_PLACEHOLDER_VALUES = (
    "Connect this term to the planned practice topic.",
    "Do not confuse the term with a neighboring concept.",
)


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
            "images": _image_public_paths(runtime.get("images", [])),
        }
        actual = {
            "source_url": str(generated.source_url).rstrip("/"),
            "question_text": generated.question_text,
            "choices": generated.choices,
            "answer": generated.answer,
            "images": _image_public_paths(generated.images),
        }
        if not generated.explanation.strip():
            raise ContentValidationError(f"question {index} explanation must not be blank")
        if not _contains_cjk(generated.explanation):
            raise ContentValidationError(f"question {index} explanation must be Chinese")
        for field, expected_value in expected.items():
            if actual[field] != expected_value:
                raise ContentValidationError(
                    f"question {index} {field} changed: expected {expected_value!r}, got {actual[field]!r}"
                )
        _validate_distractor_explanations(index, generated)


def _image_public_paths(images: list[dict[str, Any]]) -> list[str | None]:
    return [image.get("publicPath") for image in images]


def _contains_cjk(text: str) -> bool:
    return re.search(r"[\u4e00-\u9fff]", text) is not None


def _validate_distractor_explanations(index: int, generated: Any) -> None:
    explanations = generated.distractor_explanations
    if not isinstance(explanations, dict):
        raise ContentValidationError(f"question {index} distractor_explanations must be an object")

    wrong_labels = [label for label in generated.choices if label != generated.answer]
    values: list[str] = []
    for label in wrong_labels:
        value = explanations.get(label)
        if not isinstance(value, str) or not value.strip():
            raise ContentValidationError(
                f"question {index} distractor_explanations missing explanation for {label}"
            )
        if not _contains_cjk(value):
            raise ContentValidationError(
                f"question {index} distractor_explanations for {label} must be Chinese"
            )
        values.append(value.strip())

    if len(values) > 1 and len(set(values)) != len(values):
        raise ContentValidationError(f"question {index} distractor_explanations must not be repeated")


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
    _validate_term_table(content.terms)

    total_minutes = 0
    for entry in content.time_table:
        if isinstance(entry, dict):
            total_minutes += int(entry.get("minutes", 0))
    if total_minutes < 55 or total_minutes > 65:
        raise ContentValidationError(f"time_table must total about 60 minutes, got {total_minutes}")

    if not content.tomorrow_suggestion:
        raise ContentValidationError("tomorrow_suggestion must not be empty")


def _validate_term_table(terms: list[Any]) -> None:
    exam_notes: list[str] = []
    traps: list[str] = []
    for index, item in enumerate(terms):
        if not isinstance(item, dict):
            raise ContentValidationError(f"terms {index} must be an object")
        for field in ("term", "meaning", "exam_note", "trap"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ContentValidationError(f"terms {index} {field} must not be blank")
            if value.strip() in TERM_PLACEHOLDER_VALUES:
                raise ContentValidationError(f"terms {index} {field} must not use placeholder text")
        exam_notes.append(item["exam_note"].strip())
        traps.append(item["trap"].strip())

    if len(set(exam_notes)) != len(exam_notes):
        raise ContentValidationError("terms exam_note values must be specific, not repeated")
    if len(set(traps)) != len(traps):
        raise ContentValidationError("terms trap values must be specific, not repeated")


def validate_daily_html(
    html: str,
    content: DailyLearningContent,
    *,
    page_url: str,
    allowed_image_prefixes: tuple[str, ...] = DEFAULT_PUBLIC_IMAGE_PREFIXES,
) -> None:
    _validate_no_secret_leakage(html)
    soup = BeautifulSoup(html, "html.parser")

    page = soup.select_one('article[data-page-type="daily"]')
    if page is None:
        raise ContentValidationError("daily page article is missing")

    expected_date = content.date.isoformat()
    if page.get("data-date") != expected_date:
        raise ContentValidationError(f"date mismatch: expected {expected_date}")

    if page.get("data-page-url") != page_url:
        raise ContentValidationError(f"page_url mismatch: expected {page_url}")

    if page.get("data-main-theme") != content.main_theme:
        raise ContentValidationError("main_theme mismatch in rendered HTML")

    heading = page.find("h1")
    if heading is None or heading.get_text(strip=True) != content.title:
        raise ContentValidationError("title mismatch in rendered HTML")

    reading_section = soup.select_one('[data-section="reading-assignment"]')
    if reading_section is None or content.plan_reference.reading_assignment not in reading_section.get_text(" ", strip=True):
        raise ContentValidationError("reading_assignment missing from rendered HTML")

    rendered_questions = soup.select('[data-section="questions"] [data-question]')
    if len(rendered_questions) != 10 or len(content.questions) != 10:
        raise ContentValidationError(
            f"question count must be exactly 10: rendered {len(rendered_questions)}, content {len(content.questions)}"
        )

    for index, (rendered, expected) in enumerate(zip(rendered_questions, content.questions, strict=True), start=1):
        rendered_text = rendered.get_text(" ", strip=True)
        if expected.question_text not in rendered_text:
            raise ContentValidationError(f"question {index} question_text missing")
        answer_text = _question_answer_text(rendered)
        if answer_text != f"Correct answer: {expected.answer}":
            raise ContentValidationError(f"question {index} answer mismatch")
        if expected.explanation not in rendered_text:
            raise ContentValidationError(f"question {index} explanation missing")

        source = rendered.find("a", href=True)
        expected_source = str(expected.source_url).rstrip("/")
        if source is None or source["href"].rstrip("/") != expected_source:
            raise ContentValidationError(f"question {index} source_url mismatch")

    _validate_image_paths(soup, allowed_image_prefixes)


def _validate_no_secret_leakage(html: str) -> None:
    secret_markers = ("OPENAI_API_KEY", "API_KEY", "SECRET", "TOKEN", ".env")
    if any(marker in html for marker in secret_markers):
        raise ContentValidationError("secret leakage detected in rendered HTML")


def _question_answer_text(rendered_question: Any) -> str:
    for paragraph in rendered_question.find_all("p"):
        text = paragraph.get_text("", strip=True)
        if text.startswith("Correct answer:"):
            return text
    return ""


def _validate_image_paths(soup: BeautifulSoup, allowed_image_prefixes: tuple[str, ...]) -> None:
    for image in soup.find_all("img"):
        source = image.get("src", "")
        if not source.startswith(allowed_image_prefixes):
            raise ContentValidationError(f"image path is not public: {source}")
