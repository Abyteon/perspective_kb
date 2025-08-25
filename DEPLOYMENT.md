# 视角知识库系统 - 部署指南

## 🐳 Docker部署（推荐）

### Windows环境部署

#### 前置要求

1. **安装Docker Desktop**
   - 下载地址: https://www.docker.com/products/docker-desktop/
   - 确保启用WSL2后端（推荐）
   - 分配足够的内存（建议8GB+）

2. **系统要求**
   - Windows 10/11 (64位)
   - 至少8GB RAM
   - 至少20GB可用磁盘空间

#### 快速部署

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd perspective_kb
   ```

2. **使用自动化脚本**
   ```bash
   # 批处理脚本（推荐）
   scripts\start-windows.bat
   
   # 或PowerShell脚本
   scripts\start-windows.ps1
   ```

3. **手动部署**
   ```bash
   # 开发环境（推荐首次使用）
   docker-compose -f docker-compose.dev.yml up -d
   
   # 生产环境
   docker-compose -f docker-compose.windows.yml up -d
   ```

#### 验证部署

1. **检查服务状态**
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. **查看日志**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

3. **访问服务**
   - 应用: http://localhost:8000
   - Ollama: http://localhost:11434
   - Milvus: http://localhost:19530

### Linux/macOS环境部署

#### 前置要求

1. **安装Docker**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   
   # CentOS/RHEL
   sudo yum install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **安装Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

#### 部署步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd perspective_kb
   ```

2. **启动服务**
   ```bash
   # 开发环境
   docker-compose -f docker-compose.dev.yml up -d
   
   # 生产环境
   docker-compose -f docker-compose.windows.yml up -d
   ```

## 🔧 本地安装部署

### 环境准备

1. **Python环境**
   ```bash
   # 安装Python 3.11+
   python --version
   
   # 创建虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动Ollama服务**
   ```bash
   # 安装Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # 启动服务
   ollama serve
   
   # 拉取模型
   ollama pull mitoza/Qwen3-Embedding-0.6B:latest
   ```

### 配置系统

1. **环境配置**
   ```bash
   cp env.example .env
   # 编辑.env文件，根据需要调整配置
   ```

2. **数据准备**
   ```bash
   # 确保数据目录存在
   mkdir -p data/processed
   mkdir -p log
   ```

### 运行系统

```bash
# 使用CLI工具
python -m perspective_kb.cli process

# 或直接运行
python -m src.main
```

## 📊 服务管理

### Docker服务管理

```bash
# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f [service_name]

# 重启服务
docker-compose -f docker-compose.dev.yml restart [service_name]

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 清理数据
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
```

### 性能调优

1. **Docker资源分配**
   - 内存: 8GB+
   - CPU: 4核+
   - 磁盘: 20GB+

2. **应用配置优化**
   ```bash
   # 调整批处理大小
   export BATCH_SIZE=200
   
   # 调整工作线程数
   export MAX_WORKERS=8
   
   # 调整向量维度
   export VECTOR_DIM=1024
   ```

## 🔍 故障排除

### 常见问题

1. **Docker服务启动失败**
   ```bash
   # 检查Docker状态
   docker info
   
   # 重启Docker服务
   sudo systemctl restart docker
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :19530
   
   # 修改docker-compose.yml中的端口映射
   ```

3. **内存不足**
   ```bash
   # 检查系统内存
   free -h
   
   # 增加Docker内存限制
   # 在Docker Desktop设置中调整
   ```

4. **模型下载失败**
   ```bash
   # 手动拉取模型
   curl -X POST http://localhost:11434/api/pull \
     -d '{"name":"mitoza/Qwen3-Embedding-0.6B:latest"}'
   ```

### 日志分析

```bash
# 查看应用日志
docker-compose -f docker-compose.dev.yml logs perspective-kb-dev

# 查看Ollama日志
docker-compose -f docker-compose.dev.yml logs ollama

# 查看Milvus日志
docker-compose -f docker-compose.dev.yml logs milvus-lite
```

## 🔒 安全配置

### 生产环境安全

1. **网络安全**
   ```bash
   # 使用自定义网络
   docker network create perspective-kb-network
   
   # 限制端口暴露
   # 只暴露必要的端口
   ```

2. **数据安全**
   ```bash
   # 数据加密
   # 使用加密卷
   docker volume create --opt type=none --opt o=bind --opt device=/secure/path encrypted-data
   ```

3. **访问控制**
   ```bash
   # 设置访问密钥
   export MINIO_ACCESS_KEY=your-access-key
   export MINIO_SECRET_KEY=your-secret-key
   ```

## 📈 监控和维护

### 系统监控

1. **资源监控**
   ```bash
   # 查看容器资源使用
   docker stats
   
   # 查看磁盘使用
   df -h
   ```

2. **应用监控**
   ```bash
   # 健康检查
   curl http://localhost:9091/healthz
   
   # 性能指标
   curl http://localhost:9091/metrics
   ```

### 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/ volumes/

# 备份数据库
docker exec milvus-standalone milvus backup --collection=knowledge
```

## 🚀 扩展部署

### 集群部署

1. **多节点部署**
   ```bash
   # 使用Docker Swarm
   docker swarm init
   docker stack deploy -c docker-compose.swarm.yml perspective-kb
   ```

2. **负载均衡**
   ```bash
   # 使用Nginx反向代理
   docker-compose -f docker-compose.prod.yml up -d
   ```

### 云平台部署

1. **AWS部署**
   ```bash
   # 使用ECS
   aws ecs create-cluster --cluster-name perspective-kb
   ```

2. **Azure部署**
   ```bash
   # 使用Azure Container Instances
   az container create --resource-group myResourceGroup --name perspective-kb
   ```

## 📞 技术支持

如果遇到部署问题，请：

1. 查看日志文件
2. 检查系统资源
3. 验证网络连接
4. 提交Issue到GitHub

---

更多详细信息请参考 [README.md](README.md)
