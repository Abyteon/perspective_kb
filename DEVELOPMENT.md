# 视角知识库系统 - 开发指南

## 🚀 快速开始 (本地开发)

### 推荐工作流：本地开发 + Docker生产

- **开发阶段**: 使用pixi本地环境 ⚡ (启动快，调试方便)
- **生产部署**: 使用Docker容器 🐳 (环境一致，易部署)

## 本地开发环境

### 环境要求

- **Python**: 3.12+ (通过pixi管理)
- **Ollama**: 本地安装
- **Git**: 版本控制

### 快速启动

```bash
# 一键启动开发环境
./start-local.sh

# 或者手动启动
pixi install
ollama serve &
pixi run python -m perspective_kb.cli status
```

### 开发命令

```bash
# 系统状态检查
pixi run python -m perspective_kb.cli status

# 数据处理
pixi run python -m perspective_kb.cli process --force

# 搜索测试
pixi run python -m perspective_kb.cli search "价格便宜" --top-k 3

# 集合管理
pixi run python -m perspective_kb.cli collections list
pixi run python -m perspective_kb.cli collections drop knowledge

# 配置查看
pixi run python -m perspective_kb.cli config
```

### 开发技巧

#### 1. 快速迭代
```bash
# 修改代码后直接运行，无需重启
pixi run python -m perspective_kb.cli search "新查询"

# 使用--force重新处理数据
pixi run python -m perspective_kb.cli process --force
```

#### 2. 调试模式
```bash
# 设置调试级别日志
export PKB_LOG_LEVEL=DEBUG
pixi run python -m perspective_kb.cli status

# 或在.env文件中设置
echo "PKB_LOG_LEVEL=DEBUG" >> .env
```

#### 3. 缓存管理
```bash
# 清理嵌入缓存
rm -rf embeddings/cache/

# 禁用缓存（测试时有用）
export PKB_ENABLE_EMBEDDING_CACHE=false
```

## 代码结构

```
src/perspective_kb/
├── __init__.py         # 包初始化
├── cli.py             # 命令行界面
├── config.py          # 配置管理
├── data_helper.py     # 数据处理和嵌入
├── utils.py           # 工具函数
└── vector_db.py       # 向量数据库接口
```

### 核心组件

#### 1. 配置系统 (`config.py`)
- 使用Pydantic进行配置管理
- 支持环境变量覆盖
- 自动类型验证

```python
from perspective_kb.config import settings
print(settings.ollama_host)  # http://localhost:11434
```

#### 2. 数据处理 (`data_helper.py`)
- 文本清理和预处理
- 批量向量化
- 缓存管理

```python
from perspective_kb.data_helper import DataHelper
helper = DataHelper()
embeddings = helper.generate_embeddings(["文本1", "文本2"])
```

#### 3. 向量数据库 (`vector_db.py`)
- Milvus Lite本地版本
- Milvus Server生产版本
- 统一的API接口

```python
from perspective_kb.vector_db import LocalVectorDB
db = LocalVectorDB()
results = db.search("knowledge", query_vectors)
```

## 测试指南

### 单元测试
```bash
# 运行基础测试
pixi run python tests/test_basic.py

# 系统集成测试
pixi run python test_system.py
```

### 功能测试
```bash
# 测试搜索功能
pixi run python -m perspective_kb.cli search "价格" --top-k 5

# 测试不同维度
pixi run python -m perspective_kb.cli search "空间大" --top-k 3
pixi run python -m perspective_kb.cli search "动力强" --top-k 3
```

## 生产部署

### Docker部署
```bash
# Windows环境
scripts\docker-start.bat prod

# Linux/macOS环境
scripts/docker-start.sh prod

# 手动部署
docker-compose -f docker-compose.windows.yml up -d
```

### 环境变量配置
```bash
# 生产环境配置
PKB_MILVUS_USE_SERVER=true
PKB_MILVUS_HOST=milvus-server
PKB_BATCH_SIZE=200
PKB_MAX_WORKERS=8
PKB_LOG_LEVEL=INFO
```

## 开发最佳实践

### 1. 代码规范
- 使用类型提示
- 添加文档字符串
- 遵循PEP 8规范

### 2. 错误处理
```python
try:
    result = some_operation()
except SpecificError as e:
    logger.error("操作失败", error=str(e))
    # 优雅降级或重试
```

### 3. 日志记录
```python
from perspective_kb.utils import get_logger
logger = get_logger("module_name")

logger.info("操作成功", item_count=100)
logger.warning("注意事项", field="value") 
logger.error("操作失败", error=str(e))
```

### 4. 配置管理
```python
# 优先使用配置对象
from perspective_kb.config import settings
batch_size = settings.batch_size

# 避免硬编码
# ❌ 不好
BATCH_SIZE = 50

# ✅ 好
batch_size = settings.batch_size
```

## 常见问题

### 1. Ollama连接失败
```bash
# 检查Ollama状态
curl http://localhost:11434/api/version

# 重启Ollama
pkill ollama
ollama serve &
```

### 2. 模型下载慢
```bash
# 设置代理
export HTTP_PROXY=http://proxy:port
ollama pull mitoza/Qwen3-Embedding-0.6B:latest
```

### 3. 内存不足
```bash
# 减少批处理大小
export PKB_BATCH_SIZE=10
export PKB_MAX_WORKERS=1
```

### 4. 端口冲突
```bash
# 检查端口占用
lsof -i :11434
lsof -i :8000

# 修改配置
export PKB_OLLAMA_HOST=http://localhost:11435
```

## 性能优化

### 1. 嵌入缓存
- 启用缓存：`PKB_ENABLE_EMBEDDING_CACHE=true`
- 缓存位置：`embeddings/cache/`
- 清理缓存：删除缓存目录

### 2. 并发处理
- 调整工作线程：`PKB_MAX_WORKERS=4`
- 批处理大小：`PKB_BATCH_SIZE=100`

### 3. 向量数据库
- 本地开发：Milvus Lite (快速)
- 生产环境：Milvus Server (完整功能)

## 贡献指南

1. Fork项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m "添加新功能"`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

---

**开发愉快！** 🎉

如有问题，请查看 [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md) 或 [README.md](README.md)
