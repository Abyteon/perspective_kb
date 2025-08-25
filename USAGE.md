# 视角知识库系统 - 使用指南

## 🎯 概述

视角知识库系统现在支持两种运行模式：
- **本地模式**: 使用Milvus Lite进行本地向量存储
- **服务器模式**: 使用Milvus服务器进行分布式向量存储

## 🚀 快速开始

### 1. 本地模式（推荐开发使用）

#### 环境配置
```bash
# 复制环境配置
cp env.example .env

# 编辑配置（保持默认即可）
# MILVUS_USE_SERVER=false
# DB_PATH=milvus_lite.db
```

#### 启动服务
```bash
# 使用Docker（推荐）
scripts/start-windows.bat
# 选择选项2: 开发环境 - 本地模式

# 或手动启动
docker-compose -f docker-compose.dev.yml up -d perspective-kb-dev-local ollama
```

#### 验证服务
```bash
# 检查服务状态
python -m perspective_kb.cli status

# 查看配置
python -m perspective_kb.cli config
```

### 2. 服务器模式（推荐生产使用）

#### 环境配置
```bash
# 编辑.env文件
MILVUS_USE_SERVER=true
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

#### 启动服务
```bash
# 使用Docker
scripts/start-windows.bat
# 选择选项1: 生产环境

# 或手动启动
docker-compose -f docker-compose.windows.yml up -d
```

## 📊 数据处理

### 处理知识库和反馈数据

```bash
# 处理所有数据
python -m perspective_kb.cli process

# 强制重新处理
python -m perspective_kb.cli process --force

# 自定义批处理大小
python -m perspective_kb.cli process --batch-size 200 --max-workers 8
```

### 查看处理结果

```bash
# 查看集合统计
python -m perspective_kb.cli collections

# 查看系统状态
python -m perspective_kb.cli status
```

## 🔍 搜索功能

### 搜索知识库

```bash
# 搜索知识库
python -m perspective_kb.cli search "价格偏高" --collection knowledge

# 搜索反馈
python -m perspective_kb.cli search "这车太贵了" --collection feedback

# 自定义返回结果数量
python -m perspective_kb.cli search "质量问题" --collection knowledge --top-k 10
```

### 编程接口搜索

```python
from perspective_kb import get_vector_db, DataHelper

# 创建数据库连接
with get_vector_db() as db:
    # 创建数据处理助手
    helper = DataHelper()
    
    # 向量化查询文本
    query_text = "价格偏高"
    embedding = helper.embed_text(query_text)
    
    # 搜索
    results = db.search("knowledge", [embedding], top_k=5)
    
    # 处理结果
    for id_, score, metadata in results[0]:
        print(f"ID: {id_}, 相似度: {score:.3f}")
        print(f"观点: {metadata.get('insight', 'N/A')}")
        print(f"维度: {metadata.get('aspect', 'N/A')}")
        print()
```

## 🛠️ 管理功能

### 集合管理

```bash
# 列出所有集合
python -m perspective_kb.cli collections

# 删除集合（危险操作）
python -m perspective_kb.cli clean knowledge --confirm

# 查看集合详细信息
python -m perspective_kb.cli status
```

### 配置管理

```bash
# 查看当前配置
python -m perspective_kb.cli config

# 修改配置（编辑.env文件）
# MILVUS_USE_SERVER=true  # 切换到服务器模式
# MILVUS_HOST=your-milvus-server
# MILVUS_PORT=19530
```

## 🔧 高级配置

### 环境变量配置

```bash
# 数据库配置
DB_PATH=milvus_lite.db                    # 本地模式数据库路径
MILVUS_USE_SERVER=false                   # 是否使用服务器模式
MILVUS_HOST=localhost                     # Milvus服务器地址
MILVUS_PORT=19530                         # Milvus服务器端口

# Ollama配置
OLLAMA_HOST=http://localhost:11434        # Ollama服务地址
EMBEDDING_MODEL=mitoza/Qwen3-Embedding-0.6B:latest  # 嵌入模型

# 性能配置
VECTOR_DIM=1024                           # 向量维度
BATCH_SIZE=100                            # 批处理大小
MAX_WORKERS=4                             # 最大工作线程数
```

### 性能调优

```bash
# 增加批处理大小（适合大数据量）
export BATCH_SIZE=500

# 增加工作线程数（适合多核CPU）
export MAX_WORKERS=8

# 使用IVF索引（适合大规模数据）
export USE_FLAT_INDEX=false
```

## 🐳 Docker使用

### 开发环境

```bash
# 本地模式
docker-compose -f docker-compose.dev.yml up -d perspective-kb-dev-local ollama

# 服务器模式
docker-compose -f docker-compose.dev.yml up -d perspective-kb-dev-server milvus-lite ollama
```

### 生产环境

```bash
# 完整生产环境
docker-compose -f docker-compose.windows.yml up -d

# 查看服务状态
docker-compose -f docker-compose.windows.yml ps

# 查看日志
docker-compose -f docker-compose.windows.yml logs -f
```

## 🔍 故障排除

### 常见问题

1. **向量数据库连接失败**
   ```bash
   # 检查服务状态
   python -m perspective_kb.cli status
   
   # 检查配置
   python -m perspective_kb.cli config
   ```

2. **Ollama服务不可用**
   ```bash
   # 检查Ollama服务
   curl http://localhost:11434/api/tags
   
   # 拉取模型
   curl -X POST http://localhost:11434/api/pull \
     -d '{"name":"mitoza/Qwen3-Embedding-0.6B:latest"}'
   ```

3. **数据加载失败**
   ```bash
   # 检查数据目录
   ls -la data/canonical_perspectives/
   ls -la data/user_feedbacks/
   
   # 检查JSON格式
   python -c "import json; json.load(open('data/canonical_perspectives/价格.json'))"
   ```

### 日志查看

```bash
# 查看应用日志
tail -f log/perspective_kb.log

# 查看Docker日志
docker-compose -f docker-compose.dev.yml logs -f perspective-kb-dev-local

# 查看Ollama日志
docker logs -f ollama-dev
```

## 📈 性能监控

### 系统监控

```bash
# 查看Docker资源使用
docker stats

# 查看集合统计
python -m perspective_kb.cli collections

# 查看处理统计
python -m perspective_kb.cli status
```

### 性能指标

- **向量化速度**: 每秒处理的文本数量
- **搜索延迟**: 查询响应时间
- **内存使用**: 向量数据库内存占用
- **存储空间**: 向量数据磁盘占用

## 🔄 数据迁移

### 本地模式到服务器模式

```bash
# 1. 备份本地数据
cp milvus_lite.db milvus_lite_backup.db

# 2. 修改配置
# MILVUS_USE_SERVER=true
# MILVUS_HOST=your-server

# 3. 重新处理数据
python -m perspective_kb.cli process --force
```

### 服务器模式到本地模式

```bash
# 1. 修改配置
# MILVUS_USE_SERVER=false

# 2. 重新处理数据
python -m perspective_kb.cli process --force
```

## 📚 最佳实践

1. **开发阶段**: 使用本地模式，快速迭代
2. **测试阶段**: 使用服务器模式，模拟生产环境
3. **生产阶段**: 使用完整的Milvus集群
4. **数据备份**: 定期备份向量数据库文件
5. **性能监控**: 监控系统资源使用情况
6. **日志管理**: 配置合适的日志级别和轮转策略

---

更多详细信息请参考 [README.md](README.md) 和 [DEPLOYMENT.md](DEPLOYMENT.md)
