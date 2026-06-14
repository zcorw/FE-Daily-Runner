import subprocess


def test_docker_compose_uses_question_bank_service_name_inside_runner():
    result = subprocess.run(
        ["docker", "compose", "config"],
        check=True,
        text=True,
        capture_output=True,
    )

    config = result.stdout
    assert "QUESTION_BANK_SERVICE_URL: http://question-bank-runtime:8000" in config
    assert "QUESTION_BANK_SERVICE_URL: http://localhost" not in config
    assert "QUESTION_BANK_SERVICE_URL: http://127.0.0.1" not in config


def test_docker_compose_joins_external_fe_shared_network():
    result = subprocess.run(
        ["docker", "compose", "config"],
        check=True,
        text=True,
        capture_output=True,
    )

    config = result.stdout
    assert "fe-shared:" in config
    assert "external: true" in config
    assert "fe-shared: null" in config
