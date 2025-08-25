"""
现代化向量数据库模块 - 2025年版本
支持Milvus Lite和Milvus服务器，优化性能和错误处理
"""
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
from dataclasses import dataclass

from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
    connections,
    db,
    utility
)

from .config import settings, VectorDBType
from .utils import get_logger


class VectorDBError(Exception):
    """向量数据库操作异常"""
    pass


class ConnectionError(VectorDBError):
    """连接异常"""
    pass


class CollectionError(VectorDBError):
    """集合操作异常"""
    pass


class SearchError(VectorDBError):
    """搜索操作异常"""
    pass


@dataclass
class SearchResult:
    """搜索结果数据类"""
    id: str
    score: float
    metadata: Dict[str, Any]
    distance: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "score": self.score,
            "metadata": self.metadata,
            "distance": self.distance
        }


@dataclass
class CollectionInfo:
    """集合信息数据类"""
    name: str
    row_count: int
    status: str
    schema: Optional[CollectionSchema] = None
    index_info: Optional[Dict[str, Any]] = None


class BaseVectorDB:
    """向量数据库基类"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.client: Optional[MilvusClient] = None
        self._connection_pool = None
        
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect_async()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_async()
    
    def connect(self) -> bool:
        """连接数据库（同步）"""
        raise NotImplementedError
    
    async def connect_async(self) -> bool:
        """连接数据库（异步）"""
        # 默认实现：在线程池中运行同步方法
        return await asyncio.get_event_loop().run_in_executor(None, self.connect)
    
    def close(self) -> None:
        """关闭连接（同步）"""
        try:
            if self.client:
                self.client.close()
                self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.warning("关闭数据库连接时出错", error=str(e))
    
    async def close_async(self) -> None:
        """关闭连接（异步）"""
        await asyncio.get_event_loop().run_in_executor(None, self.close)
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.client:
                return False
            collections = self.client.list_collections()
            return True
        except Exception as e:
            self.logger.error("健康检查失败", error=str(e))
            return False
    
    def create_collection(self, 
                         collection_name: str, 
                         vector_dim: Optional[int] = None,
                         metric_type: Optional[str] = None,
                         index_type: Optional[str] = None,
                         force_recreate: bool = False) -> bool:
        """创建集合"""
        raise NotImplementedError
    
    def upsert(self, 
               entities: List[Dict[str, Any]], 
               collection_name: str,
               batch_size: Optional[int] = None) -> bool:
        """插入或更新数据"""
        raise NotImplementedError
    
    def search(self, 
               collection_name: str, 
               query_vectors: List[List[float]],
               top_k: Optional[int] = None,
               search_params: Optional[Dict[str, Any]] = None,
               filter_expr: Optional[str] = None) -> List[List[SearchResult]]:
        """向量搜索"""
        raise NotImplementedError
    
    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """获取集合信息"""
        raise NotImplementedError
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            return self.client.list_collections() if self.client else []
        except Exception as e:
            self.logger.error("列出集合失败", error=str(e))
            return []
    
    def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if self.client and self.client.has_collection(collection_name):
                self.client.drop_collection(collection_name)
                self.logger.info("集合删除成功", collection_name=collection_name)
                return True
            else:
                self.logger.warning("集合不存在", collection_name=collection_name)
                return False
        except Exception as e:
            self.logger.error("删除集合失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise CollectionError(f"删除集合 {collection_name} 失败: {e}")


class LocalVectorDB(BaseVectorDB):
    """本地向量数据库管理器（Milvus Lite）"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化本地向量数据库
        
        Args:
            db_path: 数据库文件路径
        """
        super().__init__()
        self.db_path = db_path or settings.get_database_uri()
        self.logger = get_logger("LocalVectorDB")
        
    def connect(self) -> bool:
        """连接到Milvus Lite数据库"""
        try:
            # 确保数据库目录存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self.client = MilvusClient(uri=self.db_path)
            self.logger.info("本地向量数据库连接成功", db_path=self.db_path)
            return True
        except Exception as e:
            self.logger.error("本地向量数据库连接失败", error=str(e), db_path=self.db_path)
            raise ConnectionError(f"无法连接到本地向量数据库: {e}")
    
    def create_collection(self, 
                         collection_name: str, 
                         vector_dim: Optional[int] = None,
                         metric_type: Optional[str] = None,
                         index_type: Optional[str] = None,
                         force_recreate: bool = False) -> bool:
        """
        创建集合
        
        Args:
            collection_name: 集合名称
            vector_dim: 向量维度
            metric_type: 相似度度量方式
            index_type: 索引类型
            force_recreate: 是否强制重新创建
        """
        vector_dim = vector_dim or settings.vector_dim
        metric_type = metric_type or settings.similarity_metric
        index_type = index_type or ("FLAT" if settings.use_flat_index else "IVF_FLAT")
        
        try:
            # 检查集合是否已存在
            if self.client.has_collection(collection_name):
                if force_recreate:
                    self.logger.info("删除现有集合", collection_name=collection_name)
                    self.client.drop_collection(collection_name)
                else:
                    self.logger.info("集合已存在", collection_name=collection_name)
                    return True
            
            # 创建集合schema
            schema = CollectionSchema([
                FieldSchema(
                    name="id", 
                    dtype=DataType.VARCHAR, 
                    max_length=100, 
                    is_primary=True, 
                    auto_id=False,
                    description="主键ID"
                ),
                FieldSchema(
                    name="vector", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=vector_dim,
                    description="向量数据"
                ),
                FieldSchema(
                    name="text_for_embedding", 
                    dtype=DataType.VARCHAR, 
                    max_length=65535,
                    description="用于嵌入的文本"
                ),
                FieldSchema(
                    name="metadata", 
                    dtype=DataType.JSON,
                    description="元数据"
                )
            ], description=f"视角知识库集合 - {collection_name}")
            
            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                properties={"collection.ttl.seconds": 0}  # 不自动删除
            )
            
            # 在集合创建后立即建立索引
            self._create_index_immediately(collection_name, metric_type)
            
            self.logger.info("集合创建成功", 
                           collection_name=collection_name,
                           vector_dim=vector_dim,
                           metric_type=metric_type,
                           index_type=index_type)
            
            return True
            
        except Exception as e:
            self.logger.error("创建集合失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise CollectionError(f"创建集合 {collection_name} 失败: {e}")
    
    def upsert(self, 
               entities: List[Dict[str, Any]], 
               collection_name: str,
               batch_size: Optional[int] = None) -> bool:
        """
        批量插入或更新数据
        
        Args:
            entities: 实体数据列表
            collection_name: 集合名称
            batch_size: 批处理大小
        """
        batch_size = batch_size or settings.batch_size
        
        try:
            if not entities:
                self.logger.warning("没有数据需要插入")
                return True
            
            total_batches = (len(entities) + batch_size - 1) // batch_size
            successful_inserts = 0
            
            # 分批处理
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                try:
                    # 准备数据
                    insert_data = []
                    for item in batch:
                        insert_data.append({
                            "id": str(item["id"]),
                            "vector": item["vector"],
                            "text_for_embedding": item["text_for_embedding"],
                            "metadata": item["metadata"]
                        })
                    
                    # 插入数据
                    start_time = time.time()
                    res = self.client.insert(collection_name, insert_data)
                    insert_time = time.time() - start_time
                    
                    insert_count = res.get('insert_count', len(batch))
                    successful_inserts += insert_count
                    
                    self.logger.debug("批次数据插入成功", 
                                    collection_name=collection_name,
                                    batch_size=len(batch),
                                    batch_num=batch_num,
                                    total_batches=total_batches,
                                    insert_count=insert_count,
                                    insert_time=f"{insert_time:.3f}s")
                    
                except Exception as batch_error:
                    self.logger.error("批次数据插入失败", 
                                    collection_name=collection_name,
                                    batch_num=batch_num,
                                    error=str(batch_error))
                    # 继续处理下一批次
                    continue
            
            self.logger.info("数据插入完成", 
                           collection_name=collection_name,
                           total_entities=len(entities),
                           successful_inserts=successful_inserts,
                           total_batches=total_batches)
            
            return successful_inserts > 0
            
        except Exception as e:
            self.logger.error("数据插入失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise VectorDBError(f"插入数据到集合 {collection_name} 失败: {e}")
    
    def _create_index_immediately(self, collection_name: str, metric_type: str = "COSINE") -> None:
        """在集合创建后立即建立索引"""
        try:
            from pymilvus import MilvusClient
            
            # 使用官方推荐的索引参数准备方法
            index_params = MilvusClient.prepare_index_params()
            
            index_params.add_index(
                field_name="vector",  # 向量字段名称
                index_type="FLAT",   # 对于小数据集使用FLAT索引
                index_name="vector_index",  # 索引名称
                metric_type=metric_type,  # 相似度度量
                params={}  # FLAT索引不需要额外参数
            )
            
            self.client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )
            
            self.logger.info("索引创建成功", 
                           collection_name=collection_name,
                           index_type="FLAT",
                           metric_type=metric_type)
            
        except Exception as e:
            self.logger.error("索引创建失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise VectorDBError(f"为集合 {collection_name} 创建索引失败: {e}")
    
    def _ensure_index_exists(self, collection_name: str) -> None:
        """确保索引存在，如果不存在则创建"""
        try:
            # 检查是否已有索引
            index_info = self.client.describe_index(collection_name, "vector")
            self.logger.info("索引已存在", collection_name=collection_name)
        except:
            # 索引不存在，尝试创建 - 使用官方推荐的方式
            try:
                from pymilvus import MilvusClient
                
                # 使用官方推荐的索引参数准备方法
                index_params = MilvusClient.prepare_index_params()
                
                index_params.add_index(
                    field_name="vector",  # 向量字段名称
                    index_type="FLAT",   # 索引类型
                    index_name="vector_index",  # 索引名称
                    metric_type=settings.similarity_metric,  # 相似度度量
                    params={}  # FLAT索引不需要额外参数
                )
                
                self.client.create_index(
                    collection_name=collection_name,
                    index_params=index_params
                )
                self.logger.info("索引创建成功", collection_name=collection_name)
            except Exception as create_error:
                self.logger.warning("索引创建失败", 
                                  collection_name=collection_name,
                                  error=str(create_error))
    
    def search(self, 
               collection_name: str, 
               query_vectors: List[List[float]],
               top_k: Optional[int] = None,
               search_params: Optional[Dict[str, Any]] = None,
               filter_expr: Optional[str] = None) -> List[List[SearchResult]]:
        """
        向量相似性搜索
        
        Args:
            collection_name: 集合名称
            query_vectors: 查询向量列表
            top_k: 返回结果数量
            search_params: 搜索参数
            filter_expr: 过滤表达式
        """
        top_k = top_k or settings.top_k
        search_params = search_params or {"params": {}}
        
        try:
            import time
            start_time = time.time()
            
            # 确保集合已加载
            if not self.client.has_collection(collection_name):
                raise VectorDBError(f"集合 {collection_name} 不存在")
            
            # 加载集合到内存中
            try:
                self.client.load_collection(collection_name)
                # 等待片刻让索引完全加载
                time.sleep(0.1)
            except Exception as load_error:
                self.logger.warning("集合加载警告", 
                                  collection_name=collection_name,
                                  error=str(load_error))
            
            # 简化搜索参数以支持Milvus Lite
            search_kwargs = {
                "collection_name": collection_name,
                "data": query_vectors,
                "anns_field": "vector",
                "limit": top_k,
                "output_fields": ["text_for_embedding", "metadata"],
            }
            
            # 对于Milvus Lite，可能不需要搜索参数
            if filter_expr:
                search_kwargs["filter"] = filter_expr
            
            results = self.client.search(**search_kwargs)
            search_time = time.time() - start_time
            
            # 处理搜索结果
            processed_results = []
            for query_result in results:
                query_processed = []
                for hit in query_result:
                    # 计算标准化相似度分数 (0-1范围)
                    if settings.similarity_metric == "COSINE":
                        # COSINE: distance范围是[-1, 1], 转换为[0, 1]
                        normalized_score = (hit.distance + 1) / 2
                    elif settings.similarity_metric == "L2":
                        # L2: distance越小越相似，转换为相似度分数
                        normalized_score = 1 / (1 + hit.distance)
                    else:
                        # 其他度量方式
                        normalized_score = max(0, min(1, hit.distance))
                    
                    metadata = hit.get("entity", {}).get("metadata", {})
                    
                    search_result = SearchResult(
                        id=hit.id,
                        score=normalized_score,
                        metadata=metadata,
                        distance=hit.distance
                    )
                    query_processed.append(search_result)
                
                # 按相似度分数排序（降序）
                query_processed.sort(key=lambda x: x.score, reverse=True)
                processed_results.append(query_processed)
            
            self.logger.debug("搜索完成", 
                            collection_name=collection_name,
                            query_count=len(query_vectors),
                            top_k=top_k,
                            search_time=f"{search_time:.3f}s")
            
            return processed_results
            
        except Exception as e:
            self.logger.error("搜索失败", 
                            collection_name=collection_name,
                            error=str(e))
            raise SearchError(f"在集合 {collection_name} 中搜索失败: {e}")
    
    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """获取集合详细信息"""
        try:
            if not self.client.has_collection(collection_name):
                raise CollectionError(f"集合 {collection_name} 不存在")
            
            # 获取集合描述
            collection_desc = self.client.describe_collection(collection_name)
            
            # 获取统计信息
            stats = self.client.get_collection_stats(collection_name)
            row_count = stats.get('row_count', 0)
            
            # 获取索引信息
            try:
                index_info = self.client.describe_index(collection_name, "vector")
            except:
                index_info = None
            
            return CollectionInfo(
                name=collection_name,
                row_count=row_count,
                status="loaded",
                schema=collection_desc,
                index_info=index_info
            )
            
        except Exception as e:
            self.logger.error("获取集合信息失败", 
                            collection_name=collection_name,
                            error=str(e))
            return CollectionInfo(
                name=collection_name,
                row_count=0,
                status="error",
                schema=None,
                index_info=None
            )


class ServerVectorDB(LocalVectorDB):
    """Milvus服务器向量数据库管理器"""
    
    def __init__(self, 
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        初始化Milvus服务器连接
        
        Args:
            host: 服务器地址
            port: 服务器端口
            username: 用户名
            password: 密码
        """
        self.host = host or settings.milvus_host
        self.port = port or settings.milvus_port
        self.username = username or settings.milvus_username
        self.password = password or settings.milvus_password
        self.logger = get_logger("ServerVectorDB")
        self.client = None
        
    def connect(self) -> bool:
        """连接到Milvus服务器"""
        try:
            uri = f"http://{self.host}:{self.port}"
            
            # 配置连接参数
            connect_params = {"uri": uri}
            if self.username and self.password:
                connect_params.update({
                    "user": self.username,
                    "password": self.password
                })
            
            self.client = MilvusClient(**connect_params)
            
            # 测试连接
            if not self.health_check():
                raise ConnectionError("连接测试失败")
                
            self.logger.info("Milvus服务器连接成功", 
                           host=self.host, 
                           port=self.port,
                           username=self.username)
            return True
        except Exception as e:
            self.logger.error("Milvus服务器连接失败", 
                            error=str(e), 
                            host=self.host, 
                            port=self.port)
            raise ConnectionError(f"无法连接到Milvus服务器: {e}")


def get_vector_db() -> BaseVectorDB:
    """
    工厂函数：根据配置返回向量数据库实例
    
    Returns:
        BaseVectorDB: 向量数据库实例
    """
    try:
        if settings.vector_db_type == VectorDBType.MILVUS_SERVER or settings.milvus_use_server:
            db_instance = ServerVectorDB()
        else:
            db_instance = LocalVectorDB()
        
        # 自动连接
        db_instance.connect()
        return db_instance
        
    except Exception as e:
        logger = get_logger("VectorDBFactory")
        logger.error("创建向量数据库实例失败", error=str(e))
        raise VectorDBError(f"创建向量数据库实例失败: {e}")


# 便利函数
def create_local_db(db_path: Optional[str] = None) -> LocalVectorDB:
    """创建本地向量数据库实例"""
    db = LocalVectorDB(db_path)
    db.connect()
    return db


def create_server_db(host: str, port: int = 19530, 
                    username: Optional[str] = None, 
                    password: Optional[str] = None) -> ServerVectorDB:
    """创建服务器向量数据库实例"""
    db = ServerVectorDB(host, port, username, password)
    db.connect()
    return db