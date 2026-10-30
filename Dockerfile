# CiteKit 容器镜像（v0.3）
# 用 Python 3.11：解掉 3.8 的语法限制（list[str]）与 langgraph 装不上的问题。
FROM python:3.11-slim

WORKDIR /app

# pip 源可通过构建参数覆盖：docker compose build --build-arg PIP_INDEX_URL=...
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 先只拷依赖清单再安装，利用镜像层缓存：依赖没变就不重装
COPY requirements.txt .
RUN pip install --no-cache-dir -i "$PIP_INDEX_URL" -r requirements.txt

COPY src/ ./src/
COPY docs/ ./docs/
COPY eval/ ./eval/

# .index 由容器运行时生成/挂载；docs 建议挂载，方便换文档
VOLUME ["/app/.index", "/app/docs"]

ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]