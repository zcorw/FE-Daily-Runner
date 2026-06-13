import pytest

from fe_daily.question_details import QuestionDetailValidationError, load_required_details


class DetailsClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def details_batch(self, urls, *, include_answer, include_explanation):
        self.calls.append(
            {
                "urls": urls,
                "include_answer": include_answer,
                "include_explanation": include_explanation,
            }
        )
        return self.payload


def valid_detail(url="https://example.test/q1"):
    return {
        "url": url,
        "questionText": "Question text",
        "choices": {"ア": "A", "イ": "B", "ウ": "C", "エ": "D"},
        "answer": "ア",
        "explanation": "Explanation",
        "images": [],
    }


def test_load_required_details_requests_answer_and_explanation():
    client = DetailsClient({"questions": [valid_detail()]})

    details = load_required_details(client, ["https://example.test/q1"])

    assert details == [valid_detail()]
    assert client.calls == [
        {
            "urls": ["https://example.test/q1"],
            "include_answer": True,
            "include_explanation": True,
        }
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("url", ""),
        ("questionText", ""),
        ("choices", {}),
        ("answer", ""),
        ("explanation", ""),
    ],
)
def test_load_required_details_rejects_missing_required_fields(field, value):
    detail = valid_detail()
    detail[field] = value
    client = DetailsClient({"questions": [detail]})

    with pytest.raises(QuestionDetailValidationError) as exc_info:
        load_required_details(client, ["https://example.test/q1"])

    assert field in str(exc_info.value)


def test_load_required_details_rejects_mismatched_count():
    client = DetailsClient({"questions": [valid_detail("https://example.test/q1")]})

    with pytest.raises(QuestionDetailValidationError):
        load_required_details(client, ["https://example.test/q1", "https://example.test/q2"])
