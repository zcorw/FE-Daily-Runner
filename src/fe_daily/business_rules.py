from bs4 import BeautifulSoup

from fe_daily.secrets import SecretLeakError, assert_no_secret_leakage


FORBIDDEN_OUTPUT_MARKERS = (
    "data/fe_siken_questions.sqlite",
    "docs/assets/fe-siken/",
    "question-bank-runtime:8000",
)


class BusinessRuleError(ValueError):
    pass


def validate_generated_page_business_rules(html: str) -> None:
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        if marker in html:
            raise BusinessRuleError(f"page output contains forbidden marker: {marker}")

    try:
        assert_no_secret_leakage(html)
    except SecretLeakError as exc:
        raise BusinessRuleError(str(exc)) from exc

    soup = BeautifulSoup(html, "html.parser")
    questions = soup.select("[data-question]")
    if len(questions) != 10:
        raise BusinessRuleError(f"page must contain exactly 10 questions, got {len(questions)}")

    for index, question in enumerate(questions, start=1):
        text = question.get_text(" ", strip=True)
        source = question.find("a", href=True)
        if source is None:
            raise BusinessRuleError(f"question {index} missing source URL")
        for required in ("Question", "A:", "Answer:", "Explanation"):
            if required not in text:
                raise BusinessRuleError(f"question {index} missing {required}")
