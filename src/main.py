"""
现代化主程序入口 - 2025年版本
支持异步处理、详细进度显示、错误恢复和性能监控
"""
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass

from perspective_kb.config import settings, LogLevel
from perspective_kb.data_helper import DataHelper, DataProcessingError
from perspective_kb.vector_db import get_vector_db, VectorDBError, BaseVectorDB
from perspective_kb.utils import (
    get_logger, 
    timer, 
    console, 
    display_summary, 
    display_table,
    ensure_directory,
    safe_operation
)


@dataclass
class ProcessingStats:
    """处理统计信息"""
    knowledge_records: int = 0
    feedback_records: int = 0
    processing_time: float = 0.0
    status: str = "unknown"
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "知识库记录数": self.knowledge_records,
            "反馈记录数": self.feedback_records,
            "处理时间": f"{self.processing_time:.2f}秒",
            "状态": self.status,
            "错误数量": len(self.errors)
        }


class PerspectiveKBProcessor:
    """视角知识库处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.logger = get_logger("PerspectiveKBProcessor")
        self.stats = ProcessingStats()
        self.start_time = None
        
    async def setup(self) -> None:
        """异步设置"""
        self.start_time = time.time()
        
        # 确保目录存在
        ensure_directory(settings.processed_dir)
        if settings.log_file:
            ensure_directory(settings.log_file.parent)
        
        console.print(f"[bold blue]🚀 {settings.app_name} v{settings.app_version}[/bold blue]")
        console.print(f"[blue]配置文件: 使用环境变量前缀 PKB_[/blue]")
        if settings.debug:
            console.print(f"[yellow]⚠️  调试模式已启用[/yellow]")
        console.print()
    
    async def health_check(self, db: BaseVectorDB) -> bool:
        """系统健康检查"""
        console.print("[yellow]🔍 执行系统健康检查...[/yellow]")
        
        # 检查向量数据库
        if not db.health_check():
            console.print("[red]❌ 向量数据库健康检查失败[/red]")
            return False
        console.print("[green]✅ 向量数据库连接正常[/green]")
        
        # 检查Ollama连接
        try:
            data_helper = DataHelper()
            # 尝试一个简单的嵌入测试
            test_embedding = data_helper.embed_text("测试连接")
            if test_embedding:
                console.print(f"[green]✅ Ollama连接正常 (模型: {data_helper.embedding_model})[/green]")
            else:
                console.print("[red]❌ Ollama嵌入测试失败[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Ollama连接失败: {e}[/red]")
            return False
        
        # 检查数据目录
        required_dirs = [
            settings.canonical_perspectives_dir,
            settings.user_feedbacks_dir
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                console.print(f"[red]❌ 必需目录不存在: {directory}[/red]")
                return False
            
            json_files = list(directory.glob("*.json"))
            if not json_files:
                console.print(f"[yellow]⚠️  目录中没有JSON文件: {directory}[/yellow]")
            else:
                console.print(f"[green]✅ 数据目录正常: {directory} ({len(json_files)}个文件)[/green]")
        
        console.print()
        return True
    
    async def process_knowledge_base(self, 
                                   data_helper: DataHelper, 
                                   db: BaseVectorDB) -> Optional[List[Dict[str, Any]]]:
        """处理知识库数据"""
        console.print("[bold cyan]📚 处理标准视角知识库...[/bold cyan]")
        
        try:
            # 加载知识库数据
            perspective_dictionary = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: data_helper.load_data_from_directory(
                    "knowledge",
                    settings.canonical_perspectives_dir,
                    db
                )
            )
            
            if not perspective_dictionary:
                console.print("[red]❌ 没有加载到知识库数据[/red]")
                self.stats.errors.append("知识库数据加载失败")
                return None
            
            self.stats.knowledge_records = len(perspective_dictionary)
            console.print(f"[green]✅ 知识库数据加载完成，共 {len(perspective_dictionary)} 条记录[/green]")
            
            # 创建知识库集合
            console.print("[cyan]创建知识库集合...[/cyan]")
            if db.create_collection(
                collection_name="knowledge", 
                vector_dim=settings.vector_dim,
                metric_type=settings.similarity_metric,
                index_type="FLAT" if settings.use_flat_index else "IVF_FLAT"
            ):
                console.print("[green]✅ 知识库集合创建成功[/green]")
            else:
                console.print("[red]❌ 知识库集合创建失败[/red]")
                self.stats.errors.append("知识库集合创建失败")
                return None
            
            # 插入知识库数据
            console.print("[cyan]插入知识库数据...[/cyan]")
            if db.upsert(
                entities=perspective_dictionary,
                collection_name="knowledge",
                batch_size=settings.batch_size
            ):
                console.print("[green]✅ 知识库数据插入成功[/green]")
            else:
                console.print("[red]❌ 知识库数据插入失败[/red]")
                self.stats.errors.append("知识库数据插入失败")
                return None
            
            return perspective_dictionary
            
        except Exception as e:
            error_msg = f"知识库处理失败: {e}"
            console.print(f"[red]❌ {error_msg}[/red]")
            self.stats.errors.append(error_msg)
            self.logger.error(error_msg, error=str(e))
            return None
    
    async def process_feedback_data(self, 
                                  data_helper: DataHelper, 
                                  db: BaseVectorDB) -> Optional[List[Dict[str, Any]]]:
        """处理用户反馈数据"""
        console.print("\n[bold cyan]💬 处理用户反馈数据...[/bold cyan]")
        
        try:
            # 加载用户反馈数据
            feedback_corpus = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: data_helper.load_data_from_directory(
                    "feedback",
                    settings.user_feedbacks_dir,
                    db
                )
            )
            
            if not feedback_corpus:
                console.print("[red]❌ 没有加载到用户反馈数据[/red]")
                self.stats.errors.append("用户反馈数据加载失败")
                return None
            
            self.stats.feedback_records = len(feedback_corpus)
            console.print(f"[green]✅ 用户反馈数据加载完成，共 {len(feedback_corpus)} 条记录[/green]")
            
            # 创建反馈集合
            console.print("[cyan]创建反馈集合...[/cyan]")
            if db.create_collection(
                collection_name="feedback", 
                vector_dim=settings.vector_dim,
                metric_type=settings.similarity_metric,
                index_type="FLAT" if settings.use_flat_index else "IVF_FLAT"
            ):
                console.print("[green]✅ 反馈集合创建成功[/green]")
            else:
                console.print("[red]❌ 反馈集合创建失败[/red]")
                self.stats.errors.append("反馈集合创建失败")
                return None
            
            # 插入反馈数据
            console.print("[cyan]插入反馈数据...[/cyan]")
            if db.upsert(
                entities=feedback_corpus,
                collection_name="feedback",
                batch_size=settings.batch_size
            ):
                console.print("[green]✅ 用户反馈数据插入成功[/green]")
            else:
                console.print("[red]❌ 用户反馈数据插入失败[/red]")
                self.stats.errors.append("用户反馈数据插入失败")
                return None
            
            return feedback_corpus
            
        except Exception as e:
            error_msg = f"反馈数据处理失败: {e}"
            console.print(f"[red]❌ {error_msg}[/red]")
            self.stats.errors.append(error_msg)
            self.logger.error(error_msg, error=str(e))
            return None
    
    async def save_processed_data(self, 
                                perspective_dictionary: Optional[List[Dict[str, Any]]],
                                feedback_corpus: Optional[List[Dict[str, Any]]]) -> bool:
        """保存处理后的数据"""
        console.print("\n[bold cyan]💾 保存处理后的数据...[/bold cyan]")
        
        try:
            saved_files = []
            
            # 保存知识库数据
            if perspective_dictionary:
                knowledge_output_file = settings.processed_dir / "canonical_perspectives.json"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._save_json_file(knowledge_output_file, perspective_dictionary)
                )
                console.print(f"[green]✅ 知识库数据已保存到 {knowledge_output_file}[/green]")
                saved_files.append(str(knowledge_output_file))
            
            # 保存反馈数据
            if feedback_corpus:
                feedback_output_file = settings.processed_dir / "user_feedback_corpus.json"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._save_json_file(feedback_output_file, feedback_corpus)
                )
                console.print(f"[green]✅ 反馈数据已保存到 {feedback_output_file}[/green]")
                saved_files.append(str(feedback_output_file))
            
            # 保存处理统计信息
            stats_file = settings.processed_dir / "processing_stats.json"
            stats_data = {
                "timestamp": time.time(),
                "processing_stats": self.stats.to_dict(),
                "settings": {
                    "embedding_model": settings.embedding_model,
                    "vector_dim": settings.vector_dim,
                    "similarity_metric": settings.similarity_metric,
                    "batch_size": settings.batch_size
                },
                "saved_files": saved_files
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._save_json_file(stats_file, stats_data)
            )
            console.print(f"[green]✅ 处理统计信息已保存到 {stats_file}[/green]")
            
            return True
            
        except Exception as e:
            error_msg = f"保存数据失败: {e}"
            console.print(f"[red]❌ {error_msg}[/red]")
            self.stats.errors.append(error_msg)
            self.logger.error(error_msg, error=str(e))
            return False
    
    def _save_json_file(self, file_path: Path, data: Any) -> None:
        """保存JSON文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def display_final_summary(self, 
                                  db: BaseVectorDB, 
                                  data_helper: DataHelper) -> None:
        """显示最终摘要"""
        console.print("\n[bold green]📊 处理摘要[/bold green]")
        
        # 计算总处理时间
        if self.start_time:
            self.stats.processing_time = time.time() - self.start_time
        
        # 确定状态
        if not self.stats.errors:
            self.stats.status = "成功"
        elif self.stats.knowledge_records > 0 or self.stats.feedback_records > 0:
            self.stats.status = "部分成功"
        else:
            self.stats.status = "失败"
        
        # 显示基本统计
        display_summary(self.stats.to_dict())
        
        # 显示嵌入处理统计
        if hasattr(data_helper, 'get_stats'):
            embedding_stats = data_helper.get_stats()
            console.print("\n[bold green]🧠 嵌入处理统计[/bold green]")
            stats_data = [
                {"指标": "缓存命中率", "值": embedding_stats.get("cache_hit_rate", "0%")},
                {"指标": "总请求数", "值": embedding_stats.get("total_requests", 0)},
                {"指标": "生成嵌入数", "值": embedding_stats.get("embeddings_generated", 0)},
                {"指标": "平均处理时间", "值": f"{embedding_stats.get('avg_processing_time', 0):.3f}秒"},
                {"指标": "错误数", "值": embedding_stats.get("errors", 0)}
            ]
            display_table(stats_data, "嵌入处理性能")
        
        # 显示集合统计信息
        console.print("\n[bold green]📈 集合统计信息[/bold green]")
        
        collections = ["knowledge", "feedback"]
        collection_stats = []
        
        for collection_name in collections:
            try:
                info = db.get_collection_info(collection_name)
                collection_stats.append({
                    "集合名称": collection_name,
                    "记录数": info.row_count,
                    "状态": info.status
                })
            except Exception as e:
                collection_stats.append({
                    "集合名称": collection_name,
                    "记录数": 0,
                    "状态": f"错误: {e}"
                })
        
        display_table(collection_stats, "向量数据库集合统计")
        
        # 显示错误信息
        if self.stats.errors:
            console.print("\n[bold red]❌ 处理过程中的错误[/bold red]")
            for i, error in enumerate(self.stats.errors, 1):
                console.print(f"[red]{i}. {error}[/red]")
        
        # 最终状态
        if self.stats.status == "成功":
            console.print("\n[bold green]🎉 所有数据处理完成！[/bold green]")
        elif self.stats.status == "部分成功":
            console.print("\n[bold yellow]⚠️  部分数据处理完成，请查看错误信息[/bold yellow]")
        else:
            console.print("\n[bold red]💥 数据处理失败，请查看错误信息[/bold red]")


