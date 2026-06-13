import os

import httpx
import pytest


def test_question_bank_runtime_health_smoke():
    if os.environ.get("RUN_RUNTIME_SMOKE") != "1":
        pytest.skip("set RUN_RUNTIME_SMOKE=1 to run the live Runtime API smoke test")

    service_url = os.environ.get(
        "QUESTION_BANK_SERVICE_URL",
        "http://question-bank-runtime:8000",
    ).rstrip("/")

    response = httpx.get(f"{service_url}/health", timeout=20)

    assert response.status_code == 200
    assert response.json().get("ok") is True
