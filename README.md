# CiteKit

面向小团队的文档问答工具：把文档丢进 `docs/`，一句命令建索引，提问时答案带**原文出处**。

> 状态：**v0.1 可用** —— `ingest` 建索引、`ask` 提问（答案带原文出处）。后续阶段见 [ROADMAP.md](ROADMAP.md)

## 三步上手

1. **装依赖**：`pip install -r requirements.txt`
2. **配密钥**：`cp .env.example .env`（Windows：`Copy-Item .env.example .env`），填入自己的 `DEEPSEEK_API_KEY` 与 `DASHSCOPE_API_KEY`
3. **放文档，然后用起来**：

   ```bash
   # 把 .md / .txt 丢进 docs/ 之后：
   python src/ingest.py                        # 扫描 docs/ 建索引（落盘到 .index/）
   python src/ask.py "口径变更要怎么走流程？"     # 提问，答案带来源文件名
   ```

   资料里没有答案时它会回答"不知道"而不是编造；`ask.py` 只读索引，所以第二次提问不会重新向量化。

## 目录结构

```
CiteKit/
  docs/          # 你的文档（唯一需要你操作的地方）
  .index/        # 索引落盘（不进 git）
  src/           # kb.py 公共能力 / ingest.py 建索引 / ask.py 提问
  ROADMAP.md     # 分阶段计划
  .env.example   # 需要的环境变量（真 key 放 .env，不进 git）
```

## 环境

- Python 3.8+（当前开发环境 3.8.9）
- 对话模型：DeepSeek（OpenAI 兼容）
- 向量化：阿里百炼 DashScope `text-embedding-v3`
- 向量库：FAISS（本地文件，无需服务）

## 许可

待定。
