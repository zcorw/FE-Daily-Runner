# Project Documentation Map

## Project Purpose And Product Scope

| Document | Covers |
|---|---|
| [README.md](../README.md) | Short project summary, runtime boundary, CLI examples, Docker entry points, operations notes, and documentation index. |
| [project-overview.md](./project-overview.md) | Project purpose, product boundary, high-level workflow, output policy, and language policy. |
| [PROJECT_REQUIREMENTS.md](../references/PROJECT_REQUIREMENTS.md) | Original product requirements, migration goals, MVP scope, constraints, and acceptance criteria. |
| [verification.md](./verification.md) | Release verification checklist, secret-scan checks, Docker checks, and optional smoke tests. |

## Architecture And Data

| Document | Covers |
|---|---|
| [deployment.md](./deployment.md) | Local and Docker deployment, environment variables, Docker network, output volumes, scheduling, verification, and failure handling. |
| [question-bank-runtime-api.md](./question-bank-runtime-api.md) | Runtime API integration contract, endpoints, request/response shapes, auth boundary, asset URL boundary, and contract checks. |
| [question-bank-runtime-topic-search-requirements.md](./question-bank-runtime-topic-search-requirements.md) | Required Runtime topic-search behavior, topic metadata, shortage/fallback semantics, and acceptance tests for accurate question selection. |
| [CONSUMER_INTEGRATION_GUIDE.md](../references/question-bank-service/CONSUMER_INTEGRATION_GUIDE.md) | Upstream question-bank service consumer guide and Runtime integration expectations. |
| [database-and-assets.md](../references/legacy-project/database-and-assets.md) | Legacy question-bank database and image-asset context used only as reference material, not as a direct runtime dependency. |

## Development And Execution Plans

| Document | Covers |
|---|---|
| [01_PROJECT_SCAFFOLD_AND_CONFIG.md](../todolist/01_PROJECT_SCAFFOLD_AND_CONFIG.md) | Project scaffolding and configuration tasks. |
| [02_QUESTION_BANK_RUNTIME_INTEGRATION.md](../todolist/02_QUESTION_BANK_RUNTIME_INTEGRATION.md) | Question Bank Runtime integration tasks. |
| [03_OPENAI_STRUCTURED_GENERATION.md](../todolist/03_OPENAI_STRUCTURED_GENERATION.md) | OpenAI structured generation tasks. |
| [04_TEMPLATE_PAGE_RENDERING.md](../todolist/04_TEMPLATE_PAGE_RENDERING.md) | Static page template and rendering tasks. |
| [05_DAILY_WORKFLOW_AND_STATE.md](../todolist/05_DAILY_WORKFLOW_AND_STATE.md) | Daily workflow, state, and progress tasks. |
| [06_TELEGRAM_AND_OPERATIONS.md](../todolist/06_TELEGRAM_AND_OPERATIONS.md) | Telegram notification and operational tasks. |
| [07_END_TO_END_VERIFICATION.md](../todolist/07_END_TO_END_VERIFICATION.md) | End-to-end verification tasks. |
| [08_DOCKER_COMPOSE_REAL_RUN.md](../todolist/08_DOCKER_COMPOSE_REAL_RUN.md) | Docker Compose real-run tasks and remaining full-chain work. |

## Prompts And Reference Context

| Document | Covers |
|---|---|
| [generate-development-todolists.md](../prompts/generate-development-todolists.md) | Prompt for turning project documents into ordered development TodoLists. |
| [execute-development-todolists.md](../prompts/execute-development-todolists.md) | Prompt template for executing TodoList items task by task. |
| [summarize-question-bank-keywords.md](../prompts/summarize-question-bank-keywords.md) | Prompt for summarizing Japanese question-bank data into searchable keyword and taxonomy outputs. |
| [june-study-plan.md](../references/legacy-project/june-study-plan.md) | Legacy daily study plan used as the default study-plan input. |
| [personal-context](../references/personal-context/) | Reference weak points, mistake log, and progress context used for local generation inputs. |

