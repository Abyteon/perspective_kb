"""
主程序入口
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

from perspective_kb.config import settings
from perspective_kb.data_helper import DataHelper, DataProcessingError
from perspective_kb.vector_db import LocalVectorDB, VectorDBError
from perspective_kb.utils import (
    get_logger, 
    timer, 
    console, 
    display_summary, 
    ensure_directory,
    safe_operation
)


@timer
def main() -> bool:
    """
    主程序入口
    
    Returns:
        bool: 程序执行是否成功
    """
    # 初始化日志
    log_file = settings.log_file or Path("log/processing.log")
    logger = get_logger("main", level=settings.log_level, log_file=log_file)
    
    console.print("[bold blue]🚀 开始处理视角知识库数据...[/bold blue]\n")
    
    # 确保目录存在
    ensure_directory(settings.processed_dir)
    ensure_directory(log_file.parent)
    
    try:
        # 健康检查
        console.print("[yellow]🔍 检查系统状态...[/yellow]")
        
        # 创建本地向量数据库
        with LocalVectorDB() as local_db:
            # 健康检查
            if not local_db.health_check():
                console.print("[red]❌ 向量数据库健康检查失败[/red]")
                return False
            
            console.print("[green]✅ 向量数据库连接正常[/green]")
            
            # 数据处理助手
            data_helper = DataHelper()
            console.print("[green]✅ 数据处理助手初始化成功[/green]\n")
            
            # 处理统计
            stats = {
                "知识库记录数": 0,
                "反馈记录数": 0,
                "处理时间": 0,
                "状态": "成功"
            }
            
            # 1. 处理知识库
            console.print("[bold cyan]📚 处理标准视角知识库...[/bold cyan]")
            
            perspective_dictionary = safe_operation(
                lambda: data_helper.load_data_from_directory(
                    "knowledge",
                    settings.canonical_perspectives_dir,
                    local_db=local_db,
                ),
                "加载知识库数据失败",
                []
            )
            
            if not perspective_dictionary:
                console.print("[red]❌ 没有加载到知识库数据[/red]")
                return False
            
            stats["知识库记录数"] = len(perspective_dictionary)
            console.print(f"[green]✅ 知识库数据加载完成，共 {len(perspective_dictionary)} 条记录[/green]")
            
            # 创建知识库集合
            if local_db.create_collection(
                collection_name="knowledge", 
                vector_dim=settings.vector_dim, 
                use_flat=settings.use_flat_index
            ):
                console.print("[green]✅ 知识库集合创建成功[/green]")
            else:
                console.print("[red]❌ 知识库集合创建失败[/red]")
                return False
            
            # 插入知识库数据
            if local_db.upsert(
                entities=perspective_dictionary,
                collection_name="knowledge",
                batch_size=settings.batch_size
            ):
                console.print("[green]✅ 知识库数据插入成功[/green]")
            else:
                console.print("[red]❌ 知识库数据插入失败[/red]")
                return False
            
            # 保存处理后的知识库数据
            knowledge_output_file = settings.processed_dir / "canonical_perspectives.json"
            try:
                with open(knowledge_output_file, "w", encoding="utf-8") as f:
                    json.dump(perspective_dictionary, f, ensure_ascii=False, indent=2)
                console.print(f"[green]✅ 知识库数据已保存到: {knowledge_output_file}[/green]")
            except Exception as e:
                console.print(f"[red]❌ 保存知识库数据失败: {e}[/red]")
                logger.error("保存知识库数据失败", error=str(e))
            
            # 2. 处理用户反馈
            console.print("\n[bold cyan]💬 处理用户反馈数据...[/bold cyan]")
            
            feedback_corpus = safe_operation(
                lambda: data_helper.load_data_from_directory(
                    "feedback",
                    settings.user_feedbacks_dir,
                    local_db=local_db,
                ),
                "加载用户反馈数据失败",
                []
            )
            
            if not feedback_corpus:
                console.print("[red]❌ 没有加载到用户反馈数据[/red]")
                return False
            
            stats["反馈记录数"] = len(feedback_corpus)
            console.print(f"[green]✅ 用户反馈数据加载完成，共 {len(feedback_corpus)} 条记录[/green]")
            
            # 创建反馈集合
            if local_db.create_collection(
                collection_name="feedback", 
                vector_dim=settings.vector_dim, 
                use_flat=settings.use_flat_index
            ):
                console.print("[green]✅ 反馈集合创建成功[/green]")
            else:
                console.print("[red]❌ 反馈集合创建失败[/red]")
                return False
            
            # 插入反馈数据
            if local_db.upsert(
                entities=feedback_corpus,
                collection_name="feedback",
                batch_size=settings.batch_size
            ):
                console.print("[green]✅ 反馈数据插入成功[/green]")
            else:
                console.print("[red]❌ 反馈数据插入失败[/red]")
                return False
            
            # 保存处理后的反馈数据
            feedback_output_file = settings.processed_dir / "user_feedback_corpus.json"
            try:
                with open(feedback_output_file, "w", encoding="utf-8") as f:
                    json.dump(feedback_corpus, f, ensure_ascii=False, indent=2)
                console.print(f"[green]✅ 反馈数据已保存到: {feedback_output_file}[/green]")
            except Exception as e:
                console.print(f"[red]❌ 保存反馈数据失败: {e}[/red]")
                logger.error("保存反馈数据失败", error=str(e))
            
            # 3. 显示处理摘要
            console.print("\n[bold green]📊 处理完成！[/bold green]")
            
            # 获取集合统计信息
            knowledge_stats = local_db.get_collection_stats("knowledge")
            feedback_stats = local_db.get_collection_stats("feedback")
            
            if "error" not in knowledge_stats:
                stats["知识库向量数"] = knowledge_stats.get("row_count", 0)
            if "error" not in feedback_stats:
                stats["反馈向量数"] = feedback_stats.get("row_count", 0)
            
            display_summary(stats, "处理摘要")
            
            # 显示集合信息
            collections_info = {
                "知识库集合": knowledge_stats,
                "反馈集合": feedback_stats
            }
            
            for name, info in collections_info.items():
                if "error" not in info:
                    console.print(f"\n[bold]{name}:[/bold]")
                    console.print(f"  记录数: {info.get('row_count', 0)}")
                    console.print(f"  字段: {', '.join(info.get('fields', []))}")
                    console.print(f"  状态: {info.get('status', 'unknown')}")
                else:
                    console.print(f"\n[bold]{name}:[/bold] [red]{info['error']}[/red]")
            
            return True
            
    except VectorDBError as e:
        console.print(f"[red]❌ 向量数据库错误: {e}[/red]")
        logger.error("向量数据库错误", error=str(e))
        return False
        
    except DataProcessingError as e:
        console.print(f"[red]❌ 数据处理错误: {e}[/red]")
        logger.error("数据处理错误", error=str(e))
        return False
        
    except Exception as e:
        console.print(f"[red]❌ 程序执行出错: {e}[/red]")
        logger.error("程序执行出错", error=str(e))
        return False


if __name__ == "__main__":
    try:
        success = main()
        if success:
            console.print("\n[bold green]🎉 程序执行成功！[/bold green]")
            sys.exit(0)
        else:
            console.print("\n[bold red]💥 程序执行失败！[/bold red]")
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  程序被用户中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]💥 程序异常退出: {e}[/red]")
        sys.exit(1)
