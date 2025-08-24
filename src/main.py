from pathlib import Path
import json
from perspective_kb.data_helper import DataHelper
from perspective_kb.vector_db import LocalVectorDB
from perspective_kb.utils import get_logger, timer


@timer
def main():
    # 日志
    logger = get_logger()

    logger.info("Starting processing...")

    # 数据处理助手
    data_helper = DataHelper()

    # 创建本地向量数据库
    local_db = LocalVectorDB(db_path="milvus_lite.db")

    logger.info("Local vector DB initialized.\n")

    DATA_DIR = Path("data")

    # 1. 处理知识库
    perspective_dictionary = data_helper.load_data_from_directory(
        "knowledge",
        DATA_DIR / "canonical_perspectives/",
        local_db=local_db,
    )
    # print("perspective_dictionary: ", perspective_dictionary, "/n")

    # 创建 collection: knowledge
    local_db.create_collection(
        collection_name="knowledge", vector_dim=1024, use_flat=True
    )

    # 加入向量数据库
    local_db.upsert(
        entities=perspective_dictionary,
        collection_name="knowledge",
    )

    # 将列表写入 JSON 文件
    with open("data/processed/canonical_perspectives.json", "w", encoding="utf-8") as f:
        json.dump(perspective_dictionary, f, ensure_ascii=False, indent=2)

    # 2. 处理反馈
    feedback_corpus = data_helper.load_data_from_directory(
        "feedback",
        DATA_DIR / "user_feedbacks/",
        local_db=local_db,
    )

    # 创建 collection: feedback
    local_db.create_collection(
        collection_name="feedback", vector_dim=1024, use_flat=True
    )

    # 加入向量数据库
    local_db.upsert(
        entities=feedback_corpus,
        collection_name="knowledge",
    )
    # print("Collections: ", local_db.collections)
    # 将列表写入 JSON 文件
    with open("data/processed/user_feedback_corpus.json", "w", encoding="utf-8") as f:
        json.dump(feedback_corpus, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
