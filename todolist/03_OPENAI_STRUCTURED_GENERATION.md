# 03 OpenAI Structured Generation TodoList

## 目标

使用 OpenAI Responses API 生成结构化学习内容，并通过 JSON Schema 或 `pydantic v2` 严格校验输出。OpenAI 只负责组织学习目标、知识点和复盘内容，不负责决定事实题目字段、路径、secret 或发布状态。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 的配置和 CLI。
- 依赖 `02_QUESTION_BANK_RUNTIME_INTEGRATION.md` 的真实题目详情模型。

## 具体任务列表

- [x] T201 [P0] 定义结构化输出模型
  - 目标: 定义 `DailyLearningContent`、`PlanReference`、`QuestionLearningBlock`、`ProgressSummary` 等 pydantic 模型。
  - 验证: 缺少 `date`、`main_theme`、`questions` 或题目字段时校验失败。

- [x] T202 [P0] 定义 OpenAI 输入边界
  - 目标: Prompt 输入包含当天计划、弱点、进度摘要、10 道真实题目详情；不包含 `.env`、token、Admin API 配置。
  - 验证: 单元测试确认构造的 prompt 不含 `OPENAI_API_KEY`、`TELEGRAM_BOT_TOKEN`、`.env` 内容。

- [x] T203 [P0] 实现 Responses API 调用
  - 目标: 使用 OpenAI Python SDK 调用 Responses API，默认 `OPENAI_MODEL=gpt-5.5`、reasoning effort `low`、text verbosity `medium`。
  - 验证: mock OpenAI client 返回结构化 JSON 后可解析。

- [x] T204 [P0] 实现模型事实边界校验
  - 目标: OpenAI 输出不得改写题干、选项、正确答案、来源 URL、图片路径；Python 以 Runtime API 题目事实为准。
  - 验证: 模型返回不同答案或来源 URL 时校验失败。

- [ ] T205 [P0] 实现结构化输出失败重试
  - 目标: 校验失败可重试一次，并将校验错误反馈给模型；再次失败则退出。
  - 验证: 测试覆盖第一次非法、第二次合法，以及两次都非法。

- [ ] T206 [P1] 生成学习内容质量规则
  - 目标: 校验至少 10 个重点术语、约 60 分钟时间表、当天 Main Theme、当天 20-Minute Reading Assignment、明日建议。
  - 验证: 输出不匹配当天计划时失败。

- [ ] T207 [P1] 保存 dry-run 调试 JSON
  - 目标: dry-run 将 OpenAI 原始输出、校验后 JSON 和页面预览写入临时目录，不写正式页面。
  - 验证: dry-run 后 `site/daily/.../index.html` 不存在，临时预览存在。

## 推荐使用的成熟工具 / 库

- `openai` Python SDK。
- OpenAI Responses API。
- Structured Outputs / JSON Schema。
- `pydantic v2` 作为主要校验工具。
- `jsonschema` 可用于补充 schema 回归测试。

## 不建议自行开发的部分

- 不手写 JSON schema validator，优先使用 `pydantic` 或 `jsonschema`。
- 不让 OpenAI 输出最终 HTML 文件。
- 不让 OpenAI 决定输出目录、模板路径、页面 URL、Telegram token、题目来源 URL、正确答案。
- 不让 OpenAI 编造题目补足数量。

## 可能涉及的文件或模块

- `src/fe_daily/openai_generator.py`
- `src/fe_daily/output_schema.py`
- `src/fe_daily/prompt_builder.py`
- `src/fe_daily/content_validation.py`
- `tests/test_openai_generator.py`
- `tests/test_output_schema.py`
- `tests/test_prompt_builder.py`
- `config/daily_output_schema.json`

## 测试方式

- `python -m pytest tests/test_output_schema.py tests/test_openai_generator.py tests/test_prompt_builder.py`
- `python scripts/daily_publish.py --date 2026-06-13 --dry-run`
- 人工检查 dry-run JSON 中不含 secret、Docker 内部图片 URL、本地文件路径。

## 验收标准

- OpenAI 输出必须经过 pydantic 或 JSON Schema 校验。
- OpenAI API 只生成结构化学习内容，不生成最终页面文件。
- 模型不能改写题库事实字段。
- 模型不能决定路径、模板、输出目录、页面 URL、Telegram secret 或发布状态。
- 结构化输出失败明确失败并写日志。
- dry-run 只写临时 JSON 和预览，不写正式页面，不发 Telegram。

## 未确认问题 / AI 假设

- 假设 `gpt-5.5` 在目标环境可用；如不可用，应通过配置替换模型，不改代码。
- 假设 Responses API structured output 能直接满足 pydantic schema；如 SDK 支持不同，需要在 adapter 中隔离。
- 未确认学习内容是否需要中日双语比例；计划按中文解释并保留日语术语。
