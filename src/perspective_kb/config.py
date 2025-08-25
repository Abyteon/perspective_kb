"""
配置管理模块
"""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    db_path: str = Field(default="milvus_lite.db", description="Milvus Lite数据库路径")
    
    # Ollama配置
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    embedding_model: str = Field(
        default="mitoza/Qwen3-Embedding-0.6B:latest", 
        description="嵌入模型名称"
    )
    
    # 向量配置
    vector_dim: int = Field(default=1024, description="向量维度")
    use_flat_index: bool = Field(default=True, description="是否使用FLAT索引")
    top_k: int = Field(default=5, description="检索返回结果数量")
    
    # 数据路径配置
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
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: Optional[Path] = Field(default=None, description="日志文件路径")
    
    # 性能配置
    batch_size: int = Field(default=100, description="批处理大小")
    max_workers: int = Field(default=4, description="最大工作线程数")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# 全局配置实例
settings = Settings()
