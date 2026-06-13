# 04 Template Page Rendering TodoList

## 目标

使用 Python 模板引擎渲染静态 HTML 页面，默认输出到 `site/daily/YYYY/MM/YYYY-MM-DD/index.html` 和 `site/index.html`，并在写入前完成 HTML、内容、路径和 secret 泄漏校验。

## 依赖任务

- 依赖 `01_PROJECT_SCAFFOLD_AND_CONFIG.md` 的路径和运行模式。
- 依赖 `02_QUESTION_BANK_RUNTIME_INTEGRATION.md` 的图片路径归一化。
- 依赖 `03_OPENAI_STRUCTURED_GENERATION.md` 的校验后结构化内容。

## 具体任务列表

- [x] T301 [P0] 创建 Jinja2 模板结构
  - 目标: 添加 `templates/base.html.j2`、`templates/daily_page.html.j2`、`templates/index_page.html.j2`、`templates/progress_entry.md.j2`、`templates/telegram_message.html.j2`。
  - 验证: 模板加载测试通过，缺失模板时报清晰错误。

- [x] T302 [P0] 实现每日页面渲染
  - 目标: 渲染今日目标、时间分配、书籍学习范围、学习清单、至少 10 个术语、知识点、正好 10 道科目 A 题、复盘区、明日建议。
  - 验证: BeautifulSoup 检查必需 section 和 10 道题。

- [x] T303 [P0] 实现首页索引渲染
  - 目标: 更新 `site/index.html`，展示最近每日页面、最新更新时间和当前学习策略。
  - 验证: index 包含当天 `/daily/YYYY-MM-DD/` 链接，重复运行不重复添加同一天。

- [x] T304 [P0] 实现原子写入
  - 目标: 使用临时文件写入并原子替换正式文件，失败时不留下半成品页面。
  - 验证: 模拟写入失败时正式文件保持旧内容，日志记录失败。

- [x] T305 [P0] 实现 HTML 和内容校验
  - 目标: 校验日期、permalink 或页面 URL、主题、阅读范围、10 道题、来源 URL、正解、解说、图片路径、secret 泄漏。
  - 验证: 每个校验规则有失败用例。

- [ ] T306 [P0] 实现图片路径输出规则
  - 目标: 页面中图片只能是 `/assets/fe-siken/...` 或其他明确允许的公共路径。
  - 验证: 页面中出现 `question-bank-runtime`、本地磁盘路径、`docs/assets/fe-siken/` 时失败。

- [ ] T307 [P1] 支持旧 Markdown 输出兼容配置
  - 目标: 默认 HTML 输出，必要时可配置生成旧 `docs/daily/YYYY/MM/YYYY-MM-DD.md` 和 `docs/index.md`。
  - 验证: 默认不写 `docs/`；启用兼容模式时路径和 front matter 正确。

## 推荐使用的成熟工具 / 库

- `Jinja2` 负责模板渲染。
- `BeautifulSoup4` 检查 HTML 结构。
- `pathlib` 和 `tempfile` 处理路径和临时文件。
- `os.replace` 或同等原子替换机制。

## 不建议自行开发的部分

- 不手写模板拼接 HTML。
- 不用字符串搜索替代 HTML parser 做结构校验。
- 不让 OpenAI 输出最终 HTML。
- 不在模板中读取 SQLite、本地图库或 `.env`。

## 可能涉及的文件或模块

- `templates/base.html.j2`
- `templates/daily_page.html.j2`
- `templates/index_page.html.j2`
- `templates/progress_entry.md.j2`
- `templates/telegram_message.html.j2`
- `src/fe_daily/page_renderer.py`
- `src/fe_daily/index_renderer.py`
- `src/fe_daily/output_writer.py`
- `src/fe_daily/content_validation.py`
- `tests/test_page_renderer.py`
- `tests/test_output_writer.py`
- `tests/test_content_validation.py`

## 测试方式

- `python -m pytest tests/test_page_renderer.py tests/test_output_writer.py tests/test_content_validation.py`
- `python scripts/daily_publish.py --date 2026-06-13 --render-only --input tmp/daily.json`
- 使用 BeautifulSoup 检查生成 HTML。

## 验收标准

- 默认正式页面路径为 `site/daily/YYYY/MM/YYYY-MM-DD/index.html`。
- 首页路径为 `site/index.html`。
- 页面必须正好包含 10 道科目 A 练习题。
- 每题包含来源 URL、题干、选项、正解、解说。
- 页面使用当天 Main Theme 和 20-Minute Reading Assignment，且不扩大到整章。
- 页面不包含 `question-bank-runtime`、本地图库路径或 secret。
- 写入失败时明确失败、写日志、返回非 0。

## 未确认问题 / AI 假设

- 假设静态站点路由 `/daily/YYYY-MM-DD/` 映射到 `site/daily/YYYY/MM/YYYY-MM-DD/index.html`。
- 假设页面可使用纯静态 HTML，不需要客户端框架。
- 未确认是否保留 Jekyll front matter；HTML 默认不需要，Markdown 兼容模式需要。
