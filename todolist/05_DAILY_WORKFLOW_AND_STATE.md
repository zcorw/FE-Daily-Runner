# 05 Daily Workflow And State TodoList

## 目标

实现完整每日生成编排：读取日期、学习计划、个人上下文，调用题库 Runtime、OpenAI、模板渲染、正式写入，并更新进度、状态和运行日志。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 的 CLI 和配置。
- 依赖 `02_QUESTION_BANK_RUNTIME_INTEGRATION.md` 的题库数据。
- 依赖 `03_OPENAI_STRUCTURED_GENERATION.md` 的结构化内容。
- 依赖 `04_TEMPLATE_PAGE_RENDERING.md` 的页面和索引写入。

## 具体任务列表

- [x] T401 [P0] 实现 Asia/Tokyo 日期逻辑
  - 目标: `--today` 使用 Asia/Tokyo 日期，不依赖服务器本地时区。
  - 验证: 冻结时间跨 UTC 日期边界时仍得到东京日期。

- [ ] T402 [P0] 实现 June study plan parser
  - 目标: 从学习计划表读取当天 `Date`、`Main Theme`、`20-Minute Reading Assignment`、`Practice Focus`。
  - 验证: `2026-06-13` 返回 `データベース: 集計・結合` 和 SQL join/group 分布。

- [ ] T403 [P0] 实现计划缺失 fallback
  - 目标: 当天计划不存在时，基于 weak points、mistake log、recent progress 选择主题，并在日志写 `plan_source=fallback`。
  - 验证: 无计划日期生成 fallback 上下文，但不替换已有计划日期主题。

- [ ] T404 [P0] 实现 workflow orchestrator
  - 目标: 串联 health check、计划读取、候选题选择、详情获取、OpenAI 生成、schema 校验、页面渲染、内容校验、写入。
  - 验证: mock 全链路 dry-run 成功且不写正式页面。

- [ ] T405 [P0] 实现 `personal/progress.md` 更新
  - 目标: `--write` 和 `--notify` 成功后追加或更新当天进度，保留主题、题量、收获、易错点、明日建议、页面。
  - 验证: 重复运行同一天不重复追加，或按配置覆盖。

- [ ] T406 [P0] 实现状态文件更新
  - 目标: 写 `state/daily_state.json`，并可兼容 `.codex/daily_state.json`。
  - 验证: 状态包含 `last_run_date`、`last_daily_page`、`last_topics`、`last_question_count`、`status`。

- [ ] T407 [P0] 实现运行日志
  - 目标: 写 `logs/daily_publish/YYYY-MM-DD.md`，记录运行时间、模式、题目数、输出路径、计划来源、通知状态、错误。
  - 验证: 所有失败路径都写日志并返回非 0。

- [ ] T408 [P1] 实现幂等和已有页面策略
  - 目标: `fail`、`skip`、`overwrite` 控制同一天已有页面行为。
  - 验证: 三种策略分别有测试，`skip` 不调用 OpenAI。

## 推荐使用的成熟工具 / 库

- `zoneinfo` 处理 Asia/Tokyo。
- `markdown-it-py` 或简单表格 parser 可选；若 study plan 格式稳定，可用受控 Markdown table parser。
- `pydantic` 定义 workflow 状态模型。
- Python `logging` 写运行日志。

## 不建议自行开发的部分

- 不使用 Git commit/push 作为发布流程。
- 不把 Codex prompt 当作每日生成执行主体。
- 不让 OpenAI 决定状态文件内容和输出路径。
- 不在失败时继续写部分正式文件。

## 可能涉及的文件或模块

- `src/fe_daily/dates.py`
- `src/fe_daily/study_plan.py`
- `src/fe_daily/progress_context.py`
- `src/fe_daily/workflow.py`
- `src/fe_daily/state.py`
- `src/fe_daily/run_log.py`
- `scripts/daily_publish.py`
- `personal/progress.md`
- `state/daily_state.json`
- `.codex/daily_state.json`
- `logs/daily_publish/`
- `tests/test_study_plan.py`
- `tests/test_workflow.py`
- `tests/test_state.py`
- `tests/test_run_log.py`

## 测试方式

- `python -m pytest tests/test_study_plan.py tests/test_workflow.py tests/test_state.py tests/test_run_log.py`
- `python scripts/daily_publish.py --date 2026-06-13 --dry-run`
- `python scripts/daily_publish.py --date 2026-06-13 --write`

## 验收标准

- `--dry-run` 只生成临时 JSON 和预览，不写正式页面，不发 Telegram。
- `--write` 生成正式页面、首页、进度、状态和日志。
- `--notify` 必须执行成功的 `--write` 后才能发通知。
- 每日计划日期匹配时使用当天 Main Theme、20-Minute Reading Assignment 和 Practice Focus。
- 题目分布尽量匹配 Practice Focus。
- 服务不可用、题目不足、AI 校验失败、页面写入失败都明确失败并记录日志。
- 所有错误返回非 0 退出码。

## 未确认问题 / AI 假设

- 假设 `personal/progress.md` 继续使用 Markdown 追加格式。
- 假设状态文件迁移到 `state/daily_state.json`，旧 `.codex/` 路径仅为兼容。
- 未确认是否需要 file lock 防止 cron 并发；建议在后续运维任务中加入。
