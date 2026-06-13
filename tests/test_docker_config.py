from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_uses_python_runtime_and_installs_project():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in dockerfile
    assert "pip install --no-cache-dir -e ." in dockerfile
    assert "scripts/daily_publish.py" in dockerfile


def test_compose_uses_question_bank_runtime_service_name():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000" in compose
    assert "localhost" not in compose


def test_compose_declares_external_fe_shared_network():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "fe-shared:" in compose
    assert "external: true" in compose
    assert "- fe-shared" in compose
