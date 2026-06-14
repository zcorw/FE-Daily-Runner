import json

import httpx

from fe_daily.question_bank_client import QuestionBankClient


def test_runtime_contract_requests_are_read_only_and_do_not_send_admin_auth():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path != "/admin"
        assert not request.url.path.startswith("/admin/")
        assert "authorization" not in request.headers

        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/keywords":
            return httpx.Response(200, json={"keywords": ["SQL"]})
        if request.url.path == "/questions/candidates":
            return httpx.Response(200, json={"questions": [{"url": "https://example.test/q1"}]})
        if request.url.path == "/questions/candidates/search":
            return httpx.Response(200, json={"questions": [{"url": "https://example.test/q1"}]})
        if request.url.path == "/questions/by-url":
            return httpx.Response(200, json={"id": "q1", "url": request.url.params["url"]})
        if request.url.path == "/questions/q1":
            return httpx.Response(200, json={"id": "q1"})
        if request.url.path == "/questions/details/batch":
            payload = json.loads(request.read())
            assert payload == {
                "urls": ["https://example.test/q1"],
                "includeAnswer": True,
                "includeExplanation": False,
            }
            return httpx.Response(
                200,
                json={
                    "questions": [
                        {
                            "url": "https://example.test/q1",
                            "images": [{"publicPath": "/assets/fe-siken/q1.png"}],
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected Runtime path: {request.url.path}")

    client = QuestionBankClient(
        "http://question-bank-runtime:8000",
        transport=httpx.MockTransport(handler),
    )

    assert client.health()["ok"] is True
    assert client.keywords()["keywords"] == ["SQL"]
    assert client.candidates(exam_part="科目A", limit=1)["questions"][0]["url"] == "https://example.test/q1"
    assert client.search_candidates({"keywords": ["SQL"], "limit": 1})["questions"][0]["url"] == "https://example.test/q1"
    assert client.question_by_url("https://example.test/q1")["id"] == "q1"
    assert client.question("q1")["id"] == "q1"
    details = client.details_batch(
        ["https://example.test/q1"],
        include_answer=True,
        include_explanation=False,
    )

    assert details["questions"][0]["images"][0]["publicPath"] == "/assets/fe-siken/q1.png"
    assert [request.url.path for request in requests] == [
        "/health",
        "/keywords",
        "/questions/candidates",
        "/questions/candidates/search",
        "/questions/by-url",
        "/questions/q1",
        "/questions/details/batch",
    ]


def test_asset_url_uses_runtime_asset_endpoint_without_leaking_browser_proxy_path():
    client = QuestionBankClient("http://question-bank-runtime:8000/")

    assert client.asset_url("/assets/fe-siken/07_haru/a6/06.png") == (
        "http://question-bank-runtime:8000/assets/fe-siken/07_haru/a6/06.png"
    )
