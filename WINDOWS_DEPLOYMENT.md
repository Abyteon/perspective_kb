# 视角知识库系统 - Windows部署指南

## 🪟 Windows环境快速部署

### 系统要求

- **操作系统**: Windows 10/11 (64位)
- **内存**: 最少8GB RAM (推荐16GB+)
- **磁盘空间**: 至少20GB可用空间
- **网络**: 稳定的互联网连接

### 前置条件

#### 1. 安装Docker Desktop

1. **下载Docker Desktop for Windows**
   - 访问: https://www.docker.com/products/docker-desktop/
   - 下载适合Windows的版本

2. **安装配置**
   ```cmd
   # 运行安装程序，按照提示完成安装
   # 重启计算机
   ```

3. **启用WSL2后端**（推荐）
   ```powershell
   # 在PowerShell管理员模式下运行
   wsl --install
   wsl --set-default-version 2
   ```

4. **配置Docker资源**
   - 打开Docker Desktop
   - Settings → Resources → Advanced
   - 内存: 8GB+ (推荐12GB)
   - CPU: 4核+ (推荐6核)
   - 磁盘: 60GB+

#### 2. 验证安装

```cmd
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version

# 测试Docker运行
docker run hello-world
```

### 快速部署

#### 方法1: 使用批处理脚本（推荐）

1. **下载项目**
   ```cmd
   git clone <repository-url>
   cd perspective_kb
   ```

2. **运行启动脚本**
   ```cmd
   # 双击运行或在命令行执行
   scripts\docker-start.bat

   # 或选择特定模式
   scripts\docker-start.bat simple    # 简化模式（推荐）
   scripts\docker-start.bat dev       # 开发模式
   scripts\docker-start.bat prod      # 生产模式
   ```

#### 方法2: 使用PowerShell脚本

1. **以管理员身份运行PowerShell**
   ```powershell
   # 设置执行策略（如果需要）
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

   # 运行启动脚本
   .\scripts\docker-start.ps1

   # 或选择特定模式
   .\scripts\docker-start.ps1 simple    # 简化模式（推荐）
   .\scripts\docker-start.ps1 dev       # 开发模式
   .\scripts\docker-start.ps1 prod      # 生产模式
   ```

#### 方法3: 手动部署

1. **创建必要目录**
   ```cmd
   mkdir volumes\ollama
   mkdir volumes\app_data
   mkdir log
   ```

2. **复制环境配置**
   ```cmd
   copy env.example .env
   ```

3. **启动服务**
   ```cmd
   # 简化模式（推荐新手）
   docker-compose -f docker-compose.simple.yml up -d

   # 生产模式（完整功能）
   docker-compose -f docker-compose.windows.yml up -d
   ```

### 配置说明

#### 简化模式 vs 生产模式

| 特性 | 简化模式 | 生产模式 |
|------|----------|----------|
| 数据库 | Milvus Lite | Milvus Server + etcd + MinIO |
| 内存需求 | 4GB+ | 8GB+ |
| 启动时间 | 2-3分钟 | 5-8分钟 |
| 功能完整性 | 基本功能 | 完整功能 |
| 适用场景 | 开发测试 | 生产环境 |

#### 环境变量配置

编辑 `.env` 文件来自定义配置：

```env
# 数据库配置
PKB_MILVUS_USE_SERVER=false              # false=Lite模式, true=Server模式
PKB_DB_PATH=./milvus_lite.db              # Lite模式数据库路径

# Ollama配置
PKB_OLLAMA_HOST=http://localhost:11434    # Ollama服务地址
PKB_EMBEDDING_MODEL=mitoza/Qwen3-Embedding-0.6B:latest

# 性能配置
PKB_BATCH_SIZE=50                         # 批处理大小
PKB_MAX_WORKERS=2                         # 并发工作线程数
PKB_VECTOR_DIM=1024                       # 向量维度

# 日志配置
PKB_LOG_LEVEL=INFO                        # 日志级别
PKB_LOG_FORMAT=json                       # 日志格式
```

### 验证部署

#### 1. 检查服务状态

```cmd
# 查看运行中的容器
docker ps

# 查看服务状态
docker-compose -f docker-compose.simple.yml ps
```

#### 2. 访问服务

