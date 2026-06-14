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


def test_compose_reads_env_file_and_mounts_all_write_targets():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "env_file:" in compose
    assert "path: .env" in compose
    assert "required: false" in compose
    for mount in [
        "./site:/app/site",
        "./state:/app/state",
        "./logs:/app/logs",
        "./personal:/app/personal",
    ]:
        assert mount in compose


def test_dockerfile_includes_runtime_inputs_without_missing_config_copy():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY references ./references" in dockerfile
    assert "COPY config ./config" not in dockerfile
