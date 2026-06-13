import pytest

from fe_daily.business_rules import BusinessRuleError, validate_generated_page_business_rules


def valid_page_html() -> str:
    questions = "\n".join(
        f"""
        <article data-question="{index}">
          <p>Question {index}</p>
          <ol><li>A: alpha</li><li>B: beta</li></ol>
          <p>Answer: A</p>
          <p>Explanation {index}</p>
          <a href="https://example.test/q{index}">Source</a>
        </article>
        """
        for index in range(1, 11)
    )
    return f"""
    <article data-page-type="daily">
      <section data-section="questions">{questions}</section>
    </article>
    """


def test_validate_generated_page_business_rules_accepts_valid_page():
    validate_generated_page_business_rules(valid_page_html())


@pytest.mark.parametrize(
    "forbidden",
    [
        "data/fe_siken_questions.sqlite",
        "docs/assets/fe-siken/",
        "question-bank-runtime:8000",
        "OPENAI_API_KEY",
    ],
)
def test_validate_generated_page_business_rules_rejects_forbidden_output(forbidden):
    with pytest.raises(BusinessRuleError):
        validate_generated_page_business_rules(valid_page_html() + forbidden)


def test_validate_generated_page_business_rules_requires_10_questions():
    html = valid_page_html().replace('data-question="10"', 'data-not-question="10"')

    with pytest.raises(BusinessRuleError):
        validate_generated_page_business_rules(html)


def test_validate_generated_page_business_rules_requires_question_fields():
    html = valid_page_html().replace("Explanation 1", "")

    with pytest.raises(BusinessRuleError):
        validate_generated_page_business_rules(html)
