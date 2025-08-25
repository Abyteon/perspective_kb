# 视角知识库系统 - 快速启动指南

## 🚀 一键启动

### 方法一：使用启动脚本（推荐）

```bash
# 给脚本执行权限
chmod +x start_local.sh

# 运行启动脚本
./start_local.sh
```

### 方法二：使用pixi命令

```bash
# 激活pixi环境
pixi shell

# 查看配置
pixi run config

# 检查状态
pixi run status

# 处理数据
pixi run process

# 搜索数据
pixi run search "价格偏高" --collection knowledge
```

## 📋 前置要求

### 1. 安装pixi（如果未安装）

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### 2. 安装Ollama（如果未安装）

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 3. 启动Ollama服务

```bash
# 启动服务
ollama serve

# 拉取嵌入模型
ollama pull mitoza/Qwen3-Embedding-0.6B:latest
```

## 🔧 环境配置

### 自动配置

启动脚本会自动：
- 创建必要的目录
- 复制环境配置文件
- 检查服务状态

### 手动配置

```bash
# 复制环境配置
cp env.example .env

# 编辑配置（可选）
# nano .env
```

## 📊 使用步骤

### 1. 检查系统状态

```bash
pixi run status
```

### 2. 处理数据

```bash
pixi run process
```

### 3. 搜索数据

```bash
# 搜索知识库
pixi run search "价格偏高" --collection knowledge

# 搜索反馈
pixi run search "这车太贵了" --collection feedback
```

### 4. 查看集合信息

```bash
pixi run collections
```

## 🐛 故障排除

### 常见问题

1. **pixi未安装**
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. **Ollama服务未运行**
   ```bash
   ollama serve
   ```

3. **模型未下载**
   ```bash
   ollama pull mitoza/Qwen3-Embedding-0.6B:latest
   ```

4. **权限问题**
   ```bash
   chmod +x start_local.sh
   ```

### 检查服务状态

```bash
# 检查Ollama服务
curl http://localhost:11434/api/tags

# 检查pixi环境
pixi info
```

## 📚 更多信息

- 详细使用指南: [USAGE.md](USAGE.md)
- 部署指南: [DEPLOYMENT.md](DEPLOYMENT.md)
- 项目说明: [README.md](README.md)

## 🎯 快速测试

运行以下命令测试系统是否正常工作：

```bash
# 1. 检查配置
pixi run config

# 2. 检查状态
pixi run status

# 3. 处理数据
pixi run process

# 4. 搜索测试
pixi run search "价格" --collection knowledge
```

如果所有步骤都成功，说明系统配置正确！
