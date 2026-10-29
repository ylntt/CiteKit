# v0.3：给非技术成员用的容器镜像
# 说明：作者本机未安装 Docker，此文件未经过本机构建验证。
# 用 Python 3.11 而不是 3.8：解掉 3.8 的语法限制（list[str]）与 langgraph 装不上的问题。
FROM python:3.11-slim

WORKDIR /app

# 先只拷依赖清单再安装，利用镜像层缓存：依赖没变就不重装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY docs/ ./docs/
COPY eval/ ./eval/

# .index 由容器运行时生成/挂载；docs 建议挂载，方便换文档
VOLUME ["/app/.index", "/app/docs"]

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]