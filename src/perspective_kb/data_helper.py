"""
现代化数据处理助手模块 - 2025年版本
支持异步处理、缓存、重试机制和更好的错误处理
"""
import re
import json
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum
import time

import ollama
from tqdm import tqdm

from .config import settings
from .utils import get_logger, safe_operation
from .vector_db import BaseVectorDB, VectorDBError, SearchResult


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    status: ProcessingStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class EmbeddingCache:
    """嵌入缓存数据类"""
    text_hash: str
    embedding: List[float]
    model: str
    timestamp: float
    
    @classmethod
    def from_text(cls, text: str, embedding: List[float], model: str) -> 'EmbeddingCache':
        """从文本创建缓存对象"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return cls(
            text_hash=text_hash,
            embedding=embedding,
            model=model,
            timestamp=time.time()
        )


class DataProcessingError(Exception):
    """数据处理异常"""
    pass


class EmbeddingError(DataProcessingError):
    """嵌入生成异常"""
    pass


class DataHelper:
    """现代化数据处理助手类"""
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 enable_cache: bool = True,
                 cache_dir: Optional[Path] = None):
        """
        初始化数据处理助手
        
        Args:
            max_workers: 最大工作线程数
            enable_cache: 是否启用缓存
            cache_dir: 缓存目录
        """
        self.max_workers = max_workers or settings.max_workers
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir or settings.embeddings_dir
        self.logger = get_logger("DataHelper")
        
        # 初始化缓存
        self._embedding_cache: Dict[str, EmbeddingCache] = {}
        if self.enable_cache:
            self._load_cache()
        
        # 配置Ollama客户端
        self._setup_ollama_client()
        
        # 确保embedding_model属性存在
        if not hasattr(self, 'embedding_model'):
            self.embedding_model = settings.embedding_model
        
        # 性能统计
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "embeddings_generated": 0,
            "processing_time": 0.0,
            "errors": 0
        }
    
    def _setup_ollama_client(self) -> None:
        """设置Ollama客户端"""
        try:
            ollama_config = settings.get_ollama_config()
            self.ollama_client = ollama.Client(
                host=ollama_config["host"],
                timeout=ollama_config.get("timeout", 300)
            )
            self.embedding_model = ollama_config["model"]
            self.logger.info("Ollama客户端配置成功", 
                           host=ollama_config["host"],
                           model=self.embedding_model)
        except Exception as e:
            self.logger.warning("Ollama客户端配置失败，使用默认配置", error=str(e))
            self.ollama_client = ollama.Client()
            self.embedding_model = settings.embedding_model
    
    def _load_cache(self) -> None:
        """加载嵌入缓存"""
        try:
            cache_file = self.cache_dir / f"embeddings_{self.embedding_model.replace(':', '_')}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                for item in cache_data:
                    cache_obj = EmbeddingCache(**item)
                    self._embedding_cache[cache_obj.text_hash] = cache_obj
                    
                self.logger.info("嵌入缓存加载成功", 
                               cache_size=len(self._embedding_cache),
                               cache_file=str(cache_file))
        except Exception as e:
            self.logger.warning("加载嵌入缓存失败", error=str(e))
            self._embedding_cache = {}
    
    def _save_cache(self) -> None:
        """保存嵌入缓存"""
        if not self.enable_cache or not self._embedding_cache:
            return
            
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"embeddings_{self.embedding_model.replace(':', '_')}.json"
            
            cache_data = [asdict(cache_obj) for cache_obj in self._embedding_cache.values()]
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("嵌入缓存保存成功", 
                           cache_size=len(self._embedding_cache),
                           cache_file=str(cache_file))
        except Exception as e:
            self.logger.error("保存嵌入缓存失败", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "total_requests": total_requests,
            "avg_processing_time": self.stats["processing_time"] / max(1, self.stats["embeddings_generated"])
        }
    
    def clean_text(self, text: str) -> str:
        """
        高级文本清理
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        try:
            # 去除首尾空白
            text = text.strip()
            
            # 标准化空白字符
            text = re.sub(r'\s+', ' ', text)
            
            # 保留中英文、数字、常用标点符号和表情符号
            text = re.sub(r'[^\w\u4e00-\u9fff0-9\.,!?；：""''（）【】\\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
            
            # 处理重复标点
            text = re.sub(r'([,.!?；：])\1+', r'\1', text)
            
            # 最终清理
            text = text.strip()
            
            return text
            
        except Exception as e:
            self.logger.warning("文本清理失败", text_preview=text[:100], error=str(e))
            return text or ""
    
    def load_data_from_directory(self, 
                                data_type: str, 
                                directory: Path, 
                                local_db: BaseVectorDB) -> List[Dict[str, Any]]:
        """
        从目录加载数据，支持进度显示和错误恢复
        
        Args:
            data_type: 数据类型 ("knowledge" 或 "feedback")
            directory: 数据目录路径
            local_db: 向量数据库实例
            
        Returns:
            List[Dict]: 处理后的数据列表
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
            failed_files = []
            
            # 使用进度条
            with tqdm(json_files, desc=f"加载{data_type}数据", unit="file") as pbar:
                for json_file in pbar:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                            
                        if isinstance(file_data, list):
                            all_data.extend(file_data)
                            record_count = len(file_data)
                        else:
                            all_data.append(file_data)
                            record_count = 1
                        
                        pbar.set_postfix({"记录数": len(all_data)})
                        
                        self.logger.debug("文件加载成功", 
                                        file=str(json_file),
                                        record_count=record_count)
                        
                    except Exception as e:
                        failed_files.append((json_file, str(e)))
                        self.logger.error("文件加载失败", 
                                        file=str(json_file),
                                        error=str(e))
                        continue
            
            if failed_files:
                self.logger.warning("部分文件加载失败", 
                                  failed_count=len(failed_files),
                                  total_count=len(json_files))
            
            self.logger.info("数据加载完成", 
                           data_type=data_type,
                           total_records=len(all_data),
                           successful_files=len(json_files) - len(failed_files),
                           failed_files=len(failed_files))
            
            # 构建数据字典
            return self.build_dictionary(data_type, all_data, local_db)
            
        except Exception as e:
            self.logger.error("数据加载失败", 
                            data_type=data_type,
                            directory=str(directory),
                            error=str(e))
            raise DataProcessingError(f"加载数据失败: {e}")
    
    def build_knowledge_text(self, item: Dict[str, Any]) -> str:
        """
        构建知识文本，增强版本
        
        Args:
            item: 知识项数据
            
        Returns:
            str: 构建的文本
        """
        try:
            # 提取字段
            aspect = self.clean_text(item.get("aspect", ""))
            insight = self.clean_text(item.get("insight", ""))
            sentiment = self.clean_text(item.get("sentiment", ""))
            description = self.clean_text(item.get("description", ""))
            examples = item.get("examples", [])
            keywords = item.get("keywords", [])
            
            # 构建结构化文本
            text_parts = []
            
            if aspect:
                text_parts.append(f"维度：{aspect}")
            if insight:
                text_parts.append(f"观点：{insight}")
            if sentiment:
                text_parts.append(f"情感：{sentiment}")
            if description:
                text_parts.append(f"描述：{description}")
            
            # 处理例子
            if examples:
                cleaned_examples = [self.clean_text(ex) for ex in examples[:3] if ex]
                if cleaned_examples:
                    text_parts.append(f"例子：{' | '.join(cleaned_examples)}")
            
            # 处理关键词
            if keywords:
                cleaned_keywords = [self.clean_text(kw) for kw in keywords if kw]
                if cleaned_keywords:
                    text_parts.append(f"关键词：{' '.join(cleaned_keywords)}")
            
            result_text = " | ".join(text_parts)
            
            # 确保文本不为空
            if not result_text.strip():
                result_text = str(item.get("insight", item.get("aspect", "未知内容")))
            
            return result_text
            
        except Exception as e:
            self.logger.error("构建知识文本失败", 
                            item=item,
                            error=str(e))
            return str(item.get("insight", item.get("aspect", "处理失败")))
    
    def build_feedback_text(self, raw_text: str, summary: Optional[str] = None) -> str:
        """
        构建反馈文本，增强版本
        
        Args:
            raw_text: 原始文本
            summary: 摘要文本
            
        Returns:
            str: 构建的文本
        """
        try:
            cleaned_raw = self.clean_text(raw_text)
            
            if not cleaned_raw:
                return "空内容"
            
            if summary:
                cleaned_summary = self.clean_text(summary)
                if cleaned_summary:
                    return f"摘要：{cleaned_summary} | 原文：{cleaned_raw}"
            
            return f"用户反馈：{cleaned_raw}"
            
        except Exception as e:
            self.logger.error("构建反馈文本失败", 
                            raw_text=raw_text,
                            summary=summary,
                            error=str(e))
            return raw_text or "处理失败"
    
    def embed_text(self, text: str, retry_count: int = 3) -> Optional[List[float]]:
        """
        文本向量化，支持缓存和重试
        
        Args:
            text: 要向量化的文本
            retry_count: 重试次数
            
        Returns:
            Optional[List[float]]: 向量，失败时返回None
        """
        if not text or not text.strip():
            self.logger.warning("文本为空，跳过向量化")
            return None
        
        # 检查缓存
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if self.enable_cache and text_hash in self._embedding_cache:
            cache_obj = self._embedding_cache[text_hash]
            if cache_obj.model == self.embedding_model:
                self.stats["cache_hits"] += 1
                self.logger.debug("使用缓存嵌入", text_length=len(text))
                return cache_obj.embedding
        
        self.stats["cache_misses"] += 1
        
        # 生成嵌入
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                response = self.ollama_client.embed(
                    model=self.embedding_model,
                    input=text,
                )
                
                embedding_time = time.time() - start_time
                self.stats["processing_time"] += embedding_time
                self.stats["embeddings_generated"] += 1
                
                embedding = response["embeddings"][0]
                
                # 保存到缓存
                if self.enable_cache:
                    cache_obj = EmbeddingCache.from_text(text, embedding, self.embedding_model)
                    self._embedding_cache[text_hash] = cache_obj
                
                self.logger.debug("文本向量化成功", 
                                text_length=len(text),
                                embedding_dim=len(embedding),
                                embedding_time=f"{embedding_time:.3f}s",
                                attempt=attempt + 1)
                
                return embedding
                
            except Exception as e:
                self.stats["errors"] += 1
                self.logger.warning(f"向量化失败 (尝试 {attempt + 1}/{retry_count})", 
                                  error=str(e),
                                  text_preview=text[:100])
                
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    time.sleep(wait_time)
                else:
                    self.logger.error("文本向量化最终失败", 
                                    text_preview=text[:100],
                                    error=str(e))
                    raise EmbeddingError(f"向量化失败: {e}")
        
        return None
    
    def embed_batch(self, texts: List[str], show_progress: bool = True) -> List[Optional[List[float]]]:
        """
        批量文本向量化，支持并行处理和进度显示
        
        Args:
            texts: 文本列表
            show_progress: 是否显示进度条
            
        Returns:
            List[Optional[List[float]]]: 向量列表
        """
        if not texts:
            return []
        
        self.logger.info("开始批量向量化", text_count=len(texts))
        
        embeddings = [None] * len(texts)
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self.embed_text, text): i 
                for i, text in enumerate(texts)
            }
            
            # 收集结果，显示进度
            completed = 0
            progress_bar = tqdm(total=len(texts), desc="向量化进度", unit="text") if show_progress else None
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    embedding = future.result()
                    embeddings[index] = embedding
                except Exception as e:
                    self.logger.error("批量向量化中单个任务失败", 
                                    index=index,
                                    error=str(e))
                    embeddings[index] = None
                
                completed += 1
                if progress_bar:
                    progress_bar.update(1)
                    progress_bar.set_postfix({
                        "成功": sum(1 for e in embeddings[:completed] if e is not None),
                        "失败": sum(1 for e in embeddings[:completed] if e is None)
                    })
            
            if progress_bar:
                progress_bar.close()
        
        # 保存缓存
        if self.enable_cache:
            self._save_cache()
        
        success_count = sum(1 for emb in embeddings if emb is not None)
        self.logger.info("批量向量化完成", 
                        total_count=len(texts),
                        success_count=success_count,
                        failure_count=len(texts) - success_count)
        
        return embeddings
    
    def build_dictionary(self, 
                        data_type: str, 
                        data: List[Dict[str, Any]], 
                        local_db: BaseVectorDB) -> List[Dict[str, Any]]:
        """
        构建存入向量库的数据字典
        
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
        embeddings = self.embed_batch(texts, show_progress=True)
        
        # 构建结果
        knowledge_dictionary = []
        for i, (item, embedding) in enumerate(zip(data, embeddings)):
            if embedding is None:
                self.logger.warning("跳过向量化失败的项", 
                                  item_id=item.get("insight_id", f"index_{i}"))
                continue
            
            # 增强元数据
            meta = {
                "type": "knowledge",
                "aspect": item.get("aspect", ""),
                "insight": item.get("insight", ""),
                "sentiment": item.get("sentiment", ""),
                "status": item.get("status", "active"),
                "created_time": time.time(),
                "model": self.embedding_model,
                "text_length": len(texts[i]),
                "embedding_dim": len(embedding)
            }
            
            # 添加额外字段
            for key in ["description", "examples", "keywords", "confidence", "source"]:
                if key in item:
                    meta[key] = item[key]
            
            knowledge_dictionary.append({
                "id": str(item.get("insight_id", f"knowledge_{i}")),
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
                                  local_db: BaseVectorDB) -> List[Dict[str, Any]]:
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
        embeddings = self.embed_batch(texts, show_progress=True)
        
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
                search_results = local_db.search("knowledge", [embedding], top_k=5)
                if search_results and len(search_results) > 0:
                    mapped_perspectives = [
                        {
                            "id": result.id,
                            "score": result.score,
                            "insight": result.metadata.get("insight", ""),
                            "aspect": result.metadata.get("aspect", "")
                        }
                        for result in search_results[0]
                    ]
                else:
                    mapped_perspectives = []
            except Exception as e:
                self.logger.warning("搜索匹配观点失败", 
                                  item_id=item.get("fb_id", f"index_{i}"),
                                  error=str(e))
                mapped_perspectives = []
            
            # 记录匹配结果
            if mapped_perspectives:
                self.logger.info(f"反馈映射成功: {raw_text[:50]}... -> {len(mapped_perspectives)}个匹配观点")
            
            # 增强元数据
            meta = {
                "type": "feedback",
                "raw_text": raw_text,
                "summary": summary,
                "mapped_perspectives": mapped_perspectives,
                "created_time": time.time(),
                "model": self.embedding_model,
                "text_length": len(texts[i]),
                "embedding_dim": len(embedding),
                "match_count": len(mapped_perspectives)
            }
            
            # 添加原始数据的其他字段
            for key, value in item.items():
                if key not in ["raw_text", "summary"] and not key.startswith("_"):
                    meta[key] = value
            
            feedback_corpus.append({
                "id": str(item.get("fb_id", f"feedback_{i}")),
                "vector": embedding,
                "text_for_embedding": texts[i],
                "metadata": meta,
            })
        
        self.logger.info("反馈数据字典构建完成", 
                        input_count=len(data),
                        output_count=len(feedback_corpus))
        
        return feedback_corpus
    
    def __del__(self):
        """析构函数，保存缓存"""
        try:
            if hasattr(self, 'enable_cache') and self.enable_cache:
                self._save_cache()
        except:
            pass