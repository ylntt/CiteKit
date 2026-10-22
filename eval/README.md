# eval/ — 评测集

`qa_seed.jsonl` 每行一个用例，字段：

| 字段 | 含义 |
|---|---|
| `id` | 编号 |
| `question` | 要问的问题 |
| `expect_source` | 期望命中的文档（相对 `docs/`） |
| `expect_contains` | 答案里应出现的关键词 |
| `expect_refuse` | `true` 表示资料里没有，应回答"不知道" |

## v0.1 起就能用

拿这些问题手动问一遍，检查答案对不对、出处标得对不对。

## v0.5 用它算指标

- **Recall@k**：`expect_source` 是否出现在检索结果里
- **答案命中率**：`expect_contains` 的关键词命中比例
- **拒答率**：`expect_refuse` 的题是否正确拒答（资料里没有就别说）
- **平均耗时**：每条问题的端到端时间

改切块大小 / k / prompt 之后，指标是升是降就有了依据。
