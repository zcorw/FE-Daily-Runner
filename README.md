# FE Daily Python/OpenAI New Project Dev Kit

This folder is a portable development kit for building the new FE daily page generator in a separate project directory.

## Purpose

Use this folder as the single source package for the new project. It contains the project requirements, reference documents, legacy context, and the prompt for generating phased development TodoLists.

The new project should:

- Use Python instead of Codex for orchestration.
- Use OpenAI API for structured content generation.
- Use Python templates, preferably Jinja2, to generate pages.
- Read questions through FE Question Bank Service Runtime API.
- Avoid direct local SQLite and local image-cache reads.
- Avoid Git commit/push as the page delivery mechanism.

## Folder Structure

```text
new-project-dev-kit/
├─ README.md
├─ references/
│  ├─ PROJECT_REQUIREMENTS.md
│  ├─ question-bank-service/
│  │  └─ CONSUMER_INTEGRATION_GUIDE.md
│  ├─ legacy-project/
│  │  ├─ README.md
│  │  ├─ june-study-plan.md
│  │  ├─ database-and-assets.md
│  │  └─ daily_publish_prompt.md
│  ├─ personal-context/
│  │  ├─ progress.md
│  │  ├─ weak_points.md
│  │  └─ mistake_log.md
│  └─ legacy-todolist/
│     └─ 01_QUESTION_BANK_SERVICE_MIGRATION.md
├─ prompts/
│  └─ generate-development-todolists.md
└─ todolist/
   └─ README.md
```

## Recommended Use

1. Copy `new-project-dev-kit/` into the new project workspace.
2. Run the prompt in `prompts/generate-development-todolists.md`.
3. Generate TodoList files into `new-project-dev-kit/todolist/`.
4. Execute the TodoLists task by task in the new project, not in the legacy repository.

## Primary Document

Start from:

```text
references/PROJECT_REQUIREMENTS.md
```

Use other files only as supporting context.

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

## Browser Image Proxy

Generated pages use browser-facing image paths under `/assets/fe-siken/`.

The page output must not expose `http://question-bank-runtime:8000/` because that
hostname is only resolvable inside the Docker network. Serve or proxy
`/assets/fe-siken/<asset-path>` from the consumer app or reverse proxy to:

```text
$QUESTION_BANK_SERVICE_URL/assets/fe-siken/<asset-path>
```

## Notes

- `references/legacy-todolist/01_QUESTION_BANK_SERVICE_MIGRATION.md` is historical context. Do not treat it as the target architecture because it still reflects older migration thinking.
- New TodoLists should be generated under `todolist/`.
- The new project runtime must not depend on files under this legacy repository.
