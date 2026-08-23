# FE Daily Runner

A Python-based workflow that generates personalized daily study pages for Japan's Fundamental Information Technology Engineer Examination (FE).

> Part of **[FE Study System](https://github.com/zcorw/FE-System)** — the automated daily study generator powered by the shared question bank and OpenAI.

**FE Study System:**  
[System Overview](https://github.com/zcorw/FE-System) ·
[Question Bank](https://github.com/zcorw/fe-question-bank-service) ·
[Quiz App](https://github.com/zcorw/fe-siken-quiz-bot) ·
**Daily Runner**

## Role in the System

This service generates personalized daily study content from learning context
and shared FE question-bank data.

```text
Personal Study Context
          +
FE Question Bank Service
          +
       OpenAI
          │
          ↓
    Daily Runner
          │
          ↓
   Static Study Page
          │
          ↓
 Telegram Notification
```

Unlike the interactive quiz application, the Daily Runner operates as an
automated learning workflow rather than an on-demand practice interface.

It consumes question data through
[FE Question Bank Service](https://github.com/zcorw/fe-question-bank-service).

For the complete platform architecture, see
[FE-System](https://github.com/zcorw/FE-System).

## Project Documentation

Current operation and integration docs:

- [Project overview](docs/project-overview.md) - project purpose, boundaries, workflow, output policy.
- [Question Bank Runtime API integration](docs/question-bank-runtime-api.md) - Runtime endpoints, request/response shapes, image boundary, contract tests.
- [Deployment and operations](docs/deployment.md) - local and Docker setup, environment variables, run commands, scheduling.
- [Release verification checklist](docs/verification.md) - tests and smoke checks before publishing.

## Runtime Boundary

This application is a consumer of FE Question Bank Service Runtime API. It:

- does not read `data/fe_siken_questions.sqlite`
- does not read `docs/assets/fe-siken/`
- does not use Git commit/push as a publishing mechanism
- uses `QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000` inside Docker Compose
- renders static output under `site/` by default

## CLI Examples

```bash
python scripts/daily_publish.py --validate-config
python scripts/daily_publish.py --health-check
python scripts/daily_publish.py --date 2026-06-13 --dry-run
python scripts/daily_publish.py --date 2026-06-13 --write
python scripts/daily_publish.py --date 2026-06-13 --notify
python scripts/daily_publish.py --today --dry-run
```

Mode behavior:

- `--dry-run` creates only temporary JSON and page preview output.
- `--write` writes the formal daily page, index, progress, state, and log files.
- `--notify` performs a successful write first, then sends Telegram if configured.

## Docker Runtime

Prepare local real-run configuration:

```bash
cp .env.example .env
```

Edit `.env` and set at least `OPENAI_API_KEY`. Set `PAGE_BASE_URL`,
`TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` before using `--notify`.

Create the shared Docker network once:

```bash
docker network inspect fe-shared >/dev/null 2>&1 || docker network create fe-shared
```

The Compose service joins `fe-shared` and uses the Runtime service name:

```env
QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000
```

Verify from inside the consumer container:

```bash
docker exec <consumer-container> printenv QUESTION_BANK_SERVICE_URL
docker exec <consumer-container> curl -fsS http://question-bank-runtime:8000/health
```

Do not use `localhost` from inside the container to reach the question bank service.

Run the real workflow through Docker Compose:

```bash
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --write
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --notify
```

Expected output locations:

```text
site/tmp/dry-run/
site/daily/
site/index.html
personal/progress.md
state/daily_state.json
logs/daily_publish/
```

Optional Runtime API smoke test:

```bash
RUN_RUNTIME_SMOKE=1 QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000 python -m pytest tests/test_runtime_smoke.py
```

## Operations

Required and optional environment variables:

```env
OPENAI_API_KEY=...
QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000
PAGE_BASE_URL=https://example.com
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Run from cron or a container scheduler with one command per day:

```cron
10 6 * * * cd /app && python scripts/daily_publish.py --today --write
15 6 * * * cd /app && python scripts/daily_publish.py --today --notify
```

Operational logs are written under:

```text
logs/daily_publish/
```

Use `python scripts/daily_publish.py --health-check` or run
`curl -fsS http://question-bank-runtime:8000/health` inside the consumer container
before enabling the schedule.

## Browser Image Proxy

Generated pages use browser-facing image paths under `/assets/fe-siken/`.

The page output must not expose `http://question-bank-runtime:8000/` because that
hostname is only resolvable inside the Docker network. Serve or proxy
`/assets/fe-siken/<asset-path>` from the consumer app or reverse proxy to:

```text
$QUESTION_BANK_SERVICE_URL/assets/fe-siken/<asset-path>
```

## Development Kit and Historical Context

The repository also contains a portable development kit used during the rewrite
from the legacy FE Daily Runner architecture.

The new implementation was designed to:

- use Python instead of Codex for orchestration,
- use the OpenAI API for structured content generation,
- use Python templates, preferably Jinja2, to generate pages,
- read questions through FE Question Bank Service Runtime API,
- avoid direct local SQLite and local image-cache reads,
- avoid Git commit/push as the page delivery mechanism.

Legacy project references are kept only as supporting context and should not be
treated as the target runtime architecture.

For the original implementation, see
[FE-Daily-Runner](https://github.com/zcorw/FE-Daily-Runner).
