# 06 Telegram And Operations TodoList

## 目标

实现可选 Telegram 通知、部署运行说明、Docker 网络验证、失败通知和生产运行安全要求。Telegram 缺少配置时应跳过通知，但不影响成功的页面生成。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 的配置。
- 依赖 `04_TEMPLATE_PAGE_RENDERING.md` 的 Telegram message template。
- 依赖 `05_DAILY_WORKFLOW_AND_STATE.md` 的 write 成功状态和日志。

## 具体任务列表

- [x] T501 [P0] 实现 Telegram notifier
  - 目标: 使用 Telegram Bot API `sendMessage`，支持 HTML 转义和 `parse_mode=HTML`。
  - 验证: mock HTTP 请求中 token 不进入日志；HTML 特殊字符被转义。

- [ ] T502 [P0] 实现缺失环境变量跳过通知
  - 目标: 缺少 `TELEGRAM_BOT_TOKEN` 或 `TELEGRAM_CHAT_ID` 时记录 skipped，不失败。
  - 验证: `--notify` 在页面生成成功但缺少 Telegram 配置时退出 0，日志写 `Telegram skipped: missing env`。

- [ ] T503 [P0] 限制 notify 只能在 write 成功后执行
  - 目标: 如果页面写入、校验、状态更新任一步失败，不发送成功通知。
  - 验证: 模拟页面校验失败时 Telegram 不被调用。

- [ ] T504 [P1] 实现失败通知
  - 目标: 如果 Telegram 配置存在，题库服务不可用、OpenAI 校验失败、页面写入失败时发送失败通知。
  - 验证: 失败通知不包含 secret，只包含日期、阶段、错误摘要。

- [ ] T505 [P1] 生成部署运行文档
  - 目标: README 说明 Docker network `fe-shared`、环境变量、cron 或容器定时任务、health check、日志路径。
  - 验证: README 包含 `docker network create fe-shared` 和容器内 `curl /health` 验证步骤。

- [ ] T506 [P1] 添加并发运行保护
  - 目标: 使用 lock file 或平台调度锁防止同一天多个 publish 并发写文件。
  - 验证: 并发启动第二个进程时退出或等待策略明确，日志记录。

- [ ] T507 [P1] 添加 secret 泄漏扫描
  - 目标: 在页面、日志、临时 JSON、Telegram 文案写出前扫描敏感键名和已知 token 值。
  - 验证: 注入 `OPENAI_API_KEY`、`TELEGRAM_BOT_TOKEN`、`ADMIN_API_TOKEN` 的测试内容时校验失败。

## 推荐使用的成熟工具 / 库

- `httpx` 调用 Telegram Bot API。
- `Jinja2` 渲染 Telegram HTML 模板。
- Python `html.escape` 或模板自动转义。
- `filelock` 可选用于并发锁。

## 不建议自行开发的部分

- 不手写 Telegram HTTP 编码细节，使用 `httpx` 表单或 JSON 请求。
- 不在日志中打印 Telegram token、OpenAI key 或 Admin token。
- 不用 GitHub Pages blob URL 作为默认发布地址；页面 URL 由 `PAGE_BASE_URL` 和静态路由决定。
- 不公开 Admin API 给日常生成容器。

## 可能涉及的文件或模块

- `src/fe_daily/telegram_notifier.py`
- `src/fe_daily/secrets.py`
- `src/fe_daily/locks.py`
- `templates/telegram_message.html.j2`
- `tests/test_telegram_notifier.py`
- `tests/test_secrets.py`
- `tests/test_locks.py`
- `README.md`
- `docker-compose.yml`

## 测试方式

- `python -m pytest tests/test_telegram_notifier.py tests/test_secrets.py tests/test_locks.py`
- `python scripts/daily_publish.py --date 2026-06-13 --notify`
- `docker compose config`
- `docker exec <consumer-container> curl -fsS http://question-bank-runtime:8000/health`

## 验收标准

- Telegram 为可选能力。
- 缺少 Telegram 环境变量时页面生成仍可成功。
- `--notify` 只在 `--write` 成功后发送成功通知。
- Telegram 失败时写日志，且不泄漏 token。
- 页面 URL 优先来自 `PAGE_BASE_URL + /daily/YYYY-MM-DD/`。
- 部署说明明确 Docker 内部访问题库服务使用 `question-bank-runtime:8000`，不使用 `localhost`。
- 日志、页面、临时文件、通知均不泄漏 secret。

## 未确认问题 / AI 假设

- 假设通知只需要 Telegram Bot API，不需要其他通知渠道。
- 假设 cron 或宿主调度在后续部署中决定；MVP 只提供命令和容器运行方式。
- 未确认是否需要失败通知在 dry-run 中启用；当前假设 dry-run 不发 Telegram。
