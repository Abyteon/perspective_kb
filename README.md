# 视角知识库系统 (Perspective Knowledge Base)

一个基于向量数据库的视角知识库管理系统，支持知识库构建、用户反馈分析和智能匹配。

## ✨ 主要特性

- 🚀 **高性能向量数据库**: 基于 Milvus Lite 的本地向量存储
- 🤖 **智能文本嵌入**: 使用 Ollama 进行文本向量化
- 📊 **结构化数据处理**: 支持知识库和用户反馈的批量处理
- 🔍 **语义搜索**: 基于向量相似度的智能匹配
- 🛠️ **命令行工具**: 丰富的 CLI 操作界面
- 📝 **结构化日志**: 完整的操作日志和错误追踪
- ⚙️ **灵活配置**: 支持环境变量和配置文件

## 🏗️ 系统架构

```
perspective_kb/
├── src/perspective_kb/
│   ├── config.py          # 配置管理
│   ├── vector_db.py       # 向量数据库操作
│   ├── data_helper.py     # 数据处理助手
│   ├── utils.py           # 工具函数
│   ├── cli.py             # 命令行界面
│   └── __init__.py        # 包初始化
├── data/                  # 数据目录
│   ├── canonical_perspectives/  # 标准视角数据
│   ├── user_feedbacks/          # 用户反馈数据
│   └── processed/               # 处理后数据
├── log/                   # 日志目录
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Ollama 服务 (用于文本向量化)
- 足够的磁盘空间用于向量存储

### 2. 安装依赖

```bash
# 使用 pixi (推荐)
pixi install

# 或使用 pip
pip install -e .
```

### 3. 启动 Ollama 服务

```bash
# 启动 Ollama 服务
ollama serve

# 拉取嵌入模型
ollama pull mitoza/Qwen3-Embedding-0.6B:latest
```

### 4. 配置环境

复制环境配置示例文件：

```bash
cp env.example .env
# 根据需要修改 .env 文件中的配置
```

### 5. 运行系统

```bash
# 使用 CLI 工具
python -m perspective_kb.cli process

# 或直接运行主程序
python -m src.main
```

## 📖 使用方法

### 命令行工具

系统提供了丰富的命令行操作：

```bash
# 处理数据
python -m perspective_kb.cli process [--force] [--batch-size 100] [--max-workers 4]

# 查看系统状态
python -m perspective_kb.cli status

# 搜索数据
python -m perspective_kb.cli search "查询文本" [--collection knowledge] [--top-k 5]

# 查看集合信息
python -m perspective_kb.cli collections

# 清理集合
python -m perspective_kb.cli clean collection_name --confirm

# 查看配置
python -m perspective_kb.cli config
```

### 编程接口

```python
from perspective_kb import LocalVectorDB, DataHelper, settings

# 创建向量数据库连接
with LocalVectorDB() as db:
    # 创建集合
    db.create_collection("knowledge", vector_dim=1024)
    
    # 搜索向量
    results = db.search("knowledge", query_vectors, top_k=5)
    
    # 获取统计信息
    stats = db.get_collection_stats("knowledge")

# 数据处理
data_helper = DataHelper()
knowledge_data = data_helper.load_data_from_directory(
    "knowledge", 
    Path("data/canonical_perspectives"), 
    db
)
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_PATH` | `milvus_lite.db` | 向量数据库文件路径 |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `EMBEDDING_MODEL` | `mitoza/Qwen3-Embedding-0.6B:latest` | 嵌入模型名称 |
| `VECTOR_DIM` | `1024` | 向量维度 |
| `BATCH_SIZE` | `100` | 批处理大小 |
| `MAX_WORKERS` | `4` | 最大工作线程数 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 数据格式

#### 标准视角数据 (canonical_perspectives)

```json
[
  {
    "insight_id": "PRICE_001",
    "aspect": "价格",
    "insight": "价格偏高",
    "description": "用户认为价格高于预期或竞品",
    "examples": ["这车比同级别贵太多", "价格虚高，不值得"],
    "keywords": ["贵", "价格高", "虚高"],
    "sentiment": "negative",
    "status": "active"
  }
]
```

#### 用户反馈数据 (user_feedbacks)

```json
[
  {
    "fb_id": "fb_20250823_0001",
    "raw_text": "这车比同级别贵两万，不划算。",
    "summary": "投诉价格偏高，性价比不足。",
    "channel": "NSS Survey",
    "product": "问界M5",
    "language": "zh",
    "sentiment_pred": "negative",
    "insight_pred": ["PRICE_001"],
    "insight_manul": ["null"]
  }
]
```

## 🔧 开发指南

### 项目结构

- `config.py`: 配置管理，使用 pydantic-settings
- `vector_db.py`: 向量数据库操作，基于 Milvus Lite
- `data_helper.py`: 数据处理，支持批量向量化
- `utils.py`: 工具函数，包括日志、进度条等
- `cli.py`: 命令行界面，使用 Typer

### 添加新功能

1. 在相应模块中添加新功能
2. 更新类型提示和文档字符串
3. 添加单元测试
4. 更新 README 文档

### 代码风格

- 使用类型提示
- 遵循 PEP 8 规范
- 添加详细的文档字符串
- 使用结构化日志

## 🧪 测试

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=perspective_kb

# 代码质量检查
ruff check .
black --check .
mypy src/
```

## 📝 更新日志

### v0.1.0 (2024-12-19)

- ✨ 初始版本发布
- 🚀 基于 Milvus Lite 的向量数据库
- 🤖 Ollama 文本向量化支持
- 📊 知识库和用户反馈处理
- 🛠️ 完整的命令行工具
- 📝 结构化日志系统
- ⚙️ 灵活的配置管理

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 作者: Abyteon
- 邮箱: bai.tn@icloud.com
- 项目地址: [GitHub Repository](https://github.com/your-username/perspective_kb)

---

如果这个项目对你有帮助，请给它一个 ⭐️！
