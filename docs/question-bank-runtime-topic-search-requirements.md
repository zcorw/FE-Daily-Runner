# 题库 Runtime 主题检索能力调整要求

## 背景

FE Daily Runner 需要根据当天学习计划生成每日练习页面。页面中的 `Subject-A Practice Questions` 必须与当天学习主题和 `Practice Focus` 保持一致，例如：

- `main_theme`: `トランザクション / ロック`
- `practice_focus`: `Transaction 4, lock/recovery 3, SQL 2, security 1`

当前 consumer 侧已经按 `practice_focus` 拆分主题配额，并调用题库 Runtime 的候选题搜索接口：

```http
POST /questions/candidates/search
```

请求示例：

```json
{
  "keywords": ["Transaction"],
  "examPart": "科目A",
  "limit": 5
}
```

## 当前问题

在真实 Docker Compose 链路中，Runtime 对不同 `keywords` 返回同一批候选题，无法体现主题过滤。

已验证的请求与结果：

| keywords | examPart | 返回结果 |
|---|---|---|
| `Transaction` | `科目A` | `07_haru/a1.html` 到 `07_haru/a5.html` |
| `トランザクション` | `科目A` | `07_haru/a1.html` 到 `07_haru/a5.html` |
| `lock` | `科目A` | `07_haru/a1.html` 到 `07_haru/a5.html` |
| `SQL` | `科目A` | `07_haru/a1.html` 到 `07_haru/a5.html` |

这会导致 FE Daily Runner 虽然请求了当天主题题目，但实际页面仍可能出现 AI、数值表現、探索木、稼働率、ローコード等与当天主题不相关的题。

## 调整目标

题库 Runtime 需要提供可被 consumer 可靠使用的主题检索能力，使 FE Daily Runner 能完成以下目标：

1. 按当天 `practice_focus` 的主题和数量配额选题。
2. 返回题目必须属于 `科目A`。
3. 候选题应与关键词、标签或 syllabus area 有明确匹配关系。
4. 当某个主题题量不足时，Runtime 应明确返回不足信息，而不是静默返回无关题。
5. consumer 不需要 Admin API token，不读取 SQLite，不直接访问图片缓存目录。

## 必须支持的 Runtime 接口能力

### 1. 修复 `/questions/candidates/search` 的关键词过滤

当前接口签名可以保留，但必须让 `keywords` 生效。

请求：

```json
{
  "keywords": ["トランザクション", "ロック"],
  "examPart": "科目A",
  "limit": 10
}
```

期望行为：

- 只返回 `examPart = 科目A` 的题。
- 优先返回题干、解释、标签、分类中命中关键词的题。
- 不应在没有命中的情况下返回默认顺序题。
- 如果没有足够结果，应返回已匹配数量和不足原因。

建议响应：

```json
{
  "questions": [
    {
      "url": "https://www.fe-siken.com/kakomon/06_haru/a7.html",
      "examPart": "科目A",
      "matchedKeywords": ["トランザクション"],
      "topicTags": ["database", "transaction", "atomicity"],
      "syllabusArea": "Database",
      "score": 0.94
    }
  ],
  "totalMatched": 1,
  "shortage": {
    "requested": 10,
    "returned": 1,
    "reason": "not_enough_topic_matches"
  }
}
```

### 2. 增加结构化主题字段

候选题与详情接口都应返回可用于筛选和展示的结构化字段。

建议字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `topicTags` | `string[]` | 题目主题标签，例如 `transaction`, `lock`, `sql`, `security` |
| `syllabusArea` | `string` | 大纲领域，例如 `Database`, `Security`, `Network` |
| `knowledgePoint` | `string` | 更细的知识点，例如 `ACID atomicity` |
| `matchedKeywords` | `string[]` | 本次搜索命中的关键词 |
| `score` | `number` | 相关性分数，范围建议 `0.0 - 1.0` |

### 3. 支持主题精确过滤

建议新增或扩展接口，支持按标签或 syllabus area 精确筛选。

可选方案 A：扩展现有 search 接口

```json
{
  "examPart": "科目A",
  "topicTags": ["transaction", "lock"],
  "syllabusArea": "Database",
  "limit": 10
}
```

可选方案 B：新增专用接口

```http
GET /questions/topics
GET /questions/candidates/by-topic?examPart=科目A&topicTag=transaction&limit=10
```

