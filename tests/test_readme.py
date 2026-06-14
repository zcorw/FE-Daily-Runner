from pathlib import Path


README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_documents_cli_run_modes():
    text = README.read_text(encoding="utf-8")

    assert "python scripts/daily_publish.py --date 2026-06-13 --dry-run" in text
    assert "python scripts/daily_publish.py --date 2026-06-13 --write" in text
    assert "python scripts/daily_publish.py --date 2026-06-13 --notify" in text


def test_readme_documents_docker_shared_network():
    text = README.read_text(encoding="utf-8")

    assert "docker network create fe-shared" in text
    assert "QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000" in text
    assert "curl -fsS http://question-bank-runtime:8000/health" in text


def test_readme_documents_consumer_boundaries():
    text = README.read_text(encoding="utf-8")

    assert "does not read `data/fe_siken_questions.sqlite`" in text
    assert "does not read `docs/assets/fe-siken/`" in text
    assert "does not use Git commit/push as a publishing mechanism" in text


def test_readme_documents_browser_image_proxy_boundary():
    text = README.read_text(encoding="utf-8")

    assert "/assets/fe-siken/" in text
    assert "browser-facing image paths" in text
    assert "must not expose `http://question-bank-runtime:8000/`" in text


def test_readme_documents_operations_schedule_and_logs():
    text = README.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY" in text
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "cron" in text
    assert "logs/daily_publish/" in text


def test_readme_documents_one_command_docker_real_run_flow():
    text = README.read_text(encoding="utf-8")

    assert "cp .env.example .env" in text
    assert "docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run" in text
    assert "docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --write" in text
    assert "docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --notify" in text
    assert "site/tmp/dry-run/" in text
    assert "site/daily/" in text
