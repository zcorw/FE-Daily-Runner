import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    os.getenv("RUN_DOCKER_REAL_RUN_SMOKE") != "1",
    reason="set RUN_DOCKER_REAL_RUN_SMOKE=1 to run Docker Compose real-run smoke test",
)
def test_docker_compose_dry_run_creates_preview_artifacts():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for real Docker dry-run smoke test")

    result = subprocess.run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "fe-daily-runner",
            "python",
            "scripts/daily_publish.py",
            "--today",
            "--dry-run",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        timeout=600,
    )

    assert result.returncode == 0, result.stderr
    assert any((ROOT / "site" / "tmp" / "dry-run").glob("*/preview.html"))
