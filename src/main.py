from logging import Logger
from pathlib import Path
from perspective_kb.data_helper import DataHelper
from perspective_kb.vector_db import LocalVectorDB
from perspective_kb.utils import get_logger
import warnings
import json

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")


def main():
    logger = get_logger()

    logger.info("Starting processing...")

    # 数据处理助手
    data_helper = DataHelper()

    # 创建本地向量数据库
    local_db = LocalVectorDB(db_path="milvus_lite.db")

    logger.info("Local vector DB initialized.\n")

    DATA_DIR = Path("data")

    # 1. 处理知识库
    dictionary = data_helper.load_json_list_from_directory(
        DATA_DIR / "perspective_dictionary/"
    )
    perspective_dictionary = []

    # 创建 collection: knowledge
    local_db.create_collection(
        collection_name="knowledge", vector_dim=1024, use_flat=True
    )
    for item in dictionary:
        text = data_helper.build_knowledge_text(item)
        vec = local_db.embed(text)
        doc_meta = {
            "type": "knowledge",
            "aspect": item["aspect"],
            "insight": item["insight"],
            "sentiment": item.get("sentiment", ""),
            "status": item.get("status", "active"),
        }
        perspective_dictionary.append(
            {
                "id": item["insight_id"],
                "vector": vec[0],
                "text_for_embedding": text,
                "metadata": doc_meta,
            }
        )
    # print("perspective_dictionary: ", perspective_dictionary, "/n")

    # 加入向量数据库
    local_db.upsert(
        entities=perspective_dictionary,
        collection_name="knowledge",
    )

    # local_db.client.load_collection(collection_name="knowledge")
    # 将列表写入 JSON 文件
    with open("data/processed/perspective_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(perspective_dictionary, f, ensure_ascii=False, indent=2)

    # 2. 处理反馈
    feedbacks = data_helper.load_json_list_from_directory(DATA_DIR / "feedback_raw/")
    feedback_corpus = []

    # 创建 collection: feedback
    local_db.create_collection(
        collection_name="feedback", vector_dim=1024, use_flat=True
    )
    # local_db.client.load_collection(collection_name="feedback")

    for fb in feedbacks:
        raw_text = fb["raw_text"]
        summary = fb.get("summary")
        text = data_helper.build_feedback_text(
            data_helper.clean_text(raw_text), summary
        )
        vec = local_db.embed(text)
        logger.info(text.replace("\n", "\n                                "))
        mapped = local_db.search("knowledge", vec, top_k=5)
        logger.info(f"Mapped perspectives: {mapped}\n")
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
                "vector": vec[0],
                "text_for_embedding": text,
                "metadata": meta,
            }
        )

    # print("feedback_corpus: ", feedback_corpus, "/n")

    # 加入向量数据库
    local_db.upsert(
        entities=feedback_corpus,
        collection_name="knowledge",
    )
    # 将列表写入 JSON 文件
    with open("data/processed/feedback_corpus.json", "w", encoding="utf-8") as f:
        json.dump(feedback_corpus, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
