# 使用说明

本项目需要用到嵌入模型和向量数据库。

## 1. 启动本地嵌入模型服务

### Linux/MacOS用户

- 1.1 使用前需要添加环境变量。

```sh
export OLLAMA_MODELS="embeddings/.ollama/models"
export OLLAMA_CACHE="embeddings/.ollama/cache"
```

- 1.2 关闭代理，防止影响本地模型的使用。

```sh
export NO_PROXY=127.0.1.1,localhost

```

- 1.3 启动 Ollama 服务

```sh
ollama serve
```

### Windows用户

```powershell
./scripts/start_ollama.ps1
```

## 2. 安装pixi（一个环境管理工具）

目录 tools/ 下有安装脚本。

## 3. 启动程序

cd 到项目根目录，执行以下命令：

```sh
# 环境准备
pixi install

# 运行程序
pixi run main

# 使用notebook
pixi run notebook
```

# 数据组织说明

```text
data/canonical_perspectives: 目录下存放标准观点数据
data/user_feedbacks: 目录下存放用户反馈数据
data/processed: 目录下存放处理后加入向量库的数据
```
