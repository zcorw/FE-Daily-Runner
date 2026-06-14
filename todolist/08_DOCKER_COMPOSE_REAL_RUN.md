# 08 Docker Compose Real Run TodoList

## Project Summary

当前核心模块和 workflow 已实现并有单元/E2E 覆盖，但真实命令入口尚未把 `scripts/daily_publish.py --dry-run/--write/--notify` 接到 `run_daily_workflow()`。因此用户不能只写 `.env` 后用一条 `docker compose run` 完整跑完链路。

本阶段目标是补齐真实运行入口和 Docker 运行体验，使以下命令成为主要使用方式：

```bash
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --write
docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --notify
```

## Source Documents Reviewed

- `src/fe_daily/cli.py`
- `src/fe_daily/workflow.py`
- `src/fe_daily/config.py`
- `docker-compose.yml`
- `README.md`
- `docs/verification.md`
- `references/question-bank-service/CONSUMER_INTEGRATION_GUIDE.md`
- `todolist/01_PROJECT_SCAFFOLD_AND_CONFIG.md` through `todolist/07_END_TO_END_VERIFICATION.md`

## Key Requirements

- `.env` is the primary real-run configuration surface.
- Docker Compose should read `.env` and mount all write targets.
- CLI must call the already implemented workflow for `--dry-run`, `--write`, and `--notify`.
- Real run must use Runtime API, OpenAI API, templates, output writer, progress, state, logs, and optional Telegram.
- Missing Telegram config must not fail page generation.
- Runtime or OpenAI failures must fail closed and write logs.
- The app must not read local SQLite or local image cache.
- Browser-facing output must not expose `question-bank-runtime`.
- Question bank integration tests must verify the documented Runtime contract: `health`, `keywords`, candidates, search, by-url/detail, batch details, and asset `publicPath` behavior.
- Consumer Runtime requests must not use Admin API endpoints or send Admin bearer tokens.
- Docker Compose tests must reject `localhost` or `127.0.0.1` for the in-container question bank service URL.

## Questions / Assumptions

- Assumption: Real local Docker run uses `QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000` inside the shared Docker network.
- Assumption: Host-local direct Python runs may use `QUESTION_BANK_SERVICE_URL=http://localhost:8000`.
- Assumption: Reference files under `references/legacy-project/` and `references/personal-context/` are acceptable default inputs for this dev kit.
- Assumption: `PAGE_BASE_URL` is optional for dry-run but required for production notify quality.
- Open question: Final deployment may later move input documents out of `references/`; this TodoList only makes the current dev kit runnable.

## Development TodoList

- [x] T701 [P0] Wire CLI run modes to workflow
  - Goal / outcome: `python scripts/daily_publish.py --date 2026-06-13 --dry-run|--write|--notify` executes `run_daily_workflow()` instead of only printing the parsed mode.
  - Implementation notes:
    - In `src/fe_daily/cli.py`, load settings, resolve target date, instantiate `QuestionBankClient`, `OpenAIGenerator`, and optional `TelegramNotifier`.
    - Pass default study plan and personal context file contents into `run_daily_workflow()`.
    - Return `0` on success/skipped optional notification and non-zero on hard failure.
  - Files likely involved:
    - `src/fe_daily/cli.py`
    - `scripts/daily_publish.py`
    - `tests/test_cli.py`
    - new `tests/test_cli_workflow.py` if useful
  - Dependencies: Existing `run_daily_workflow()`, `QuestionBankClient`, `OpenAIGenerator`.
  - Verification:
    - Mock CLI test proves `main(["--date", "2026-06-13", "--dry-run"])` calls workflow and writes dry-run artifacts.
    - Mock CLI test proves `--write` writes formal outputs.

- [x] T702 [P0] Add configurable input document paths
  - Goal / outcome: The CLI can find study plan, weak points, mistake log, and progress context from `.env` defaults without hardcoding fragile paths in workflow calls.
  - Implementation notes:
    - Add settings fields:
      - `study_plan_path`
      - `weak_points_path`
      - `mistake_log_path`
      - `progress_context_path`
    - Defaults should point to current dev kit files:
      - `references/legacy-project/june-study-plan.md`
      - `references/personal-context/weak_points.md`
      - `references/personal-context/mistake_log.md`
      - `references/personal-context/progress.md`
    - Validate blank paths are rejected.
  - Files likely involved:
    - `src/fe_daily/config.py`
    - `tests/test_config.py`
    - `.env.example`
  - Dependencies: T701 can use temporary defaults, but final real-run UX depends on this.
  - Verification:
    - Settings test confirms defaults.
    - Settings test confirms env overrides.

- [x] T703 [P0] Provide `.env.example` for full real run
  - Goal / outcome: User can copy `.env.example` to `.env`, fill secrets, and run Docker Compose.
  - Implementation notes:
    - Include Runtime, OpenAI, output, template, input path, page base URL, existing page policy, timezone, and Telegram variables.
    - Do not include real secrets.
  - Files likely involved:
    - `.env.example`
    - `README.md`
    - `tests/test_readme.py`
  - Dependencies: T702.
  - Verification:
    - Test or README assertion confirms `.env.example` contains required variable names and no placeholder that looks like a real token.

