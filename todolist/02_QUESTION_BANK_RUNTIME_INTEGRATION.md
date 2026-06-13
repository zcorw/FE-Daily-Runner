# 02 Question Bank Runtime Integration TodoList

## 目标

通过 FE Question Bank Service Runtime API 获取候选题、题目详情、答案、解说和图片引用，彻底替代每日生成阶段对本地 SQLite 和本地图库的读取。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 的配置、CLI、路径和测试基础。

## 具体任务列表

- [x] T101 [P0] 实现 Runtime API client
  - 目标: 支持 `GET /health`、`GET /keywords`、`GET /questions/candidates`、`POST /questions/candidates/search`、`GET /questions/by-url`、`GET /questions/{questionId}`、`POST /questions/details/batch`。
  - 验证: 使用 `pytest-httpx` 或 `respx` mock 成功、404、500、timeout。

- [x] T102 [P0] 实现 health check fail closed
  - 目标: `/health` 失败时每日生成必须停止，不生成页面，不调用 OpenAI，不写正式输出。
  - 验证: `--health-check` 返回非 0；日志包含失败原因。

- [x] T103 [P0] 解析 Practice Focus 到候选题查询
  - 目标: 将每日计划的 `Practice Focus` 转为 Runtime API 查询条件，在 Python 中选择题目。
  - 验证: SQL join/group 4、DB design 2、transaction 2、law 2 能映射为目标分布并产生选择报告。

- [x] T104 [P0] 实现 10 道科目 A 选择规则
  - 目标: 只选择 `exam_part = 科目A` 的题，最终必须正好 10 道；不足 10 道时失败。
  - 验证: 候选题不足时返回非 0，不调用 OpenAI 补题。

- [x] T105 [P0] 实现 batch details 获取
  - 目标: 使用 `includeAnswer=true` 和 `includeExplanation=true` 获取题干、选项、正解、解说、图片引用、来源 URL。
  - 验证: 每道题详情缺少来源 URL、正解或解说时失败。

- [ ] T106 [P0] 实现图片路径归一化
  - 目标: 将题库返回或 Markdown 中的图片引用统一为 `/assets/fe-siken/<asset-path>`。
  - 验证: 输入 `http://question-bank-runtime:8000/assets/fe-siken/r7/q1.png` 输出 `/assets/fe-siken/r7/q1.png`。

- [ ] T107 [P1] 设计浏览器图片代理交付边界
  - 目标: 明确静态 HTML 中只输出 `/assets/fe-siken/...`，由消费端或反向代理代理到 Runtime API。
  - 验证: 文档和配置中有 `/assets/fe-siken/` 代理说明；页面中不暴露 Docker 内部 URL。

- [ ] T108 [P1] 添加 Runtime API 集成 smoke test
  - 目标: 在 Docker 网络内验证 `QUESTION_BANK_SERVICE_URL=http://question-bank-runtime:8000` 可访问。
  - 验证: `docker exec <consumer-container> curl -fsS http://question-bank-runtime:8000/health` 成功。

## 推荐使用的成熟工具 / 库

- `httpx` 作为 HTTP client。
- `pytest-httpx` 或 `respx` mock HTTP。
- `tenacity` 可选用于 retry；也可用简单显式 retry，但必须可测试。
- `pydantic v2` 定义 Runtime API 响应模型。

## 不建议自行开发的部分

- 不手写复杂 HTTP 连接池，使用 `httpx.Client` 或 `httpx.AsyncClient`。
- 不在新项目中实现题库爬虫。
- 不读取 `data/fe_siken_questions.sqlite` 作为 fallback。
- 不挂载或读取 `docs/assets/fe-siken/` 作为本地图库。
- 不在每日生成中调用 Admin API。

## 可能涉及的文件或模块

- `src/fe_daily/question_bank_client.py`
- `src/fe_daily/question_selection.py`
- `src/fe_daily/image_paths.py`
- `src/fe_daily/models.py`
- `tests/test_question_bank_client.py`
- `tests/test_question_selection.py`
- `tests/test_image_paths.py`
- `docker-compose.yml`
- `README.md`

## 测试方式

- `python scripts/daily_publish.py --health-check`
- `python -m pytest tests/test_question_bank_client.py tests/test_question_selection.py tests/test_image_paths.py`
- `docker exec <consumer-container> printenv QUESTION_BANK_SERVICE_URL`
- `docker exec <consumer-container> curl -fsS http://question-bank-runtime:8000/health`

## 验收标准

- 每日生成候选题、详情、答案、解说、图片引用全部来自 Runtime API。
- 日常生成不使用 Admin API。
- 新项目不读取 `data/fe_siken_questions.sqlite`。
- 新项目不读取 `docs/assets/fe-siken/` 作为本地图库。
- 题库服务 `/health` 失败时 fail closed。
- 题目不足 10 道时 fail closed。
- 浏览器页面不包含 `http://question-bank-runtime:8000/...`。
- 所有图片路径规范化为 `/assets/fe-siken/<asset-path>`。

## 未确认问题 / AI 假设

- 假设 Runtime API 的 details batch 响应包含足够字段以构建页面题目区。
- 假设候选题 API 可按 topic/category/search 过滤；若字段不同，需要在 client 层做适配。
- 未确认是否需要独立的图片代理服务；当前任务只要求消费端或反向代理策略明确。
