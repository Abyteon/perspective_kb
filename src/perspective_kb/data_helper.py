"""
数据处理助手模块
"""
import re
import json
import ollama
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .config import settings
from .utils import get_logger, safe_operation
from .vector_db import LocalVectorDB, VectorDBError


class DataProcessingError(Exception):
    """数据处理异常"""
    pass


class DataHelper:
    """数据处理助手类"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化数据处理助手
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers or settings.max_workers
        self.logger = get_logger("data_helper")
        
        # 配置Ollama客户端
        try:
            ollama.set_host(settings.ollama_host)
            self.logger.info("Ollama客户端配置成功", host=settings.ollama_host)
        except Exception as e:
            self.logger.warning("Ollama客户端配置失败，使用默认配置", error=str(e))
    
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 去除首尾空白
        text = text.strip()
        
        # 合并多个空白字符
        text = re.sub(r"\s+", " ", text)
        
        # 保留中英文、数字、常用标点符号
        text = re.sub(r"[^\w\u4e00-\u9fff0-9,.!?；：""''（）【】]", "", text)
        
        return text
    
    def load_data_from_directory(self, 
                                data_type: str, 
                                directory: Path, 
                                local_db: LocalVectorDB) -> List[Dict[str, Any]]:
        """
        从目录加载所有JSON文件数据
        
        Args:
            data_type: 数据类型 ("knowledge" 或 "feedback")
            directory: 数据目录路径
            local_db: 向量数据库实例
            
        Returns:
            List[Dict]: 处理后的数据列表
            
        Raises:
            DataProcessingError: 数据处理失败时抛出
        """
        if not directory.exists():
            raise DataProcessingError(f"目录不存在: {directory}")
        
        try:
            # 获取所有JSON文件
            json_files = list(directory.glob("*.json"))
            if not json_files:
                self.logger.warning("目录中没有找到JSON文件", directory=str(directory))
                return []
            
            self.logger.info("开始加载数据", 
                           data_type=data_type,
                           file_count=len(json_files),
                           directory=str(directory))
            
            # 加载所有数据
            all_data = []
            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        content = json.load(f)
                    
                    if not isinstance(content, list):
                        self.logger.warning("文件内容不是JSON列表格式", 
                                          file=str(json_file))
                        continue
                    
                    all_data.extend(content)
                    self.logger.debug("文件加载成功", 
                                    file=str(json_file),
                                    record_count=len(content))
                    
                except Exception as e:
                    self.logger.error("加载文件失败", 
                                    file=str(json_file),
                                    error=str(e))
                    continue
            
            if not all_data:
                self.logger.warning("没有成功加载任何数据", data_type=data_type)
                return []
            
            self.logger.info("数据加载完成", 
                           data_type=data_type,
                           total_records=len(all_data))
            
            # 构建数据字典
            return self.build_dictionary(data_type, all_data, local_db)
            
        except Exception as e:
            self.logger.error("加载数据失败", 
                            data_type=data_type,
                            directory=str(directory),
                            error=str(e))
            raise DataProcessingError(f"加载数据失败: {e}")
    
    def build_knowledge_text(self, item: Dict[str, Any]) -> str:
        """
        构建知识文本用于嵌入
        
        Args:
            item: 知识项数据
            
        Returns:
            str: 构建的文本
        """
        try:
            aspect = item.get("aspect", "")
            insight = item.get("insight", "")
            sentiment = item.get("sentiment", "")
            description = item.get("description", "")
            
            # 处理示例，限制数量避免文本过长
            examples = item.get("examples", [])
            examples_text = "；".join(examples[:3]) if examples else ""
            
            # 处理关键词
            keywords = item.get("keywords", [])
            keywords_text = ", ".join(keywords[:8]) if keywords else ""
            
            # 构建文本
            text_parts = [
                f"维度: {aspect}" if aspect else "",
                f"观点: {insight}" if insight else "",
                f"情感: {sentiment}" if sentiment else "",
                f"描述: {description}" if description else "",
                f"示例: {examples_text}" if examples_text else "",
                f"关键词: {keywords_text}" if keywords_text else ""
            ]
            
            # 过滤空字符串并连接
            return "\n".join(part for part in text_parts if part)
            
        except Exception as e:
            self.logger.error("构建知识文本失败", item=item, error=str(e))
            return str(item.get("insight", ""))
    
    def build_feedback_text(self, 
                           raw_text: str, 
                           summary: Optional[str] = None) -> str:
        """
        构建反馈文本用于嵌入
        
        Args:
            raw_text: 原始反馈文本
            summary: 摘要文本
            
        Returns:
            str: 构建的文本
        """
        try:
            cleaned_raw = self.clean_text(raw_text)
            
            if summary:
                cleaned_summary = self.clean_text(summary)
                return f"原文: {cleaned_raw}\n摘要: {cleaned_summary}"
            
            return f"原文: {cleaned_raw}"
            
        except Exception as e:
            self.logger.error("构建反馈文本失败", 
                            raw_text=raw_text,
                            summary=summary,
                            error=str(e))
            return raw_text or ""
    
    def embed_text(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        文本向量化
        
        Args:
            text: 要向量化的文本
            retry_count: 重试次数
            
        Returns:
            Optional[List[float]]: 向量，失败时返回None
        """
        if not text or not text.strip():
            self.logger.warning("文本为空，跳过向量化")
            return None
        
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                response: ollama.EmbedResponse = ollama.embed(
                    model=settings.embedding_model,
                    input=text,
                )
                
                embedding_time = time.time() - start_time
                self.logger.debug("文本向量化成功", 
                                text_length=len(text),
                                embedding_time=f"{embedding_time:.3f}s")
                
                return response["embeddings"][0]
                
            except Exception as e:
                self.logger.warning(f"向量化失败 (尝试 {attempt + 1}/{retry_count})", 
                                  error=str(e),
                                  text_preview=text[:100])
                
                if attempt < retry_count - 1:
                    time.sleep(1)  # 等待1秒后重试
                else:
                    self.logger.error("文本向量化最终失败", 
                                    text_preview=text[:100],
                                    error=str(e))
                    return None
        
        return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            List[Optional[List[float]]]: 向量列表，失败时对应位置为None
        """
        if not texts:
            return []
        
        self.logger.info("开始批量向量化", text_count=len(texts))
        
        # 使用线程池并行处理
        embeddings = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self.embed_text, text): i 
                for i, text in enumerate(texts)
            }
            
            # 收集结果
            temp_embeddings = [None] * len(texts)
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    embedding = future.result()
                    temp_embeddings[index] = embedding
                except Exception as e:
                    self.logger.error("批量向量化中单个任务失败", 
                                    index=index,
                                    error=str(e))
                    temp_embeddings[index] = None
            
            embeddings = temp_embeddings
        
        success_count = sum(1 for emb in embeddings if emb is not None)
        self.logger.info("批量向量化完成", 
                        total_count=len(texts),
                        success_count=success_count,
                        failure_count=len(texts) - success_count)
        
        return embeddings
    
    def build_dictionary(self, 
                        data_type: str, 
                        data: List[Dict[str, Any]], 
                        local_db: LocalVectorDB) -> List[Dict[str, Any]]:
        """
        构建存入向量库的数据
        
        Args:
            data_type: 数据类型
            data: 原始数据列表
            local_db: 向量数据库实例
            
        Returns:
            List[Dict]: 处理后的数据列表
        """
        if not data:
            return []
        
        try:
            if data_type == "knowledge":
                return self._build_knowledge_dictionary(data)
            elif data_type == "feedback":
                return self._build_feedback_dictionary(data, local_db)
            else:
                raise DataProcessingError(f"未知的数据类型: {data_type}")
                
        except Exception as e:
            self.logger.error("构建数据字典失败", 
                            data_type=data_type,
                            error=str(e))
            raise DataProcessingError(f"构建数据字典失败: {e}")
    
    def _build_knowledge_dictionary(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建知识数据字典"""
        self.logger.info("开始构建知识数据字典", record_count=len(data))
        
        # 准备文本
        texts = []
        for item in data:
            text = self.build_knowledge_text(item)
            texts.append(text)
        
        # 批量向量化
        embeddings = self.embed_batch(texts)
        
        # 构建结果
        knowledge_dictionary = []
        for i, (item, embedding) in enumerate(zip(data, embeddings)):
            if embedding is None:
                self.logger.warning("跳过向量化失败的项", 
                                  item_id=item.get("insight_id", f"index_{i}"))
                continue
            
            meta = {
                "type": "knowledge",
                "aspect": item.get("aspect", ""),
                "insight": item.get("insight", ""),
                "sentiment": item.get("sentiment", ""),
                "status": item.get("status", "active"),
            }
            
            knowledge_dictionary.append({
                "id": item.get("insight_id", f"knowledge_{i}"),
                "vector": embedding,
                "text_for_embedding": texts[i],
                "metadata": meta,
            })
        
        self.logger.info("知识数据字典构建完成", 
                        input_count=len(data),
                        output_count=len(knowledge_dictionary))
        
        return knowledge_dictionary
    
    def _build_feedback_dictionary(self, 
                                  data: List[Dict[str, Any]], 
                                  local_db: LocalVectorDB) -> List[Dict[str, Any]]:
        """构建反馈数据字典"""
        self.logger.info("开始构建反馈数据字典", record_count=len(data))
        
        # 准备文本
        texts = []
        for item in data:
            raw_text = item.get("raw_text", "")
            summary = item.get("summary")
            text = self.build_feedback_text(raw_text, summary)
            texts.append(text)
        
        # 批量向量化
        embeddings = self.embed_batch(texts)
        
        # 构建结果
        feedback_corpus = []
        for i, (item, embedding) in enumerate(zip(data, embeddings)):
            if embedding is None:
                self.logger.warning("跳过向量化失败的项", 
                                  item_id=item.get("fb_id", f"index_{i}"))
                continue
            
            raw_text = item.get("raw_text", "")
            summary = item.get("summary")
            
            # 搜索匹配的观点
            try:
                mapped = local_db.search("knowledge", [embedding], top_k=5)
                if mapped and len(mapped) > 0 and len(mapped[0]) > 0:
                    mapped_perspectives = mapped[0]  # 取第一个查询结果
                else:
                    mapped_perspectives = []
            except Exception as e:
                self.logger.warning("搜索匹配观点失败", 
                                  item_id=item.get("fb_id", f"index_{i}"),
                                  error=str(e))
                mapped_perspectives = []
            
            # 记录匹配结果
            self.logger.info(f"原始反馈: {raw_text}")
            if summary:
                self.logger.info(f"摘要: {summary}")
            self.logger.info(f"匹配的观点（越靠前匹配度越高）: {mapped_perspectives}\n")
            
            meta = {
                "type": "feedback",
                "raw_text": raw_text,
                "summary": summary,
                "mapped_perspectives": mapped_perspectives,
                **item,
            }
            
            feedback_corpus.append({
                "id": item.get("fb_id", f"feedback_{i}"),
                "vector": embedding,
                "text_for_embedding": texts[i],
                "metadata": meta,
            })
        
        self.logger.info("反馈数据字典构建完成", 
                        input_count=len(data),
                        output_count=len(feedback_corpus))
        
        return feedback_corpus