- [x] T704 [P0] Update Docker Compose for one-command real run
  - Goal / outcome: `docker compose run --rm fe-daily-runner ...` has all required env and writable mounts.
  - Implementation notes:
    - Ensure Compose reads `.env`.
    - Mount or include:
      - `site/`
      - `state/`
      - `logs/`
      - `personal/`
    - Ensure templates and references are available inside the image/container.
    - Preserve `fe-shared` external network.
  - Files likely involved:
    - `docker-compose.yml`
    - `Dockerfile`
    - `.dockerignore` if present or needed
    - `tests/test_readme.py`
  - Dependencies: T701, T702, T703.
  - Verification:
    - `docker compose config` passes.
    - Config output includes `fe-shared`, env variables, and mounts for output/state/logs/personal.

- [x] T711 [P0] Add question bank Runtime contract test suite
  - Goal / outcome: Prove the current `QuestionBankClient` matches `references/question-bank-service/CONSUMER_INTEGRATION_GUIDE.md` for consumer read-only integration.
  - Implementation notes:
    - Use `httpx.MockTransport` so the test does not require a live Runtime service.
    - Cover documented consumer endpoints:
      - `GET /health`
      - `GET /keywords`
      - `GET /questions/candidates`
      - `POST /questions/candidates/search`
      - `GET /questions/by-url?url=<question-url>`
      - `GET /questions/{questionId}`
      - `POST /questions/details/batch`
    - Assert `details_batch()` sends `urls`, `includeAnswer`, and `includeExplanation`.
    - Assert Runtime requests do not include `Authorization: Bearer ...` and do not call Admin paths.
    - Keep HTTP error and timeout behavior fail-closed.
  - Files likely involved:
    - `tests/test_question_bank_client.py`
    - new `tests/test_question_bank_contract.py` if separating contract coverage is clearer
    - `src/fe_daily/question_bank_client.py`
  - Dependencies: Existing `QuestionBankClient`.
  - Verification:
    - `python -m pytest tests/test_question_bank_client.py tests/test_question_bank_contract.py -q`

- [x] T712 [P0] Add documented query-flow integration test
  - Goal / outcome: The consumer flow from the integration guide is covered end to end without real network calls.
  - Implementation notes:
    - Test flow: health check -> candidate search -> select question URLs -> batch details -> render or preview output.
    - Mock Runtime responses with `questionText`, `choices`, `images`, and `publicPath`.
    - Assert the generated output uses `/assets/fe-siken/...` paths and does not expose `http://question-bank-runtime:8000/...` to browser-facing HTML.
    - Assert the flow does not read local SQLite files or local question image cache paths.
  - Files likely involved:
    - `tests/test_cli_workflow.py`
    - new `tests/test_question_bank_flow.py` if useful
    - `src/fe_daily/workflow.py`
    - `src/fe_daily/output.py`
  - Dependencies: T701, T711.
  - Verification:
    - `python -m pytest tests/test_question_bank_flow.py tests/test_cli_workflow.py -q`

- [x] T713 [P0] Add Docker Compose question-bank service-name contract test
  - Goal / outcome: Docker configuration follows the question bank service guide for same-network Compose integration.
  - Implementation notes:
    - Parse `docker compose config` output or inspect `docker-compose.yml`.
    - Assert the runner joins external network `fe-shared`.
    - Assert in-container `QUESTION_BANK_SERVICE_URL` is `http://question-bank-runtime:8000`.
    - Assert the Compose environment does not configure `localhost` or `127.0.0.1` for the in-container Runtime URL.
  - Files likely involved:
    - `tests/test_docker_compose_contract.py`
    - `docker-compose.yml`
    - `.env.example`
  - Dependencies: T703, T704.
  - Verification:
    - `docker compose config`
    - `python -m pytest tests/test_docker_compose_contract.py -q`

- [ ] T714 [P1] Extend opt-in live Runtime smoke with asset/publicPath checks
  - Goal / outcome: When real services are available, the smoke test verifies not only health/details but also asset delivery semantics from the integration guide.
  - Implementation notes:
    - Keep the test opt-in with `RUN_RUNTIME_SMOKE=1`.
    - Use `QUESTION_BANK_SERVICE_URL` and fetch one returned `publicPath` through `$QUESTION_BANK_SERVICE_URL/assets/fe-siken/...`.
    - Assert the upstream asset response is successful and non-empty.
    - Assert browser-facing output keeps `/assets/fe-siken/...` and does not contain `question-bank-runtime`.
  - Files likely involved:
    - `tests/test_runtime_smoke.py`
    - `docs/verification.md`
  - Dependencies: T712.
  - Verification:
    - Default test run skips the live smoke.
    - `RUN_RUNTIME_SMOKE=1 QUESTION_BANK_SERVICE_URL=<runtime-url> python -m pytest tests/test_runtime_smoke.py -q`

