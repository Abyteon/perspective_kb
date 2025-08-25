"""
命令行界面工具
"""
import typer
from pathlib import Path
from typing import Optional, List
import json

from .config import settings
from .vector_db import LocalVectorDB, VectorDBError
from .data_helper import DataHelper, DataProcessingError
from .utils import (
    console, 
    display_table, 
    display_summary,
    ensure_directory
)

app = typer.Typer(
    name="perspective_kb",
    help="视角知识库管理系统",
    add_completion=False
)




@app.command()
def process(
    force: bool = typer.Option(False, "--force", "-f", help="强制重新处理数据"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", "-b", help="批处理大小"),
    max_workers: Optional[int] = typer.Option(None, "--max-workers", "-w", help="最大工作线程数")
):
    """处理视角知识库数据"""
    console.print("[bold blue]🚀 开始处理视角知识库数据...[/bold blue]\n")
    
    try:
        # 更新配置
        if batch_size:
            settings.batch_size = batch_size
        if max_workers:
            settings.max_workers = max_workers
        
        # 确保目录存在
        ensure_directory(settings.processed_dir)
        
        # 创建向量数据库连接
        with LocalVectorDB() as local_db:
            # 健康检查
            if not local_db.health_check():
                console.print("[red]❌ 向量数据库健康检查失败[/red]")
                raise typer.Exit(1)
            
            # 数据处理助手
            data_helper = DataHelper(max_workers=settings.max_workers)
            
            # 处理知识库
            console.print("[bold cyan]📚 处理标准视角知识库...[/bold cyan]")
            
            if force and local_db.client.has_collection("knowledge"):
                local_db.drop_collection("knowledge")
                console.print("[yellow]⚠️  已删除现有知识库集合[/yellow]")
            
            perspective_dictionary = data_helper.load_data_from_directory(
                "knowledge",
                settings.canonical_perspectives_dir,
                local_db=local_db,
            )
            
            if not perspective_dictionary:
                console.print("[red]❌ 没有加载到知识库数据[/red]")
                raise typer.Exit(1)
            
            # 创建集合并插入数据
            local_db.create_collection("knowledge", force_recreate=force)
            local_db.upsert(perspective_dictionary, "knowledge")
            
            # 保存处理后的数据
            knowledge_output_file = settings.processed_dir / "canonical_perspectives.json"
            with open(knowledge_output_file, "w", encoding="utf-8") as f:
                json.dump(perspective_dictionary, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ 知识库处理完成，共 {len(perspective_dictionary)} 条记录[/green]")
            
            # 处理用户反馈
            console.print("\n[bold cyan]💬 处理用户反馈数据...[/bold cyan]")
            
            if force and local_db.client.has_collection("feedback"):
                local_db.drop_collection("feedback")
                console.print("[yellow]⚠️  已删除现有反馈集合[/yellow]")
            
            feedback_corpus = data_helper.load_data_from_directory(
                "feedback",
                settings.user_feedbacks_dir,
                local_db=local_db,
            )
            
            if not feedback_corpus:
                console.print("[red]❌ 没有加载到用户反馈数据[/red]")
                raise typer.Exit(1)
            
            # 创建集合并插入数据
            local_db.create_collection("feedback", force_recreate=force)
            local_db.upsert(feedback_corpus, "feedback")
            
            # 保存处理后的数据
            feedback_output_file = settings.processed_dir / "user_feedback_corpus.json"
            with open(feedback_output_file, "w", encoding="utf-8") as f:
                json.dump(feedback_corpus, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ 反馈数据处理完成，共 {len(feedback_corpus)} 条记录[/green]")
            
            # 显示摘要
            stats = {
                "知识库记录数": len(perspective_dictionary),
                "反馈记录数": len(feedback_corpus),
                "批处理大小": settings.batch_size,
                "最大工作线程数": settings.max_workers
            }
            
            console.print("\n[bold green]📊 处理完成！[/bold green]")
            display_summary(stats, "处理摘要")
            
    except (VectorDBError, DataProcessingError) as e:
        console.print(f"[red]❌ 处理失败: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 程序执行出错: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """显示系统状态"""
    console.print("[bold blue]🔍 系统状态检查...[/bold blue]\n")
    
    try:
        with LocalVectorDB() as local_db:
            # 健康检查
            if local_db.health_check():
                console.print("[green]✅ 向量数据库: 正常[/green]")
            else:
                console.print("[red]❌ 向量数据库: 异常[/red]")
                raise typer.Exit(1)
            
            # 获取集合列表
            collections = local_db.list_collections()
            if collections:
                console.print(f"\n[bold]集合列表:[/bold]")
                for collection_name in collections:
                    stats = local_db.get_collection_stats(collection_name)
                    if "error" not in stats:
                        console.print(f"  📊 {collection_name}: {stats.get('row_count', 0)} 条记录")
                    else:
                        console.print(f"  ❌ {collection_name}: {stats['error']}")
            else:
                console.print("\n[yellow]⚠️  没有找到任何集合[/yellow]")
            
            # 配置信息
            console.print(f"\n[bold]配置信息:[/bold]")
            console.print(f"  数据库路径: {settings.db_path}")
            console.print(f"  向量维度: {settings.vector_dim}")
            console.print(f"  批处理大小: {settings.batch_size}")
            console.print(f"  最大工作线程数: {settings.max_workers}")
            console.print(f"  Ollama地址: {settings.ollama_host}")
            console.print(f"  嵌入模型: {settings.embedding_model}")
            
    except Exception as e:
        console.print(f"[red]❌ 状态检查失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索查询文本"),
    collection: str = typer.Option("knowledge", "--collection", "-c", help="搜索的集合名称"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="返回结果数量")
):
    """搜索向量数据库"""
    console.print(f"[bold blue]🔍 搜索集合 '{collection}'...[/bold blue]\n")
    
    try:
        with LocalVectorDB() as local_db:
            # 检查集合是否存在
            if not local_db.client.has_collection(collection):
                console.print(f"[red]❌ 集合 '{collection}' 不存在[/red]")
                raise typer.Exit(1)
            
            # 文本向量化
            data_helper = DataHelper()
            embedding = data_helper.embed_text(query)
            
            if embedding is None:
                console.print("[red]❌ 文本向量化失败[/red]")
                raise typer.Exit(1)
            
            # 搜索
            results = local_db.search(collection, [embedding], top_k=top_k)
            
            if not results or not results[0]:
                console.print("[yellow]⚠️  没有找到匹配的结果[/yellow]")
                return
            
            # 显示结果
            console.print(f"[green]✅ 找到 {len(results[0])} 个匹配结果:[/green]\n")
            
            for i, (id_, score, entity) in enumerate(results[0], 1):
                console.print(f"[bold cyan]{i}. ID: {id_}[/bold cyan]")
                console.print(f"   相似度: {score:.4f}")
                
                if entity and "metadata" in entity:
                    metadata = entity["metadata"]
                    if "insight" in metadata:
                        console.print(f"   观点: {metadata['insight']}")
                    if "aspect" in metadata:
                        console.print(f"   维度: {metadata['aspect']}")
                    if "sentiment" in metadata:
                        console.print(f"   情感: {metadata['sentiment']}")
                
                console.print()
            
    except Exception as e:
        console.print(f"[red]❌ 搜索失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def collections():
    """列出所有集合的详细信息"""
    console.print("[bold blue]📊 集合详细信息...[/bold blue]\n")
    
    try:
        with LocalVectorDB() as local_db:
            collections = local_db.list_collections()
            
            if not collections:
                console.print("[yellow]⚠️  没有找到任何集合[/yellow]")
                return
            
            for collection_name in collections:
                console.print(f"[bold cyan]集合: {collection_name}[/bold cyan]")
                
                stats = local_db.get_collection_stats(collection_name)
                if "error" not in stats:
                    console.print(f"  记录数: {stats.get('row_count', 0)}")
                    console.print(f"  字段: {', '.join(stats.get('fields', []))}")
                    console.print(f"  状态: {stats.get('status', 'unknown')}")
                else:
                    console.print(f"  ❌ 错误: {stats['error']}")
                
                console.print()
                
    except Exception as e:
        console.print(f"[red]❌ 获取集合信息失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def clean(
    collection: str = typer.Argument(..., help="要清理的集合名称"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="确认删除")
):
    """清理指定的集合"""
    if not confirm:
        console.print(f"[red]⚠️  危险操作！这将删除集合 '{collection}' 的所有数据[/red]")
        console.print("使用 --confirm 或 -y 参数确认操作")
        raise typer.Exit(1)
    
    console.print(f"[bold red]🗑️  清理集合 '{collection}'...[/bold red]\n")
    
    try:
        with LocalVectorDB() as local_db:
            if local_db.drop_collection(collection):
                console.print(f"[green]✅ 集合 '{collection}' 已成功删除[/green]")
            else:
                console.print(f"[red]❌ 删除集合 '{collection}' 失败[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]❌ 清理失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config():
    """显示当前配置"""
    console.print("[bold blue]⚙️  当前配置...[/bold blue]\n")
    
    config_data = [
        {"配置项": "数据库路径", "值": settings.db_path},
        {"配置项": "向量维度", "值": settings.vector_dim},
        {"配置项": "使用FLAT索引", "值": settings.use_flat_index},
        {"配置项": "批处理大小", "值": settings.batch_size},
        {"配置项": "最大工作线程数", "值": settings.max_workers},
        {"配置项": "Ollama地址", "值": settings.ollama_host},
        {"配置项": "嵌入模型", "值": settings.embedding_model},
        {"配置项": "日志级别", "值": settings.log_level},
        {"配置项": "数据目录", "值": str(settings.data_dir)},
        {"配置项": "处理后数据目录", "值": str(settings.processed_dir)},
    ]
    
    display_table(config_data, "配置信息")


if __name__ == "__main__":
    app()
