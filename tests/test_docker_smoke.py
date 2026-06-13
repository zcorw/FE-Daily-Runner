import os
import subprocess

import pytest


@pytest.mark.skipif(os.getenv("RUN_DOCKER_SMOKE") != "1", reason="set RUN_DOCKER_SMOKE=1 to run Docker network smoke test")
def test_docker_container_can_reach_question_bank_runtime_health():
    container = os.environ["CONSUMER_CONTAINER"]

    result = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "curl",
            "-fsS",
            "http://question-bank-runtime:8000/health",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
