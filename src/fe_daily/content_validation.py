from typing import Any

from bs4 import BeautifulSoup

from fe_daily.output_schema import DailyLearningContent


DEFAULT_PUBLIC_IMAGE_PREFIXES = ("/assets/fe-siken/",)


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

    heading = page.find("h1")
    if heading is None or heading.get_text(strip=True) != content.main_theme:
        raise ContentValidationError("main_theme mismatch in rendered HTML")

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
        if f"Answer: {expected.answer}" not in rendered_text:
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


def _validate_image_paths(soup: BeautifulSoup, allowed_image_prefixes: tuple[str, ...]) -> None:
    for image in soup.find_all("img"):
        source = image.get("src", "")
        if not source.startswith(allowed_image_prefixes):
            raise ContentValidationError(f"image path is not public: {source}")
