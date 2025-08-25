"""
视角知识库系统

一个基于向量数据库的视角知识库管理系统，支持知识库构建、用户反馈分析和智能匹配。
"""

__version__ = "0.1.0"
__author__ = "Abyteon"
__email__ = "bai.tn@icloud.com"

# 主要类
from .config import Settings, settings
from .vector_db import LocalVectorDB, VectorDBError
from .data_helper import DataHelper, DataProcessingError
from .utils import (
    get_logger,
    timer,
    console,
    display_table,
    display_summary,
    safe_operation,
    ensure_directory
)

# 版本信息
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    
    # 配置
    "Settings",
    "settings",
    
    # 核心类
    "LocalVectorDB",
    "VectorDBError",
    "DataHelper", 
    "DataProcessingError",
    
    # 工具函数
    "get_logger",
    "timer",
    "console",
    "display_table",
    "display_summary",
    "safe_operation",
    "ensure_directory",
]
