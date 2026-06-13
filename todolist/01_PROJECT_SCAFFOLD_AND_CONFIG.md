# 01 Project Scaffold And Config TodoList

## 目标

建立新的 Python 3.11+ FE Daily Runner 应用骨架，使后续任务可以在同一配置、CLI、测试和 Docker 约束下实现。该阶段只创建项目基础能力，不接入真实 OpenAI 生成、不写正式每日页面。

## 依赖任务

- 无。

## 具体任务列表

- [x] T001 [P0] 创建 Python 项目结构
  - 目标: 建立 `src/fe_daily/`、`scripts/`、`tests/`、`templates/`、`config/`、`site/`、`state/`、`logs/daily_publish/` 等目录。
  - 验证: `python -m pytest` 能发现测试目录，空测试或基础导入测试通过。

- [x] T002 [P0] 添加 `pyproject.toml`
  - 目标: 声明 Python 3.11+、包名、测试配置、格式化和核心依赖入口。
  - 验证: `python -m pip install -e .` 或 `uv sync` 成功；`python -c "import fe_daily"` 成功。

- [x] T003 [P0] 实现配置读取
  - 目标: 从环境变量和 `.env` 读取运行配置，覆盖 `QUESTION_BANK_SERVICE_URL`、OpenAI 模型参数、输出目录、模板目录、运行模式、已有页面策略、Telegram 可选配置。
  - 验证: 配置测试覆盖默认值、缺失必填项、枚举非法值、secret 不进入 `repr` 或日志。

- [x] T004 [P0] 实现 CLI 参数骨架
  - 目标: 支持 `--date YYYY-MM-DD`、`--today`、`--dry-run`、`--write`、`--notify`、`--health-check`、`--validate-config`、`--render-only --input <json>`。
  - 验证: CLI 单元测试确认互斥参数和退出码；`--validate-config` 在缺少 OpenAI key 时明确失败或标记 dry-run 限制。

- [ ] T005 [P0] 固化运行模式语义
  - 目标: 明确定义 `dry-run` 只写临时预览、`write` 写正式页面和状态、`notify` 在成功 `write` 后通知。
  - 验证: 测试覆盖三种模式的允许写入路径和 Telegram 行为。

- [ ] T006 [P0] 建立路径安全和输出策略
  - 目标: 所有输出路径必须基于配置的输出根目录生成，禁止模型或用户输入直接决定路径；已有页面策略支持 `fail`、`skip`、`overwrite`。
  - 验证: 路径穿越、绝对路径逃逸、已有页面三种策略均有测试。

- [ ] T007 [P1] 添加 Dockerfile 和 docker-compose 骨架
  - 目标: 新应用容器可加入 external Docker network `fe-shared`，默认 `QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000`。
  - 验证: `docker compose config` 成功；配置中不出现容器内访问 `localhost` 的题库 URL。

- [ ] T008 [P1] 编写 README 初始运行说明
  - 目标: 说明本项目是 Runtime API consumer，不读取本地 SQLite 或本地图库，不使用 Git commit/push 发布。
  - 验证: README 包含 dry-run/write/notify 示例和 Docker 网络验证命令。

## 推荐使用的成熟工具 / 库

- `uv` 优先用于依赖管理，也可兼容 `pip`。
- `pydantic-settings` 或 `python-dotenv` 读取环境变量。
- `argparse` 优先用于少量命令；如命令复杂化再使用 `Typer`。
- `pytest`、`pytest-cov`、`time-machine` 或 `freezegun`。

## 不建议自行开发的部分

- 不手写 `.env` parser，使用成熟库。
- 不手写 CLI 参数互斥和帮助系统，使用 `argparse` 或 `Typer`。
- 不自行实现复杂配置校验框架，使用 `pydantic v2`。

## 可能涉及的文件或模块

- `pyproject.toml`
- `Dockerfile`
- `docker-compose.yml`
- `scripts/daily_publish.py`
- `src/fe_daily/config.py`
- `src/fe_daily/cli.py`
- `src/fe_daily/dates.py`
- `src/fe_daily/paths.py`
- `tests/test_config.py`
- `tests/test_cli.py`
- `tests/test_paths.py`
- `README.md`

## 测试方式

- `python scripts/daily_publish.py --validate-config`
- `python scripts/daily_publish.py --today --dry-run`
- `python -m pytest tests/test_config.py tests/test_cli.py tests/test_paths.py`
- `docker compose config`

## 验收标准

- CLI 可运行并给出明确退出码。
- 默认题库服务地址为 `http://question-bank-runtime:8000`。
- 容器内题库 URL 不使用 `localhost`。
- 项目配置不包含 OpenAI key、Telegram token 或 Admin API token 明文。
- 路径策略能阻止输出到配置目录以外。
- 该阶段没有实现真实每日生成，也没有读取 `data/fe_siken_questions.sqlite` 或 `docs/assets/fe-siken/`。

## 未确认问题 / AI 假设

- 假设项目包名使用 `fe_daily`。
- 假设 MVP 不需要 Web UI，只需要 CLI 和静态文件输出。
- 假设默认输出目录为 `site/`，旧 `docs/` Markdown 输出仅作为兼容配置。
- 未确认是否必须同时维护 `.codex/daily_state.json`；计划优先使用 `state/daily_state.json`，可兼容写旧路径。
