from pathlib import Path


VERIFICATION = Path(__file__).resolve().parents[1] / "docs" / "verification.md"


def test_verification_doc_covers_release_checks():
    text = VERIFICATION.read_text(encoding="utf-8")

    for expected in [
        "python -m pytest",
        "--dry-run",
        "--write",
        "--notify",
        "--health-check",
        "secret scan",
        "docker network create fe-shared",
        "RUN_DOCKER_REAL_RUN_SMOKE=1",
    ]:
        assert expected in text
