# 使用Python 3.12官方镜像作为基础镜像（与项目保持一致）
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY pyproject.toml .
COPY src/ ./src/
COPY data/ ./data/
COPY env.example .env

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/log /app/embeddings

# 设置权限（如果文件存在）
RUN if [ -f /app/src/perspective_kb_cli.py ]; then chmod +x /app/src/perspective_kb_cli.py; fi

# 暴露端口（如果需要Web界面）
EXPOSE 8000

# 设置默认命令
CMD ["python", "-m", "perspective_kb.cli", "status"]