`GET /questions/topics` 用于让 consumer 发现可用主题标签，避免 consumer 猜测标签名称。

### 4. 明确不足和 fallback 语义

Runtime 不应在主题不足时静默返回无关题。建议支持以下语义：

```json
{
  "questions": [],
  "totalMatched": 0,
  "shortage": {
    "requested": 4,
    "returned": 0,
    "missingKeywords": ["lock"],
    "reason": "no_topic_matches"
  }
}
```

如果 Runtime 支持 fallback，应显式标记：

```json
{
  "fallbackUsed": true,
  "fallbackReason": "not_enough_topic_matches",
  "questions": []
}
```

FE Daily Runner 可以据此选择：

- 阻止发布并提示题库题量不足。
- 降级为混合复习题，并在页面中标注。
- 请求用户调整学习主题。

## 验收标准

### Runtime 行为验收

以下请求不得返回完全相同的默认候选列表：

```json
{"keywords": ["Transaction"], "examPart": "科目A", "limit": 5}
{"keywords": ["トランザクション"], "examPart": "科目A", "limit": 5}
{"keywords": ["lock"], "examPart": "科目A", "limit": 5}
{"keywords": ["SQL"], "examPart": "科目A", "limit": 5}
```

每个响应至少满足一项：

- 返回题目的 `matchedKeywords` 包含请求关键词。
- 返回题目的 `topicTags` 或 `syllabusArea` 与请求主题匹配。
- 明确返回 `shortage`，并且不返回无关默认题。

### FE Daily Runner 集成验收

以如下计划为例：

```text
main_theme: トランザクション / ロック
practice_focus: Transaction 4, lock/recovery 3, SQL 2, security 1
```

生成页面中的 10 道题应满足：

- 4 道左右与 transaction 相关。
- 3 道左右与 lock/recovery 相关。
- 2 道左右与 SQL 相关。
- 1 道左右与 security 相关。
- 每道题的 `Tested point` 不应由模型随意编造，应来自 Runtime 的结构化字段或明确的 consumer 映射。

## 建议测试用例

### Contract test: keywords must affect candidates

1. 调用 `/questions/candidates/search`，关键词为 `Transaction`。
2. 调用同一接口，关键词为 `SQL`。
3. 断言两个结果集不应完全相同。
4. 断言每个结果包含 `matchedKeywords`、`topicTags` 或 `shortage`。

### Contract test: no silent default fallback

1. 使用不存在的关键词，例如 `__NO_SUCH_FE_TOPIC__`。
2. 断言返回 `questions` 为空或显式 `fallbackUsed = true`。
3. 断言不得返回 `07_haru/a1.html` 这种默认顺序候选。

### Contract test: examPart filtering

1. 请求 `examPart = 科目A`。
2. 断言所有候选题均为 `科目A`。
3. 响应中不得混入 `科目B` 或其它题型。

### Contract test: details include topic metadata

1. 通过 `/questions/details/batch` 获取候选题详情。
2. 断言详情包含 `topicTags`、`syllabusArea` 或 `knowledgePoint`。
3. 断言图片仍使用 `publicPath`，不暴露本地文件路径或 Docker 内部 URL。

## 非目标

本次题库服务调整不要求：

- consumer 访问 Admin API。
- consumer 读取 SQLite。
- consumer 挂载题库图片目录。
- OpenAI 根据题干自行判断题目主题后再筛题。
- FE Daily Runner 在题库结果不可靠时继续静默发布无关题。

## 风险

如果 Runtime 只做全文关键词搜索，而没有结构化标签，可能出现以下风险：

- 日英关键词不一致导致漏检，例如 `Transaction` 与 `トランザクション`。
- 解释文本命中关键词但题目主题并不相关。
- 同一题属于多个主题时无法稳定配额。

因此建议 Runtime 在导入题库时生成并持久化结构化主题标签。

## Consumer 当前状态

FE Daily Runner 已完成以下 consumer 侧修复：

- 按 `practice_focus` 拆分主题配额。
- 使用 `examPart = 科目A` 请求 Runtime。
- 按主题候选组配额选题。
- 页面中每个错误选项解释已改为模型生成的独立说明。
- 校验层拒绝缺失或重复的错误选项解释。

剩余 blocker 在题库 Runtime：现有 documented search 接口无法证明按主题返回候选题。
