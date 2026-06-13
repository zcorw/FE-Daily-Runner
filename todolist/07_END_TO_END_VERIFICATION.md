# 07 End To End Verification TodoList

## 目标

建立完整验收和回归测试，证明新 Python/OpenAI consumer app 可以在不读取本地 SQLite、不读取本地图库、不使用 Git 发布的前提下，完成 dry-run、write、notify 和失败路径。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 到 `06_TELEGRAM_AND_OPERATIONS.md` 全部核心能力。

## 具体任务列表

- [x] T601 [P0] 建立单元测试总入口
  - 目标: `python -m pytest` 覆盖配置、CLI、日期、学习计划、题库 client、OpenAI schema、模板、写入、状态、日志、Telegram。
  - 验证: 本地测试全部通过。

- [ ] T602 [P0] 建立 dry-run E2E 测试
  - 目标: 使用 mock Runtime API 和 mock OpenAI，执行 `--date 2026-06-13 --dry-run`。
  - 验证: 生成临时 JSON 和预览；不写 `site/daily/.../index.html`；不发 Telegram。

- [ ] T603 [P0] 建立 write E2E 测试
  - 目标: 使用临时输出目录执行 `--write`。
  - 验证: 生成每日页面、首页、progress、state、logs；页面正好 10 道题。

- [ ] T604 [P0] 建立 notify E2E 测试
  - 目标: 使用 mock Telegram API 执行 `--notify`。
  - 验证: write 成功后发送一次通知；通知包含日期、主题、题目数、页面 URL。

- [ ] T605 [P0] 建立失败路径矩阵
  - 目标: 覆盖 `/health` 失败、候选题不足、details 缺字段、OpenAI 输出非法、页面写入失败、Telegram 失败。
  - 验证: 每个失败都写日志，退出非 0；除 Telegram 可选失败外不报告成功。

- [ ] T606 [P0] 建立业务规则验收检查
  - 目标: 自动检查 35 条业务规则中可机器验证的项目。
  - 验证: 验收脚本确认未读取 SQLite、未读取本地图库、无 Docker 内部 URL、无 secret、题目数和字段完整。

- [ ] T607 [P1] 建立 Docker 网络 smoke test
  - 目标: 在容器内验证 `QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000` 和 `/health`。
  - 验证: `docker compose up` 后容器内 curl 成功。

- [ ] T608 [P1] 建立真实 Runtime API 集成验收
  - 目标: 在可用的 FE Question Bank Service 环境下获取候选题和 details batch。
  - 验证: dry-run 页面预览无 `question-bank-runtime` 浏览器 URL，图片路径为 `/assets/fe-siken/...`。

- [ ] T609 [P1] 编写最终发布前检查清单
  - 目标: README 或 `docs/verification.md` 提供手动验收命令和预期结果。
  - 验证: 清单覆盖 dry-run、write、notify、health-check、secret scan、Docker network。

## 推荐使用的成熟工具 / 库

- `pytest`。
- `pytest-httpx` 或 `respx`。
- `tmp_path` fixture。
- `BeautifulSoup4`。
- `time-machine` 或 `freezegun`。
- `coverage.py` / `pytest-cov` 可选。

## 不建议自行开发的部分

- 不手写 ad hoc 测试 runner。
- 不依赖真实 OpenAI API 做默认 CI 单元测试。
- 不依赖本地 SQLite 或本地图库作为 E2E fixture。
- 不把 Git commit/push 作为验收步骤。

## 可能涉及的文件或模块

- `tests/test_e2e_dry_run.py`
- `tests/test_e2e_write.py`
- `tests/test_e2e_notify.py`
- `tests/test_failure_paths.py`
- `tests/test_business_rules.py`
- `tests/fixtures/`
- `docs/verification.md`
- `README.md`

## 测试方式

- `python -m pytest`
- `python scripts/daily_publish.py --health-check`
- `python scripts/daily_publish.py --date 2026-06-13 --dry-run`
- `python scripts/daily_publish.py --date 2026-06-13 --write`
- `python scripts/daily_publish.py --date 2026-06-13 --notify`
- `docker compose config`
- `docker exec <consumer-container> curl -fsS http://question-bank-runtime:8000/health`

## 验收标准

- `python -m pytest` 通过。
- dry-run 不写正式页面、不发 Telegram。
- write 写正式页面、首页、进度、状态、日志。
- notify 在 write 成功后发送 Telegram。
- 题库服务不可用时 fail closed，不生成页面。
- 题目不足 10 道时失败，不让模型编造。
- AI 输出不合规时失败并保留临时调试 JSON。
- 页面写入失败时不留下半成品。
- 页面不包含 secret、Docker 内部 URL、本地 SQLite 路径、本地图库路径。
- 每日页面正好包含 10 道科目 A 题，且每道题有来源 URL、题干、选项、正解、解说。

## 未确认问题 / AI 假设

- 假设 CI 环境不具备真实 Docker Runtime API，真实集成验收可作为手动或 nightly 检查。
- 假设 OpenAI API 默认在单元测试中完全 mock，真实 API 只用于受控 smoke test。
- 未确认最终部署是否有独立反向代理；E2E 只验证页面路径策略和代理文档要求。
