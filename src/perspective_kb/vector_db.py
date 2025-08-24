from importlib import metadata
from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
)


class LocalVectorDB:
    def __init__(self, db_path: str):
        """
        db_path: 本地 Milvus Lite 文件路径
        """
        self.client = MilvusClient(uri=db_path)
        self.collections = {}
        # {collection_name: schema_info}

    # -------------------------
    # 创建 collection
    # -------------------------
    def create_collection(self, collection_name: str, vector_dim: int, use_flat=True):
        """
        创建一个新的 collection
        """
        if self.client.has_collection(collection_name):
            self.client.drop_collection(collection_name)

        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                auto_id=False,
                max_length=24,
            ),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
            FieldSchema(
                name="text_for_embedding", dtype=DataType.VARCHAR, max_length=1000
            ),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        schema = CollectionSchema(fields=fields)
        # 创建索引
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            # 被索引的字段
            field_name="vector",
            # 索引类型
            index_type=("FLAT" if use_flat else "IVF_FLAT"),
            index_name="vector_index",
            # 度量相似度的方式
            metric_type="IP",
            params={},
        )
        self.client.create_collection(
            collection_name=collection_name, schema=schema, index_params=index_params
        )

        self.collections[collection_name] = fields

    # -------------------------
    # 向 collection 插入或更新数据
    # -------------------------
    def upsert(self, entities, collection_name: str):
        """
        插入或更新数据
        """
        self.client.upsert(collection_name, data=entities)
        self.client.flush(collection_name)
        self.client.load_collection(collection_name)

    # -------------------------
    # 查询向量
    # -------------------------
    def search(self, collection_name: str, query_vectors, top_k=5):
        """
        查询向量
        """
        results = self.client.search(
            collection_name=collection_name,
            data=query_vectors,
            anns_field="vector",
            limit=top_k,
            search_params={"params": {}},
            output_fields=["metadata"],
        )
        # print("Search results:", results)
        most_similar = []
        for hit in results[0]:
            most_similar.append(
                (hit.id, (hit.distance + 1) / 2, hit.get("entity"))
            )  # 归一化到[0,1]

        most_similar.sort(key=lambda x: x[1], reverse=True)  # 按相似度排序
        return most_similar[:3]  # 返回 top 3
