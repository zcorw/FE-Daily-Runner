import os

import httpx
import pytest

from fe_daily.question_bank_client import QuestionBankClient


def runtime_service_url() -> str:
    if os.environ.get("RUN_RUNTIME_SMOKE") != "1":
        pytest.skip("set RUN_RUNTIME_SMOKE=1 to run the live Runtime API smoke test")

    return os.environ.get(
        "QUESTION_BANK_SERVICE_URL",
        "http://question-bank-runtime:8000",
    ).rstrip("/")


def test_question_bank_runtime_health_smoke():
    service_url = runtime_service_url()

    response = httpx.get(f"{service_url}/health", timeout=20)

    assert response.status_code == 200
    assert response.json().get("ok") is True


def test_question_bank_runtime_candidates_and_details_smoke():
    client = QuestionBankClient(runtime_service_url())

    candidates = client.search_candidates({"keywords": ["SQL"], "examPart": "科目A", "limit": 1})
    questions = candidates.get("questions", [])
    assert questions

    details = client.details_batch(
        [questions[0]["url"]],
        include_answer=True,
        include_explanation=True,
    )
    detail = details["questions"][0]
    assert detail["url"] == questions[0]["url"]
    for image in detail.get("images", []):
        assert image["publicPath"].startswith("/assets/fe-siken/")
