import json

import httpx
import pytest

from fe_daily.question_bank_client import (
    QuestionBankError,
    QuestionBankClient,
    QuestionBankHTTPError,
    QuestionBankTimeoutError,
)


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return QuestionBankClient("http://question-bank-runtime:8000", transport=transport)


def json_response(data, status_code=200):
    return httpx.Response(status_code, json=data)


def test_health_gets_runtime_health_endpoint():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/health"
        return json_response({"ok": True, "database": "ready", "readOnly": True})

    client = make_client(handler)

    assert client.health() == {"ok": True, "database": "ready", "readOnly": True}


def test_keywords_gets_runtime_keywords_endpoint():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/keywords"
        return json_response({"keywords": ["SQL", "security"]})

    client = make_client(handler)

    assert client.keywords() == {"keywords": ["SQL", "security"]}


def test_candidates_gets_candidate_endpoint_with_params():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/questions/candidates"
        assert request.url.params["examPart"] == "科目A"
        assert request.url.params["limit"] == "10"
        return json_response({"questions": [{"url": "https://example.test/q1"}]})

    client = make_client(handler)

    assert client.candidates(exam_part="科目A", limit=10)["questions"][0]["url"] == "https://example.test/q1"


def test_search_candidates_posts_json_body():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/questions/candidates/search"
        assert json.loads(request.read()) == {"keywords": ["SQL"], "examPart": "科目A", "limit": 10}
        return json_response({"questions": []})

    client = make_client(handler)

    assert client.search_candidates({"keywords": ["SQL"], "examPart": "科目A", "limit": 10}) == {
        "questions": []
    }


def test_search_candidates_normalizes_runtime_list_response_and_question_url_key():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/questions/candidates/search"
        return json_response(
            [
                {
                    "questionId": "q1",
                    "questionUrl": "https://www.fe-siken.com/kakomon/sample/q1.html",
                    "examPart": "科目A",
                }
            ]
        )

    client = make_client(handler)

    assert client.search_candidates({"keywords": ["SQL"], "examPart": "科目A", "limit": 1}) == {
        "questions": [
            {
                "questionId": "q1",
                "questionUrl": "https://www.fe-siken.com/kakomon/sample/q1.html",
                "url": "https://www.fe-siken.com/kakomon/sample/q1.html",
                "examPart": "科目A",
            }
        ]
    }


def test_question_by_url_gets_encoded_source_url():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/questions/by-url"
        assert request.url.params["url"] == "https://www.fe-siken.com/kakomon/sample/q1.html"
        return json_response({"url": "https://www.fe-siken.com/kakomon/sample/q1.html"})

    client = make_client(handler)

    result = client.question_by_url("https://www.fe-siken.com/kakomon/sample/q1.html")

    assert result["url"] == "https://www.fe-siken.com/kakomon/sample/q1.html"


def test_question_gets_question_by_id():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/questions/q123"
        return json_response({"id": "q123"})

    client = make_client(handler)

    assert client.question("q123") == {"id": "q123"}


def test_details_batch_posts_expected_payload():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/questions/details/batch"
        assert request.read() == (
            b'{"urls":["https://example.test/q1"],"includeAnswer":true,"includeExplanation":true}'
        )
        return json_response({"questions": [{"url": "https://example.test/q1"}]})

    client = make_client(handler)

    result = client.details_batch(["https://example.test/q1"], include_answer=True, include_explanation=True)

    assert result == {"questions": [{"url": "https://example.test/q1"}]}


def test_details_batch_normalizes_runtime_items_and_choice_list():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/questions/details/batch"
        return json_response(
            {
                "items": [
                    {
                        "questionUrl": "https://example.test/q1",
                        "questionText": "Question",
                        "choices": [
                            {"label": "ア", "text": "alpha"},
                            {"label": "イ", "text": "beta"},
                        ],
                        "answer": "ア",
                        "learningExplanation": {
                            "explanationJa": "題庫の解説です。",
                            "distractorExplanationsJa": {"イ": "イは誤りです。"},
                            "knowledgePointJa": "題庫の知識点です。",
                            "examPointJa": "試験での着眼点です。",
                            "commonTrapJa": "よくある誤りです。",
                        },
                        "explanationJa": "題庫の解説です。",
                        "distractorExplanationsJa": {"イ": "イは誤りです。"},
                        "knowledgePointJa": "題庫の知識点です。",
                        "examPointJa": "試験での着眼点です。",
                        "commonTrapJa": "よくある誤りです。",
                        "images": [],
                    }
                ]
            }
        )

    client = make_client(handler)

    assert client.details_batch(["https://example.test/q1"], include_answer=True, include_explanation=True) == {
        "questions": [
            {
                "url": "https://example.test/q1",
                "questionUrl": "https://example.test/q1",
                "questionText": "Question",
                "choices": {"ア": "alpha", "イ": "beta"},
                "answer": "ア",
                "learningExplanation": {
                    "explanationJa": "題庫の解説です。",
                    "distractorExplanationsJa": {"イ": "イは誤りです。"},
                    "knowledgePointJa": "題庫の知識点です。",
                    "examPointJa": "試験での着眼点です。",
                    "commonTrapJa": "よくある誤りです。",
                },
                "explanationJa": "題庫の解説です。",
                "distractorExplanationsJa": {"イ": "イは誤りです。"},
                "knowledgePointJa": "題庫の知識点です。",
                "examPointJa": "試験での着眼点です。",
                "commonTrapJa": "よくある誤りです。",
                "explanation": "題庫の解説です。",
                "distractor_explanations": {"イ": "イは誤りです。"},
                "knowledge_point": "題庫の知識点です。",
                "exam_point": "試験での着眼点です。",
                "common_trap": "よくある誤りです。",
                "images": [],
            }
        ]
    }


def test_http_errors_raise_clear_exception():
    client = make_client(lambda _request: json_response({"detail": "missing"}, status_code=404))

    with pytest.raises(QuestionBankHTTPError) as exc_info:
        client.question("missing")

    assert exc_info.value.status_code == 404
    assert "GET /questions/missing failed" in str(exc_info.value)


def test_timeout_errors_raise_clear_exception():
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    client = make_client(handler)

    with pytest.raises(QuestionBankTimeoutError):
        client.health()


def test_request_errors_raise_clear_exception():
    def handler(request):
        raise httpx.ConnectError("dns failed", request=request)

    client = make_client(handler)

    with pytest.raises(QuestionBankError) as exc_info:
        client.health()

    assert "GET /health request failed" in str(exc_info.value)
