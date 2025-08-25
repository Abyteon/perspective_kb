"""
向量数据库模块 - 基于Milvus Lite
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
)

from .config import settings
from .utils import get_logger


class VectorDBError(Exception):
    """向量数据库操作异常"""
    pass


class LocalVectorDB:
    """本地向量数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化向量数据库
        
        Args:
            db_path: 数据库文件路径，如果为None则使用配置中的默认路径
        """
        self.db_path = db_path or settings.db_path
        self.logger = get_logger("vector_db")
        self.collections: Dict[str, List[FieldSchema]] = {}
        
        try:
            self.client = MilvusClient(uri=self.db_path)
            self.logger.info("向量数据库连接成功", db_path=self.db_path)
        except Exception as e:
            self.logger.error("向量数据库连接失败", error=str(e), db_path=self.db_path)
            raise VectorDBError(f"无法连接到向量数据库: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def close(self):
        """关闭数据库连接"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                self.logger.info("向量数据库连接已关闭")
        except Exception as e:
            self.logger.warning("关闭数据库连接时出错", error=str(e))
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的健康检查 - 尝试获取集合列表
            collections = self.client.list_collections()
            return True
        except Exception as e:
            self.logger.error("健康检查失败", error=str(e))
            return False
    
    def create_collection(self, 
                         collection_name: str, 
                         vector_dim: Optional[int] = None,
                         use_flat: Optional[bool] = None,
                         force_recreate: bool = False) -> bool:
        """
        创建集合
        
        Args:
            collection_name: 集合名称
            vector_dim: 向量维度
            use_flat: 是否使用FLAT索引
            force_recreate: 是否强制重新创建
            
        Returns:
            bool: 创建是否成功
        """
        vector_dim = vector_dim or settings.vector_dim
        use_flat = use_flat if use_flat is not None else settings.use_flat_index
        
        try:
            # 检查集合是否已存在
            if self.client.has_collection(collection_name):
                if force_recreate:
                    self.logger.info("删除现有集合", collection_name=collection_name)
                    self.client.drop_collection(collection_name)
                else:
                    self.logger.info("集合已存在", collection_name=collection_name)
                    return True
            
            # 定义字段模式
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    auto_id=False,
                    max_length=24,
                ),
                FieldSchema(
                    name="vector", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=vector_dim
                ),
                FieldSchema(
                    name="text_for_embedding", 
                    dtype=DataType.VARCHAR, 
                    max_length=1000
                ),
                FieldSchema(
                    name="metadata", 
                    dtype=DataType.JSON
                ),
            ]
            
            schema = CollectionSchema(fields=fields)
            
            # 准备索引参数
            index_params = self.client.prepare_index_params()
            index_type = "FLAT" if use_flat else "IVF_FLAT"
            
            index_params.add_index(
                field_name="vector",
                index_type=index_type,
                index_name="vector_index",
                metric_type="IP",  # 内积相似度
                params={},
            )
            
            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )
            
            self.collections[collection_name] = fields
            self.logger.info("集合创建成功", 
                           collection_name=collection_name,
                           vector_dim=vector_dim,
                           index_type=index_type)
            
            return True
            
        except Exception as e:
            self.logger.error("创建集合失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise VectorDBError(f"创建集合 {collection_name} 失败: {e}")
    
    def upsert(self, 
               entities: List[Dict[str, Any]], 
               collection_name: str,
               batch_size: Optional[int] = None) -> bool:
        """
        插入或更新数据
        
        Args:
            entities: 要插入的实体列表
            collection_name: 集合名称
            batch_size: 批处理大小
            
        Returns:
            bool: 操作是否成功
        """
        if not entities:
            self.logger.warning("没有数据需要插入", collection_name=collection_name)
            return True
        
        batch_size = batch_size or settings.batch_size
        
        try:
            # 分批处理
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                self.client.upsert(collection_name, data=batch)
                self.logger.debug("批次插入完成", 
                                collection_name=collection_name,
                                batch_size=len(batch),
                                batch_index=i // batch_size + 1)
            
            # 刷新并加载集合
            self.client.flush(collection_name)
            self.client.load_collection(collection_name)
            
            self.logger.info("数据插入成功", 
                           collection_name=collection_name,
                           total_count=len(entities))
            
            return True
            
        except Exception as e:
            self.logger.error("数据插入失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise VectorDBError(f"插入数据到集合 {collection_name} 失败: {e}")
    
    def search(self, 
               collection_name: str, 
               query_vectors: List[List[float]],
               top_k: Optional[int] = None,
               search_params: Optional[Dict[str, Any]] = None) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """
        向量搜索
        
        Args:
            collection_name: 集合名称
            query_vectors: 查询向量列表
            top_k: 返回结果数量
            search_params: 搜索参数
            
        Returns:
            List[List[Tuple]]: 搜索结果，每个查询向量对应一个结果列表
        """
        top_k = top_k or settings.top_k
        search_params = search_params or {"params": {}}
        
        try:
            results = self.client.search(
                collection_name=collection_name,
                data=query_vectors,
                anns_field="vector",
                limit=top_k,
                search_params=search_params,
                output_fields=["metadata"],
            )
            
            # 处理搜索结果
            processed_results = []
            for query_result in results:
                query_processed = []
                for hit in query_result:
                    # 归一化相似度分数到[0,1]范围
                    normalized_score = (hit.distance + 1) / 2
                    query_processed.append((
                        hit.id,
                        normalized_score,
                        hit.get("entity", {})
                    ))
                
                # 按相似度排序
                query_processed.sort(key=lambda x: x[1], reverse=True)
                processed_results.append(query_processed)
            
            self.logger.debug("搜索完成", 
                            collection_name=collection_name,
                            query_count=len(query_vectors),
                            top_k=top_k)
            
            return processed_results
            
        except Exception as e:
            self.logger.error("搜索失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise VectorDBError(f"在集合 {collection_name} 中搜索失败: {e}")
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            if not self.client.has_collection(collection_name):
                return {"error": "集合不存在"}
            
            # 获取集合信息
            collection_info = self.client.describe_collection(collection_name)
            
            # 获取行数
            row_count = self.client.num_entities(collection_name)
            
            return {
                "collection_name": collection_name,
                "row_count": row_count,
                "fields": [field.name for field in collection_info.fields],
                "status": "active"
            }
            
        except Exception as e:
            self.logger.error("获取集合统计信息失败", 
                            collection_name=collection_name,
                            error=str(e))
            return {"error": str(e)}
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            return self.client.list_collections()
        except Exception as e:
            self.logger.error("获取集合列表失败", error=str(e))
            return []
    
    def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if self.client.has_collection(collection_name):
                self.client.drop_collection(collection_name)
                if collection_name in self.collections:
                    del self.collections[collection_name]
                self.logger.info("集合删除成功", collection_name=collection_name)
                return True
            else:
                self.logger.warning("集合不存在", collection_name=collection_name)
                return False
        except Exception as e:
            self.logger.error("删除集合失败", 
                            collection_name=collection_name,
                            error=str(e))
            return False
