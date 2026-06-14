# Release Verification Checklist

Run these checks before publishing or enabling the daily schedule.

## Unit And E2E

```bash
python -m pytest
python scripts/daily_publish.py --date 2026-06-13 --dry-run
python scripts/daily_publish.py --date 2026-06-13 --write
python scripts/daily_publish.py --date 2026-06-13 --notify
python scripts/daily_publish.py --health-check
```

Expected results:

- `--dry-run` writes only `site/tmp/dry-run/YYYY-MM-DD/` artifacts.
- `--write` writes the daily page, index, progress, state, and log files.
- `--notify` performs a successful write before sending Telegram.
- `--health-check` fails closed when the question bank Runtime is unavailable.

## Secret Scan

Run the automated secret scan tests:

```bash
python -m pytest tests/test_secrets.py tests/test_business_rules.py
```

Confirm generated pages, dry-run JSON, logs, and Telegram messages contain no secret scan markers such as `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, or `ADMIN_API_TOKEN`.

## Docker Network

Prepare local Docker configuration:

```bash
cp .env.example .env
```

Fill `.env` with `OPENAI_API_KEY` before real generation. Fill
`PAGE_BASE_URL`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` before
notification checks.

Create the shared network once:

```bash
docker network create fe-shared
docker compose config
```

Run the real Docker workflow:

```bash
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --write
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --notify
```

Expected artifacts:

- `site/tmp/dry-run/`
- `site/daily/`
- `site/index.html`
- `personal/progress.md`
- `state/daily_state.json`
- `logs/daily_publish/`

Optional live smoke checks:

```bash
RUN_DOCKER_SMOKE=1 CONSUMER_CONTAINER=<container> python -m pytest tests/test_docker_smoke.py
RUN_RUNTIME_SMOKE=1 QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000 python -m pytest tests/test_runtime_smoke.py
```
