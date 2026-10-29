# ROADMAP — CiteKit

> 目标：把本地向量检索脚本做成一个可上传 GitHub、可供约 6 人使用的文档问答工具。
> **每阶段的完成标准都一样：能跑通 + 你能讲清楚为什么这么设计。** 讲不清楚 = 没做完。

## 项目定位

把文档丢进 `docs/` → 一条命令建/更新索引 → 提问，答案带**原文出处**。

关键差异点（简历上能讲的三个）：**增量索引**、**答案带出处**、**指标化评测**。

## 阶段

| 阶段 | 做什么（验收标准） | 要学的知识 |
|---|---|---|
| **v0.1** 骨架能跑 | `ingest` / `ask` 两条 CLI 命令 + 索引落盘。验收：换台机器 clone → 放文档 → 两条命令出带出处的答案 | venv/requirements、`argparse`、FAISS `save_local`/`load_local`、`pathlib`、logging |
| **v0.2** 增量与健壮 | manifest（mtime+hash）只重嵌入变更文件；删改处理；进度条；失败重试；`--top-k` ~ `--chunk-size` 参数 | `hashlib`、清单设计、`tqdm`、重试、配置管理 |
| **v0.3** 给 6 人用 | Dockerfile + compose（卷挂 `docs/` 与 `.index/`）+ Streamlit 页面（上传/提问/看出处）。验收：`docker compose up` 一条命令，浏览器可用 | Docker（镜像/卷/环境变量/compose）、Streamlit 或 FastAPI（选一个） |
| **v0.4** 多格式 + 检索质量 | PDF/Word/Excel/Markdown 解析；两种切块策略对比；可选 rerank 或 BM25 混合检索 | `pypdf`/`python-docx`/`openpyxl`、切块策略、rerank 与 BM25 概念 |
| **v0.5** 评测（最能打） | 20–30 条 QA 集 + 脚本输出 Recall@k / 拒答率 / 耗时；改配置看得出变好变坏 | 检索评测指标、`pytest` |
| **v0.6** 工程化收尾 | GitHub Actions（测试 + lint）、Release、耗时统计、完整 README、Demo GIF | GitHub Actions、`ruff`、写 README |

## 面试会被问到的五个问题（决定你往哪深挖）

1. 切块大小和 `k` 是怎么定的？依据是什么？
2. 文件更新了，怎么知道要重建哪部分？
3. 怎么知道你的改动让效果变好了？
4. 答案里的"出处"是怎么产生的？能回到原文吗？
5. 为什么用链式 RAG 而不是 Agent？

## 注意

- 文档规模约 10 页：加分点靠「多格式 + 评测 + 增量 + 部署」，不要编造大数据量性能故事。
- 真实内部资料与公司 key 一律不进仓库；示例文档是脱敏的。
- 一次只推一个阶段。
