from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
)
from typing import List
import ollama


class LocalVectorDB:
    def __init__(self, db_path: str):
        """
        db_path: 本地 Milvus Lite 文件路径
        """
        self.client = MilvusClient(uri=db_path)
        self.collections = {}  # {collection_name: schema_info}

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
                max_length=64,
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
            field_name="vector",  # 被索引的字段
            # 索引类型
            index_type=("FLAT" if use_flat else "IVF_FLAT"),
            index_name="vector_index",  # Name of the index to create
            metric_type="L2",  # Metric type used to measure similarity
            params={},  # No additional parameters required for FLAT
        )
        self.client.create_collection(
            collection_name=collection_name, schema=schema, index_params=index_params
        )
        # self.client.load_collection(collection_name)

        self.collections[collection_name] = fields

    def upsert(self, entities, collection_name: str):
        """
        插入或更新数据
        """
        self.client.upsert(collection_name, data=entities)
        self.client.flush(collection_name)
        self.client.load_collection(collection_name)

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
            out_fields=["id", "metadata"],
        )
        # print("Search results:", results)
        valid_match = []
        for hit in results[0]:
            valid_match.append((hit.id, (hit.distance + 1) / 2))  # 归一化到[0,1]

        valid_match.sort(key=lambda x: x[1], reverse=False)  # 按相似度排序
        # print(
        #     "valid_match:",
        #     valid_match[:3],
        #     "metadata: ",
        #     results[0][0].entity.get("metadata"),
        #     "\n",
        # )
        return valid_match[:3]  # 返回 top 3

    @staticmethod
    def embed(text: str) -> List[List[float]]:
        """单条文本向量化"""
        vec: ollama.EmbedResponse = ollama.embed(
            # model="dengcao/bge-reranker-v2-m3:latest",
            model="mitoza/Qwen3-Embedding-0.6B:latest",
            input=text,
        )
        # print("Vector dimension:", len(vec["embeddings"][0]))
        return vec["embeddings"]
