import json
from pathlib import Path
from typing import List
import re


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
    @staticmethod
    def load_json_list_from_directory(directory: Path) -> List[dict]:
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
        return data

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
