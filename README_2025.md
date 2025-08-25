# 🚀 PerspectiveKB - 现代化视角知识库系统 (2025版)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic V2](https://img.shields.io/badge/Pydantic-V2-green.svg)](https://docs.pydantic.dev/)
[![Milvus 2.6+](https://img.shields.io/badge/Milvus-2.6+-orange.svg)](https://milvus.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-purple.svg)](https://ollama.ai/)

基于向量数据库的现代化视角知识库管理系统，支持语义搜索、智能匹配和用户反馈分析。

## ✨ 2025年版本特性

### 🔧 技术升级
- **Python 3.12+** - 使用最新Python版本和特性
- **Pydantic V2** - 现代化配置管理和数据验证
- **异步支持** - 异步数据处理和向量化
- **类型安全** - 完整的类型注解和验证
- **现代CLI** - 丰富交互式命令行界面

### 🚀 核心功能
- **智能向量化** - 支持多种嵌入模型和缓存机制
- **语义搜索** - 基于余弦相似度的高精度搜索
- **数据处理** - 批量处理、并行计算、错误恢复
- **性能监控** - 实时统计、基准测试、缓存分析
- **灵活存储** - 支持Milvus Lite和Milvus服务器

### 🎯 新增特性
- **嵌入缓存系统** - 智能缓存减少重复计算
- **进度显示** - 实时处理进度和状态展示
- **错误恢复** - 优雅的错误处理和重试机制
- **配置验证** - 全面的配置校验和类型检查
- **性能基准** - 内置性能测试和分析工具

## 📦 快速开始

### 环境要求
- Python 3.12+
- [Pixi](https://pixi.sh/) 包管理器
- [Ollama](https://ollama.ai/) 本地运行

### 1. 安装依赖
```bash
# 使用Pixi安装所有依赖
pixi install

# 或者使用pip安装
pip install -r requirements.txt
```

### 2. 配置系统
```bash
# 复制配置文件
cp env.example .env

# 编辑配置（可选）
vim .env
```

### 3. 启动Ollama服务
```bash
# 下载并启动嵌入模型
ollama pull qwen2.5:latest
ollama serve
```

### 4. 验证安装
```bash
# 运行系统测试
pixi run python test_system.py

# 查看配置
pixi run python -m perspective_kb.cli config

# 检查系统状态
pixi run python -m perspective_kb.cli status
```

## 🎯 使用指南

### 📚 数据处理
```bash
# 处理所有数据（知识库+反馈）
pixi run python -m perspective_kb.cli process

# 强制重新处理
pixi run python -m perspective_kb.cli process --force

# 自定义参数
pixi run python -m perspective_kb.cli process --batch-size 200 --max-workers 8
```

### 🔍 语义搜索
```bash
# 搜索知识库
pixi run python -m perspective_kb.cli search "车辆动力性能如何"

# 搜索用户反馈
pixi run python -m perspective_kb.cli search "用户评价" --collection feedback

# 设置返回数量和阈值
pixi run python -m perspective_kb.cli search "空间表现" --top-k 10 --threshold 0.7
```

### 📊 系统管理
```bash
# 查看集合状态
pixi run python -m perspective_kb.cli collections --detailed

# 性能基准测试
pixi run python -m perspective_kb.cli benchmark --size 100

# 清理集合
pixi run python -m perspective_kb.cli clean knowledge --confirm
```

### 🚀 程序API调用
```bash
# 运行主程序（异步模式）
pixi run python -m src.main

# 或者使用pixi任务
pixi run main
```

## 🏗️ 架构设计

### 📁 项目结构
```
perspective_kb/
├── src/
│   ├── main.py                 # 主程序入口
│   └── perspective_kb/
│       ├── __init__.py         # 包初始化
│       ├── config.py           # 现代化配置管理
│       ├── vector_db.py        # 向量数据库抽象
│       ├── data_helper.py      # 数据处理助手
│       ├── utils.py            # 工具函数
│       └── cli.py              # CLI命令行接口
├── data/                       # 数据目录
│   ├── canonical_perspectives/ # 标准视角知识库
│   ├── user_feedbacks/         # 用户反馈数据
│   └── processed/              # 处理后数据
├── embeddings/                 # 嵌入缓存目录
├── log/                        # 日志目录
├── test_system.py              # 系统测试脚本
└── pyproject.toml              # 项目配置
```

### 🔧 核心组件

#### ConfigManager (config.py)
- **现代化配置** - 基于Pydantic V2的配置管理
- **环境变量** - 支持PKB_前缀的环境变量
- **配置验证** - 全面的字段验证和类型检查
- **动态配置** - 运行时配置工厂和覆盖

#### VectorDB (vector_db.py)
- **统一接口** - 抽象基类支持多种后端
- **连接池** - 高效的连接管理和资源池
- **异步支持** - 异步数据库操作
- **错误处理** - 详细的异常分类和处理

#### DataHelper (data_helper.py)
- **智能缓存** - 基于文本哈希的嵌入缓存
- **并行处理** - 多线程批量向量化
- **进度显示** - 实时处理进度和统计
- **错误恢复** - 重试机制和部分失败处理

#### CLI Interface (cli.py)
- **丰富交互** - 基于Typer的现代CLI
- **状态展示** - 美观的表格和进度条
- **多种格式** - 支持表格和JSON输出
- **命令补全** - 智能命令提示和帮助

## ⚙️ 配置选项

### 环境变量配置
```bash
# 基础配置
PKB_APP_NAME=PerspectiveKB
PKB_DEBUG=false

# 数据库配置
PKB_VECTOR_DB_TYPE=milvus_lite
PKB_DB_PATH=milvus_lite.db
PKB_MILVUS_HOST=localhost
PKB_MILVUS_PORT=19530

# Ollama配置
PKB_OLLAMA_HOST=http://localhost:11434
PKB_EMBEDDING_MODEL=qwen2.5:latest
PKB_OLLAMA_TIMEOUT=300

# 向量配置
PKB_VECTOR_DIM=1024
PKB_SIMILARITY_METRIC=COSINE
PKB_TOP_K=5

# 性能配置
PKB_BATCH_SIZE=100
PKB_MAX_WORKERS=4
PKB_CACHE_SIZE=1000

# 日志配置
PKB_LOG_LEVEL=INFO
PKB_LOG_FILE=log/app.log
```

### 支持的嵌入模型
- `qwen2.5:latest` (推荐)
- `llama3.1:latest`
- `nomic-embed-text:latest`
- `mxbai-embed-large:latest`

## 📊 性能优化

### 缓存机制
- **嵌入缓存** - 自动缓存生成的向量
- **模型缓存** - 智能模型版本管理
- **配置缓存** - 运行时配置优化

### 并行处理
- **多线程** - 可配置的工作线程池
- **批处理** - 智能批大小调整
- **异步IO** - 异步数据库操作

### 内存优化
- **流式处理** - 大文件流式读取
- **垃圾回收** - 及时释放内存资源
- **连接池** - 高效的数据库连接管理

## 🔧 开发指南

### 运行测试
```bash
# 运行所有测试
pixi run python test_system.py

# 运行linting
pixi run lint

# 运行类型检查
pixi run type-check
```

### 代码风格
- **Black** - 代码格式化
- **isort** - 导入排序
- **mypy** - 类型检查
- **flake8** - 代码规范

### 添加新功能
1. 在对应模块中添加功能
2. 更新类型注解
3. 添加测试用例
4. 更新文档

## 🚀 部署指南

### Docker部署
```bash
# 构建镜像
docker build -t perspective-kb:2025 .

# 运行容器
docker run -d \
  --name perspective-kb \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/embeddings:/app/embeddings \
  -p 8000:8000 \
  perspective-kb:2025
```

### 生产环境
```bash
# 使用生产配置
export PKB_LOG_LEVEL=INFO
export PKB_BATCH_SIZE=500
export PKB_MAX_WORKERS=16

# 启动服务
pixi run main
```

## 📈 监控和观测

### 日志系统
- **结构化日志** - JSON格式日志输出
- **日志轮转** - 自动日志文件管理
- **多级日志** - DEBUG/INFO/WARNING/ERROR

### 性能监控
```bash
# 运行基准测试
pixi run python -m perspective_kb.cli benchmark

# 查看缓存统计
pixi run python -m perspective_kb.cli status --detailed

# 监控系统资源
htop  # 或其他系统监控工具
```

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支
3. 提交代码更改
4. 运行测试套件
5. 创建Pull Request

## 📝 更新日志

### v2025.1.0
- ✅ 升级到Python 3.12和Pydantic V2
- ✅ 重构配置管理系统
- ✅ 添加异步支持和缓存机制
- ✅ 改进CLI界面和错误处理
- ✅ 优化性能和内存使用
- ✅ 增强类型安全和代码质量

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙋‍♂️ 支持

- 📧 邮箱: bai.tn@icloud.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/your-repo/perspective_kb/issues)
- 📖 文档: [项目Wiki](https://github.com/your-repo/perspective_kb/wiki)

---

**🎉 感谢使用PerspectiveKB 2025版！**
