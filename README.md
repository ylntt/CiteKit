# team-kb

面向小团队的文档问答工具：把文档丢进 `docs/`，一句命令建索引，提问时答案带**原文出处**。

> 状态：**v0.1 开发中**（仓库骨架已就绪，代码按阶段逐步补齐，见 [ROADMAP.md](ROADMAP.md)）

## 三步上手（v0.1 完成后可用）

1. **装依赖**：`pip install -r requirements.txt`
2. **放文档**：把 `.md` / `.txt` 丢进 `docs/`
3. **建索引 + 提问**：
   ```
   python src/ingest.py          # 扫描 docs/ 建索引（落盘到 .index/）
   python src/ask.py "最小权限是什么"
   ```

## 目录结构

```
team-kb/
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
