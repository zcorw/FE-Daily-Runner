# Deployment And Operations

## Prerequisites

- Python 3.11 for local runs
- Docker and Docker Compose for container runs
- FE Question Bank Service Runtime reachable on the shared Docker network
- OpenAI API key for real content generation
- Telegram bot token and chat id only when using `--notify`

## Configuration

Create local configuration:

```bash
cp .env.example .env
```

Required for real OpenAI generation:

```env
OPENAI_API_KEY=...
```

Required Runtime setting inside Docker:

```env
QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000
```

Required for absolute Telegram page links:

```env
PAGE_BASE_URL=https://your-public-site.example
```

Required only for `--notify`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Never commit `.env`, generated pages, run logs, token logs, or local state.

## Docker Network

Create the shared network once:

```bash
docker network create fe-shared
```

The question-bank Runtime container and the FE Daily runner container must both
join `fe-shared`. The runner uses `question-bank-runtime` as the Runtime service
name.

Validate the Compose configuration:

```bash
docker compose config
```

## Local Commands

Install and run locally:

```bash
python -m pip install -e .
python scripts/daily_publish.py --validate-config
python scripts/daily_publish.py --health-check
python scripts/daily_publish.py --date 2026-06-13 --dry-run
python scripts/daily_publish.py --date 2026-06-13 --write
python scripts/daily_publish.py --date 2026-06-13 --notify
```

Run modes:

- `--dry-run`: writes only preview artifacts under `site/tmp/dry-run/`
- `--write`: writes formal page, index, progress, state, and logs
- `--notify`: runs a successful write first, then sends Telegram

## Docker Commands

Build the runner image:

```bash
docker compose build fe-daily-runner
```

Run the workflow:

```bash
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --write
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --notify
```

When overwriting an existing page intentionally:

```bash
docker compose run --rm -e EXISTING_PAGE_POLICY=overwrite fe-daily-runner python scripts/daily_publish.py --today --write
```

## Output Volumes

The Compose service mounts these local directories into the container:

```text
./site:/app/site
./state:/app/state
./logs:/app/logs
./personal:/app/personal
```

Expected outputs:

```text
site/tmp/dry-run/
site/daily/
site/index.html
personal/progress.md
state/daily_state.json
logs/daily_publish/
logs/openai_token_usage.jsonl
```

## Scheduling

Example cron entries:

```cron
10 6 * * * cd /app && python scripts/daily_publish.py --today --write
15 6 * * * cd /app && python scripts/daily_publish.py --today --notify
```

Use only one scheduled writer per output directory. The runner uses a daily lock
to reduce duplicate runs, but scheduling should still avoid overlapping writes.

## Verification Before Release

Run:

```bash
python -m pytest
docker compose config
python scripts/daily_publish.py --health-check
```

Optional live checks:

```bash
RUN_RUNTIME_SMOKE=1 QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000 python -m pytest tests/test_runtime_smoke.py
RUN_DOCKER_SMOKE=1 CONSUMER_CONTAINER=<container> python -m pytest tests/test_docker_smoke.py
RUN_DOCKER_REAL_RUN_SMOKE=1 OPENAI_API_KEY=<key> python -m pytest tests/test_docker_real_run_smoke.py
```

See also [verification.md](verification.md).

## Failure Handling

- Runtime unavailable: `--health-check` fails and normal workflow stops before
  generation.
- Existing page conflict: controlled by `EXISTING_PAGE_POLICY`
  (`fail`, `skip`, or `overwrite`).
- Telegram config missing: `--notify` writes the page but skips notification.
- Validation failure: page is not written, Telegram is not sent, and the command
  exits non-zero.

