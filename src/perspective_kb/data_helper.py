import os
import re
import json
import ollama
from pathlib import Path
from typing import List
from perspective_kb.utils import get_logger
from perspective_kb.vector_db import LocalVectorDB

logger = get_logger()


class DataHelper:
    def __init__(self):
        pass

    # -------------------------
    # 清理文本
    # -------------------------
    @staticmethod
    def clean_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\u4e00-\u9fff,.!?；]", "", text)  # 保留中英文、标点
        return text

    # -------------------------------------
    # 加载目录下的所有json文件到python列表
    # -------------------------------------
    # @staticmethod
    def load_data_from_directory(
        self, type: str, directory: Path, local_db: LocalVectorDB
    ) -> List[dict]:
        # 获取所有 JSON 文件
        json_files = directory.glob("*.json")
        data = []
        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                assert isinstance(
                    content, list
                ), f"文件 {json_file} 的内容必须是JSON列表"
                # 将内容添加到列表中
                data.extend(content)
        return self.build_dictionary(type, data, local_db)

    # -------------------------
    # 准备嵌入知识
    # -------------------------
    @staticmethod
    def build_knowledge_text(item: dict) -> str:
        examples = "；".join(item.get("examples", [])[:3])
        keywords = ", ".join(item.get("keywords", [])[:8])
        return (
            f"维度: {item['aspect']}\n"
            f"观点: {item['insight']}\n"
            f"情感: {item.get('sentiment','')}\n"
            f"描述: {item.get('description','')}\n"
            f"示例: {examples}\n"
            f"关键词: {keywords}"
        ).strip()

    # -------------------------
    # 准备嵌入用户反馈
    # -------------------------
    @staticmethod
    def build_feedback_text(raw_text: str, summary: str | None = None) -> str:
        if summary:
            return f"原文: {raw_text}\n摘要: {summary}"
        return f"原文: {raw_text}"

    # -------------------------
    # 文本向量化
    # -------------------------
    @staticmethod
    def embed(text: str) -> List[float]:
        """单条文本向量化"""

        vec: ollama.EmbedResponse = ollama.embed(
            # model="dengcao/bge-reranker-v2-m3:latest",
            model="mitoza/Qwen3-Embedding-0.6B:latest",
            input=text,
        )
        return vec["embeddings"][0]

    # -------------------------
    # 构建存入向量库的数据
    # -------------------------
    def build_dictionary(
        self, type: str, dictionary: List[dict], local_db: LocalVectorDB
    ) -> List[dict]:
        match type:
            case "knowledge":
                perspective_dictionary = []
                for item in dictionary:
                    text = self.build_knowledge_text(item)
                    vec = self.embed(text)
                    meta = {
                        "type": "knowledge",
                        "aspect": item["aspect"],
                        "insight": item["insight"],
                        "sentiment": item.get("sentiment", ""),
                        "status": item.get("status", "active"),
                    }
                    perspective_dictionary.append(
                        {
                            "id": item["insight_id"],
                            "vector": vec,
                            "text_for_embedding": text,
                            "metadata": meta,
                        }
                    )
                return perspective_dictionary

            case "feedback":
                feedback_corpus = []
                for fb in dictionary:
                    raw_text = fb["raw_text"]
                    summary = fb.get("summary")
                    text = self.build_feedback_text(self.clean_text(raw_text), summary)
                    vec = self.embed(text)
                    mapped = local_db.search("knowledge", [vec], top_k=5)

                    logger.info(f"原始反馈: {raw_text}")
                    logger.info(f"摘要: {summary}")
                    logger.info(f"匹配的观点（越靠前匹配度越高）: {mapped}\n")
                    meta = {
                        "type": "feedback",
                        "raw_text": raw_text,
                        "summary": summary,
                        "mapped_perspectives": mapped,
                        **fb,
                    }

                    feedback_corpus.append(
                        {
                            "id": fb["fb_id"],
                            "vector": vec,
                            "text_for_embedding": text,
                            "metadata": meta,
                        }
                    )
                return feedback_corpus
            case _:
                raise ValueError(f"Unknown dictionary type: {type}")