- **应用服务**: http://localhost:8000
- **Ollama API**: http://localhost:11434
- **Milvus管理** (生产模式): http://localhost:9091

#### 3. 测试功能

```cmd
# 进入应用容器
docker exec -it perspective-kb-app bash

# 运行测试命令
python -m perspective_kb.cli status
python -m perspective_kb.cli search "价格便宜" --top-k 3
```

### 日常管理

#### 启动/停止服务

```cmd
# 启动服务
scripts\docker-start.bat

# 停止服务
scripts\docker-start.bat stop

# 查看日志
scripts\docker-start.bat logs

# 清理数据（谨慎使用）
scripts\docker-start.bat clean
```

#### 更新系统

```cmd
# 停止当前服务
docker-compose down

# 拉取最新镜像
docker-compose pull

# 重新构建和启动
docker-compose up --build -d
```

#### 数据备份

```cmd
# 备份数据目录
xcopy /E /I data backup\data_%date:~0,4%%date:~5,2%%date:~8,2%
xcopy /E /I volumes backup\volumes_%date:~0,4%%date:~5,2%%date:~8,2%

# 备份数据库（生产模式）
docker exec perspective-kb-app python -m perspective_kb.cli export --output backup\data.json
```

### 故障排除

#### 常见问题

1. **Docker Desktop启动失败**
   ```cmd
   # 重置Docker Desktop
   # 打开Docker Desktop → Troubleshoot → Reset to factory defaults
   
   # 重启Windows Docker服务
   net stop com.docker.service
   net start com.docker.service
   ```

2. **端口冲突**
   ```cmd
   # 查看端口占用
   netstat -ano | findstr :8000
   netstat -ano | findstr :11434
   netstat -ano | findstr :19530
   
   # 修改docker-compose.yml中的端口映射
   # 例如: "8001:8000" 改为使用8001端口
   ```

3. **内存不足**
   ```cmd
   # 检查系统内存
   wmic computersystem get TotalPhysicalMemory
   
   # 增加Docker Desktop内存分配
   # Docker Desktop → Settings → Resources → Advanced
   ```

4. **模型下载失败**
   ```cmd
   # 手动下载模型
   curl -X POST http://localhost:11434/api/pull -d "{\"name\":\"mitoza/Qwen3-Embedding-0.6B:latest\"}"
   
   # 或设置代理
   set HTTP_PROXY=http://proxy:port
   set HTTPS_PROXY=http://proxy:port
   ```

5. **防火墙问题**
   ```cmd
   # 检查Windows防火墙设置
   # 允许Docker Desktop通过防火墙
   # 控制面板 → 系统和安全 → Windows Defender防火墙 → 允许应用通过防火墙
   ```

#### 日志查看

```cmd
# 查看所有服务日志
docker-compose -f docker-compose.simple.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.simple.yml logs perspective-kb
docker-compose -f docker-compose.simple.yml logs ollama

# 实时跟踪日志
docker-compose -f docker-compose.simple.yml logs -f
```

#### 性能优化

1. **Windows特定优化**
   ```cmd
   # 禁用Windows Search索引（可选）
   # 禁用Windows Update自动重启
   # 关闭不必要的后台应用
   ```

2. **Docker优化**
   ```cmd
   # 定期清理Docker资源
   docker system prune -f
   docker volume prune -f
   docker image prune -f
   ```

3. **应用优化**
   - 减少 `PKB_MAX_WORKERS` 如果CPU使用率过高
   - 调整 `PKB_BATCH_SIZE` 根据内存情况
   - 启用 `PKB_ENABLE_EMBEDDING_CACHE` 缓存

### 监控和维护

#### 系统监控

```cmd
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df

# 查看网络状态
docker network ls
```

#### 定期维护

```cmd
# 每周执行一次
scripts\docker-start.bat stop
docker system prune -f
scripts\docker-start.bat

# 每月备份一次数据
# 运行备份脚本
```

### 技术支持

如果遇到问题：

1. 查看本指南的故障排除部分
2. 检查 `log/` 目录下的日志文件
3. 运行 `docker-compose logs` 查看详细错误信息
4. 访问项目GitHub页面提交Issue

---

**重要提示**: 首次部署可能需要下载大量Docker镜像和AI模型，请确保网络连接稳定。整个过程可能需要30-60分钟，具体时间取决于网络速度。