- [x] T705 [P0] Add CLI-level dry-run integration test
  - Goal / outcome: The command entrypoint, not only `run_daily_workflow()`, is covered for dry-run.
  - Implementation notes:
    - Use fake question client factory and fake OpenAI generator injection, or add injectable factories to `main()`.
    - Avoid real OpenAI and real Runtime.
  - Files likely involved:
    - `src/fe_daily/cli.py`
    - `tests/test_cli_workflow.py`
  - Dependencies: T701.
  - Verification:
    - `main(["--date", "2026-06-13", "--dry-run"], ...)` returns `0`.
    - Dry-run JSON and preview exist.
    - Formal `site/daily/.../index.html` does not exist.

- [x] T706 [P0] Add CLI-level write integration test
  - Goal / outcome: `--write` through CLI writes daily page, index, progress, state, and log.
  - Implementation notes:
    - Use temp output root and fake clients.
    - Assert generated page has exactly 10 questions.
  - Files likely involved:
    - `src/fe_daily/cli.py`
    - `tests/test_cli_workflow.py`
  - Dependencies: T701, T705.
  - Verification:
    - `main(["--date", "2026-06-13", "--write"], ...)` returns `0`.
    - Expected formal files exist.

- [x] T707 [P0] Add CLI-level notify integration test
  - Goal / outcome: `--notify` through CLI performs write first, then sends one Telegram message when configured.
  - Implementation notes:
    - Use fake Telegram notifier.
    - Assert missing Telegram config is skipped with exit `0`.
    - Assert configured Telegram sends once and message contains date, theme, and page URL.
  - Files likely involved:
    - `src/fe_daily/cli.py`
    - `tests/test_cli_workflow.py`
  - Dependencies: T701, T706.
  - Verification:
    - Notify success returns `0`.
    - Notify missing env returns `0` and logs skipped status.

- [x] T708 [P1] Add real-run Docker documentation
  - Goal / outcome: README gives exact copy/paste commands for local Docker real run.
  - Implementation notes:
    - Include:
      - copy `.env.example` to `.env`
      - create `fe-shared`
      - start/verify question bank runtime
      - `docker compose run --rm ... --dry-run`
      - `docker compose run --rm ... --write`
      - `docker compose run --rm ... --notify`
      - output locations
  - Files likely involved:
    - `README.md`
    - `docs/verification.md`
    - `tests/test_readme.py`
  - Dependencies: T703, T704.
  - Verification:
    - README tests assert all real-run commands are documented.

- [x] T709 [P1] Add optional real Docker run smoke script or test
  - Goal / outcome: A guarded smoke test can run the actual Docker Compose dry-run with `.env` when real services are available.
  - Implementation notes:
    - Keep opt-in via env var such as `RUN_DOCKER_REAL_RUN_SMOKE=1`.
    - Do not require real OpenAI in normal unit tests unless explicitly enabled.
    - If real OpenAI is required, skip unless `OPENAI_API_KEY` is set.
  - Files likely involved:
    - `tests/test_docker_real_run_smoke.py`
    - `docs/verification.md`
  - Dependencies: T704, T708.
  - Verification:
    - Default test is skipped.
    - With env enabled, dry-run command exits `0` and creates preview artifacts.

- [ ] T710 [P1] Clean up pytest asyncio warning
  - Goal / outcome: Local test output is clean enough for release verification.
  - Implementation notes:
    - Add `asyncio_default_fixture_loop_scope = "function"` or equivalent supported pytest config.
    - Confirm no warning remains.
  - Files likely involved:
    - `pyproject.toml`
  - Dependencies: None.
  - Verification:
    - `python -m pytest -q` passes without the `pytest_asyncio` deprecation warning.

## Acceptance Criteria

- `python scripts/daily_publish.py --date 2026-06-13 --dry-run` executes the full workflow with configured services.
- `python scripts/daily_publish.py --date 2026-06-13 --write` writes formal page, index, progress, state, and logs.
- `python scripts/daily_publish.py --date 2026-06-13 --notify` writes first, then sends Telegram only after success.
- `docker compose run --rm fe-daily-runner python scripts/daily_publish.py --today --dry-run` works after `.env` is configured and Runtime is reachable.
- `docker compose config` passes.
- Default unit tests do not require real OpenAI, real Telegram, or real Runtime.
- Opt-in smoke tests document exactly what real services are required.
- No generated output leaks local SQLite paths, local image cache paths, Docker-internal browser URLs, or secrets.
- Question bank contract tests cover every documented consumer Runtime endpoint used by the service integration flow.
- Compose contract tests fail if the runner tries to reach the Runtime service through `localhost` inside Docker.
- Live Runtime smoke tests, when enabled, cover health, candidate search, detail batch, and at least one asset/publicPath check.
- Consumer code and tests do not require or send Admin API credentials for normal question bank reads.

## Suggested Execution Order

1. T702
2. T701
3. T711
4. T712
5. T705
6. T706
7. T707
8. T703
9. T704
10. T713
11. T708
12. T709
13. T714
14. T710
