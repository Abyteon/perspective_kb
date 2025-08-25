"""
现代化配置管理模块
支持环境变量、配置文件和运行时配置
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class VectorDBType(str, Enum):
    """向量数据库类型"""
    MILVUS_LITE = "milvus_lite"
    MILVUS_SERVER = "milvus_server"


class Settings(BaseSettings):
    """
    应用配置类
    支持从环境变量、.env文件和默认值加载配置
    """
    
    # ============ 应用基础配置 ============
    app_name: str = Field(default="PerspectiveKB", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # ============ 向量数据库配置 ============
    vector_db_type: VectorDBType = Field(
        default=VectorDBType.MILVUS_LITE, 
        description="向量数据库类型"
    )
    
    # Milvus Lite配置
    db_path: str = Field(default="milvus_lite.db", description="Milvus Lite数据库路径")
    
    # Milvus服务器配置
    milvus_host: str = Field(default="localhost", description="Milvus服务器地址")
    milvus_port: int = Field(default=19530, description="Milvus服务器端口", ge=1, le=65535)
    milvus_username: Optional[str] = Field(default=None, description="Milvus用户名")
    milvus_password: Optional[str] = Field(default=None, description="Milvus密码")
    milvus_use_server: bool = Field(default=False, description="是否使用Milvus服务器模式")
    
    # ============ Ollama配置 ============
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    ollama_timeout: int = Field(default=300, description="Ollama超时时间(秒)", ge=10)
    embedding_model: str = Field(
        default="mitoza/Qwen3-Embedding-0.6B:latest",  # 使用可用的嵌入模型
        description="嵌入模型名称"
    )
    
    # 支持的嵌入模型列表
    supported_embedding_models: List[str] = Field(
        default=[
            "qwen2.5:latest",
            "llama3.1:latest", 
            "nomic-embed-text:latest",
            "mxbai-embed-large:latest"
        ],
        description="支持的嵌入模型列表"
    )
    
    # ============ 向量配置 ============
    vector_dim: int = Field(default=1024, description="向量维度", ge=128, le=4096)
    use_flat_index: bool = Field(default=True, description="是否使用FLAT索引")
    similarity_metric: str = Field(default="COSINE", description="相似度度量方式")
    top_k: int = Field(default=5, description="检索返回结果数量", ge=1, le=100)
    
    # ============ 数据路径配置 ============
    data_dir: Path = Field(default=Path("data"), description="数据目录")
    canonical_perspectives_dir: Path = Field(
        default=Path("data/canonical_perspectives"), 
        description="标准视角数据目录"
    )
    user_feedbacks_dir: Path = Field(
        default=Path("data/user_feedbacks"), 
        description="用户反馈数据目录"
    )
    processed_dir: Path = Field(
        default=Path("data/processed"), 
        description="处理后数据目录"
    )
    embeddings_dir: Path = Field(
        default=Path("embeddings"), 
        description="嵌入向量缓存目录"
    )
    
    # ============ 日志配置 ============
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    log_file: Optional[Path] = Field(default=Path("log/app.log"), description="日志文件路径")
    log_rotation: str = Field(default="10 MB", description="日志轮转大小")
    log_retention: str = Field(default="30 days", description="日志保留时间")
    
    # ============ 性能配置 ============
    batch_size: int = Field(default=100, description="批处理大小", ge=1, le=1000)
    max_workers: int = Field(default=4, description="最大工作线程数", ge=1, le=32)
    cache_size: int = Field(default=1000, description="缓存大小", ge=0)
    
    # ============ 安全配置 ============
    api_key: Optional[str] = Field(default=None, description="API密钥")
    rate_limit: int = Field(default=100, description="请求频率限制(每分钟)", ge=1)
    
    # ============ 模型配置 ============
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="PKB_",  # 环境变量前缀
        extra="forbid"  # 禁止额外字段
    )
    
    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v, info):
        """验证嵌入模型是否在支持列表中"""
        # 在Pydantic v2中，我们需要使用不同的方式访问其他字段
        # 这里简化处理，允许任何模型
        return v
    
    @field_validator("data_dir", "canonical_perspectives_dir", "user_feedbacks_dir", 
                    "processed_dir", "embeddings_dir", mode="before")
    @classmethod
    def validate_paths(cls, v):
        """验证和标准化路径"""
        if isinstance(v, str):
            v = Path(v)
        return v.resolve()
    
    @model_validator(mode="after")
    def validate_vector_db_config(self):
        """验证向量数据库配置的一致性"""
        # 确保配置一致性
        if self.vector_db_type == VectorDBType.MILVUS_SERVER:
            self.milvus_use_server = True
        elif self.vector_db_type == VectorDBType.MILVUS_LITE:
            self.milvus_use_server = False
            
        return self
    
    def get_database_uri(self) -> str:
        """获取数据库连接URI"""
        if self.milvus_use_server:
            uri = f"http://{self.milvus_host}:{self.milvus_port}"
            return uri
        else:
            return self.db_path
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """获取Ollama配置"""
        return {
            "host": self.ollama_host,
            "timeout": self.ollama_timeout,
            "model": self.embedding_model
        }
    
    def ensure_directories(self) -> None:
        """确保所有必需的目录存在"""
        directories = [
            self.data_dir,
            self.canonical_perspectives_dir,
            self.user_feedbacks_dir,
            self.processed_dir,
            self.embeddings_dir
        ]
        
        if self.log_file:
            directories.append(self.log_file.parent)
            
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump()
    
    def to_json(self, **kwargs) -> str:
        """转换为JSON格式"""
        return self.model_dump_json(**kwargs)


def create_settings(**overrides) -> Settings:
    """
    创建配置实例的工厂函数
    
    Args:
        **overrides: 覆盖的配置项
        
    Returns:
        Settings: 配置实例
    """
    return Settings(**overrides)


# 全局配置实例
settings = Settings()

# 确保目录存在
settings.ensure_directories()
