#!/bin/zsh

# 使用前需要添加环境变量。
export OLLAMA_MODELS="embeddings/.ollama/models"
export OLLAMA_CACHE="embeddings/.ollama/cache"

# 关闭代理，防止影响本地模型的使用。
export NO_PROXY=127.0.0.1,localhost

# 启动 Ollama 服务
nohup ollama serve &>"log/ollama.log" &

echo "Ollama 服务已启动，日志输出到 log/ollama.log"
