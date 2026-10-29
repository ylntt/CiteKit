# CiteKit

面向小团队的文档问答工具：把文档丢进 `docs/`，一条命令建索引，提问时答案带**原文出处**；资料里没有答案时回答"不知道"，而不是编造。

> 状态：**v0.2 可用**（增量索引）+ **v0.3 网页界面**。Docker 配置已提供，但作者本机未装 Docker，**尚未验证**。后续阶段见 [ROADMAP.md](ROADMAP.md)

## 特性

- **增量索引**：按 `size + mtime + sha256` 判断文件是否变更，只对变更/新增文件重新向量化，删除的文件自动清理；**无变更时再跑为 0 次 embedding 调用**，用缓存向量直接重建索引
- **答案带出处**：结构化输出 `{answer, sources}`，出处精确到文件名（不泄漏绝对路径）
- **拒答**：资料里没有就回答"不知道"，不编造
- **两种用法**：命令行 `ask.py`，或网页界面（Streamlit）
- **可评测**：自带 12 条用例（`eval/qa_seed.jsonl`，含 2 条应拒答）+ 评测脚本 `src/eval.py`

## 三步上手

1. **装依赖**：`pip install -r requirements.txt`
2. **配密钥**：`cp .env.example .env`（Windows：`Copy-Item .env.example .env`），填入自己的 `DEEPSEEK_API_KEY` 与 `DASHSCOPE_API_KEY`
3. **放文档，然后用起来**：

   ```bash
   # 把 .md / .txt 丢进 docs/ 之后：
   python src/ingest.py                        # 扫描 docs/ 建/更新索引（落盘到 .index/）
   python src/ask.py "口径变更要怎么走流程？"     # 提问，答案带来源文件名
   ```

   资料里没有答案时它会回答"不知道"；`ask.py` 只读索引，所以提问不会重新向量化。

## 网页界面（v0.3）

```bash
streamlit run src/app.py        # 打开 http://localhost:8501
```

左侧栏显示索引状态（文档数、块数、模型与切块参数），可调检索块数 `k`；重建索引后在侧边栏点"清除缓存"。

## 评测（v0.5）

```bash
python src/eval.py        # 默认 k=4
python src/eval.py 2      # 指定 k，用来对比不同 k 的效果
```

输出检索命中率（Recall@k）、答案正确率、拒答正确率与平均耗时。用例格式见 `eval/README.md`。

## Docker（v0.3，未验证）

```bash
docker compose up --build     # 需要 Docker Desktop 或 WSL2
```

配置见 `Dockerfile` 与 `docker-compose.yml`：镜像基于 `python:3.11-slim`，`docs/` 与 `.index/` 通过卷挂载，密钥由 `.env` 注入。**作者本机无 Docker，此路径未经实机验证。**

## 目录结构

```
CiteKit/
  docs/                # 你的文档（唯一需要你操作的地方）
  .index/              # 索引产物（不进 git）：index.faiss / index.pkl / vectors.json
  src/
    kb.py              # 公共能力：扫描/切块/向量化/索引仓库/FAISS/提问链
    ingest.py          # 入口：建或更新索引（增量）
    ask.py             # 入口：提问（只读索引）
    eval.py            # 评测脚本
    app.py             # Streamlit 网页界面
  eval/
    qa_seed.jsonl      # 12 条评测用例
    README.md
  dev-notes/           # 设计与实测记录
  ROADMAP.md           # 分阶段计划
  Dockerfile / docker-compose.yml
  .env.example         # 需要的环境变量（真 key 放 .env，不进 git）
```

## 环境

- Python 3.8+（当前开发环境 3.8.9；Docker 镜像用 3.11）
- 对话模型：DeepSeek `deepseek-chat`（OpenAI 兼容）
- 向量化：阿里百炼 DashScope `text-embedding-v3`
- 向量库：FAISS（faiss-cpu 1.8.0，本地文件，无需服务）

## 已知限制

- 只支持 `.md` / `.txt`；PDF / Word / Excel 在 v0.4 计划中
- 10 页规模下墙钟时间主要被 Python 启动与依赖导入占据，增量索引的收益体现在调用次数与费用上
- 单机单用户，未处理并发
- 向量以 JSON 文本缓存（约 20KB/块），规模大时应换成二进制格式

## 许可

待定。