@timer
async def main() -> bool:
    """
    异步主程序入口
    
    Returns:
        bool: 程序执行是否成功
    """
    # 初始化处理器
    processor = PerspectiveKBProcessor()
    
    try:
        # 设置
        await processor.setup()
        
        # 创建向量数据库连接
        console.print("[yellow]🔧 初始化向量数据库连接...[/yellow]")
        db = get_vector_db()
        
        # 健康检查
        if not await processor.health_check(db):
            return False
        
        # 初始化数据处理助手
        console.print("[yellow]🛠️  初始化数据处理助手...[/yellow]")
        data_helper = DataHelper(
            max_workers=settings.max_workers,
            enable_cache=True
        )
        console.print("[green]✅ 数据处理助手初始化成功[/green]\n")
        
        # 处理知识库
        perspective_dictionary = await processor.process_knowledge_base(data_helper, db)
        
        # 处理用户反馈
        feedback_corpus = await processor.process_feedback_data(data_helper, db)
        
        # 保存处理后的数据
        await processor.save_processed_data(perspective_dictionary, feedback_corpus)
        
        # 显示最终摘要
        await processor.display_final_summary(db, data_helper)
        
        # 关闭数据库连接
        db.close()
        
        return processor.stats.status in ["成功", "部分成功"]
        
    except VectorDBError as e:
        console.print(f"[red]❌ 向量数据库错误: {e}[/red]")
        processor.logger.error("向量数据库操作失败", error=str(e))
        return False
        
    except DataProcessingError as e:
        console.print(f"[red]❌ 数据处理错误: {e}[/red]")
        processor.logger.error("数据处理失败", error=str(e))
        return False
        
    except Exception as e:
        console.print(f"[red]❌ 系统错误: {e}[/red]")
        processor.logger.error("系统运行失败", error=str(e))
        return False


def run_main() -> bool:
    """运行主程序的同步包装器"""
    try:
        # 在Windows上可能需要设置事件循环策略
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        return asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  用户中断操作[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[red]❌ 程序异常退出: {e}[/red]")
        return False


if __name__ == "__main__":
    try:
        success = run_main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  用户中断操作[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ 程序异常退出: {e}[/red]")
        sys.exit(1)