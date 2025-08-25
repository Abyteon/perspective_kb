"""
基本功能测试
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from perspective_kb.config import Settings
from perspective_kb.vector_db import LocalVectorDB, VectorDBError
from perspective_kb.data_helper import DataHelper, DataProcessingError
from perspective_kb.utils import get_logger, safe_operation


class TestSettings:
    """测试配置类"""
    
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.vector_dim == 1024
        assert settings.batch_size == 100
        assert settings.max_workers == 4
        assert settings.ollama_host == "http://localhost:11434"
    
    def test_custom_settings(self):
        """测试自定义配置"""
        with patch.dict('os.environ', {
            'VECTOR_DIM': '512',
            'BATCH_SIZE': '50'
        }):
            settings = Settings()
            assert settings.vector_dim == 512
            assert settings.batch_size == 50


class TestUtils:
    """测试工具函数"""
    
    def test_get_logger(self):
        """测试日志记录器"""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"
    
    def test_safe_operation_success(self):
        """测试安全操作成功"""
        def success_op():
            return "success"
        
        result = safe_operation(success_op, "操作失败")
        assert result == "success"
    
    def test_safe_operation_failure(self):
        """测试安全操作失败"""
        def failure_op():
            raise ValueError("测试错误")
        
        result = safe_operation(failure_op, "操作失败", default="default")
        assert result == "default"


class TestDataHelper:
    """测试数据处理助手"""
    
    def test_clean_text(self):
        """测试文本清理"""
        helper = DataHelper()
        
        # 测试基本清理
        text = "  这是一个  测试文本  "
        cleaned = helper.clean_text(text)
        assert cleaned == "这是一个 测试文本"
        
        # 测试空文本
        assert helper.clean_text("") == ""
        assert helper.clean_text(None) == ""
    
    def test_build_knowledge_text(self):
        """测试知识文本构建"""
        helper = DataHelper()
        
        item = {
            "aspect": "价格",
            "insight": "价格偏高",
            "sentiment": "negative",
            "description": "用户认为价格高",
            "examples": ["太贵了", "不划算"],
            "keywords": ["贵", "高"]
        }
        
        text = helper.build_knowledge_text(item)
        assert "维度: 价格" in text
        assert "观点: 价格偏高" in text
        assert "情感: negative" in text
    
    def test_build_feedback_text(self):
        """测试反馈文本构建"""
        helper = DataHelper()
        
        # 有摘要的情况
        text = helper.build_feedback_text("原始文本", "摘要文本")
        assert "原文: 原始文本" in text
        assert "摘要: 摘要文本" in text
        
        # 无摘要的情况
        text = helper.build_feedback_text("原始文本")
        assert "原文: 原始文本" in text
        assert "摘要:" not in text


class TestVectorDB:
    """测试向量数据库"""
    
    @patch('perspective_kb.vector_db.MilvusClient')
    def test_init_success(self, mock_client):
        """测试初始化成功"""
        mock_client.return_value = Mock()
        
        db = LocalVectorDB("test.db")
        assert db.db_path == "test.db"
        assert db.client is not None
    
    @patch('perspective_kb.vector_db.MilvusClient')
    def test_init_failure(self, mock_client):
        """测试初始化失败"""
        mock_client.side_effect = Exception("连接失败")
        
        with pytest.raises(VectorDBError):
            LocalVectorDB("test.db")
    
    @patch('perspective_kb.vector_db.MilvusClient')
    def test_context_manager(self, mock_client):
        """测试上下文管理器"""
        mock_client.return_value = Mock()
        
        with LocalVectorDB("test.db") as db:
            assert db is not None
        
        # 检查是否调用了close方法
        mock_client.return_value.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
