"""
现代化命令行界面工具 - 2025年版本
支持丰富的交互、异步处理和详细的状态展示
"""
import asyncio
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import sys
from datetime import datetime

from .config import settings, LogLevel, VectorDBType
from .vector_db import get_vector_db, VectorDBError, SearchResult
from .data_helper import DataHelper, DataProcessingError
from .utils import (
    console, 
    display_table, 
    display_summary,
    ensure_directory,
    get_logger
)

app = typer.Typer(
    name="perspective_kb",
    help="🚀 现代化视角知识库管理系统 v2025",
    add_completion=False,
    rich_markup_mode="rich"
)


def version_callback(value: bool):
    """显示版本信息"""
    if value:
        console.print(f"[bold blue]{settings.app_name}[/bold blue] [green]v{settings.app_version}[/green]")
        console.print(f"Python向量知识库管理系统")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", 
        callback=version_callback, 
        is_eager=True,
        help="显示版本信息"
    ),
):
    """
    🚀 视角知识库管理系统
    
    现代化的向量数据库知识管理工具，支持：
    • 知识库向量化和存储
    • 智能语义搜索
    • 用户反馈分析
    • 多种数据库后端支持
    """
    pass


@app.command()
def process(
    force: bool = typer.Option(False, "--force", "-f", help="🔄 强制重新处理数据"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", "-b", help="📦 批处理大小"),
    max_workers: Optional[int] = typer.Option(None, "--max-workers", "-w", help="⚡ 最大工作线程数"),
    disable_cache: bool = typer.Option(False, "--no-cache", help="🚫 禁用嵌入缓存"),
    async_mode: bool = typer.Option(True, "--async/--sync", help="🔄 异步处理模式")
):
    """
    📚 处理视角知识库数据
    
    完整的数据处理流程：
    1. 加载原始数据
    2. 文本清理和向量化
    3. 创建向量数据库集合
    4. 批量插入数据
    5. 生成处理报告
    """
    if async_mode:
        # 异步模式 - 调用主程序
        import sys
        from pathlib import Path
        # 添加src目录到路径
        src_path = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(src_path))
        from main import run_main
        success = run_main()
        if not success:
            raise typer.Exit(1)
        return
    
    # 同步模式
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
        with get_vector_db() as local_db:
            # 健康检查
            if not local_db.health_check():
                console.print("[red]❌ 向量数据库健康检查失败[/red]")
                raise typer.Exit(1)
            
            # 数据处理助手
            data_helper = DataHelper(
                max_workers=settings.max_workers,
                enable_cache=not disable_cache
            )
            
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
            
            console.print(f"[green]✅ 用户反馈处理完成，共 {len(feedback_corpus)} 条记录[/green]")
            
            # 显示统计信息
            console.print("\n[bold green]📊 处理统计[/bold green]")
            stats = {
                "知识库记录数": len(perspective_dictionary),
                "反馈记录数": len(feedback_corpus),
                "批处理大小": settings.batch_size,
                "工作线程数": settings.max_workers,
                "缓存状态": "启用" if not disable_cache else "禁用"
            }
            display_summary(stats)
            
            # 显示嵌入统计
            if hasattr(data_helper, 'get_stats'):
                embedding_stats = data_helper.get_stats()
                console.print("\n[bold green]🧠 嵌入处理统计[/bold green]")
                display_summary(embedding_stats)
            
            console.print("\n[bold green]🎉 处理完成！[/bold green]")
            
    except VectorDBError as e:
        console.print(f"[red]❌ 向量数据库错误: {e}[/red]")
        raise typer.Exit(1)
    except DataProcessingError as e:
        console.print(f"[red]❌ 数据处理错误: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 系统错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="📊 显示详细状态信息"),
    json_output: bool = typer.Option(False, "--json", help="🔗 JSON格式输出")
):
    """
    🔍 检查系统状态
    
    显示系统各组件的运行状态：
    • 向量数据库连接状态
    • 集合统计信息
    • Ollama服务状态
    • 存储空间使用情况
    """
    if not json_output:
        console.print("[bold blue]🔍 检查系统状态...[/bold blue]\n")
    
    status_data = {
        "timestamp": datetime.now().isoformat(),
        "system_status": "unknown",
        "components": {}
    }
    
    try:
        with get_vector_db() as local_db:
            # 向量数据库状态
            db_healthy = local_db.health_check()
            status_data["components"]["vector_db"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "type": settings.vector_db_type.value,
                "uri": settings.get_database_uri()
            }
            
            if not json_output:
                if db_healthy:
                    console.print("[green]✅ 向量数据库连接正常[/green]")
                    console.print(f"   类型: {settings.vector_db_type.value}")
                    console.print(f"   地址: {settings.get_database_uri()}")
                else:
                    console.print("[red]❌ 向量数据库连接异常[/red]")
            
            # 获取集合列表
            collections = local_db.list_collections()
            collection_stats = []
            
            if collections:
                status_data["components"]["collections"] = {}
                if not json_output:
                    console.print(f"\n[green]✅ 发现 {len(collections)} 个集合[/green]")
                
                for collection in collections:
                    try:
                        info = local_db.get_collection_info(collection)
                        collection_data = {
                            "name": collection,
                            "row_count": info.row_count,
                            "status": info.status
                        }
                        
                        status_data["components"]["collections"][collection] = collection_data
                        collection_stats.append({
                            "集合名称": collection,
                            "记录数": info.row_count,
                            "状态": info.status
                        })
                        
                        if not json_output and not detailed:
                            console.print(f"  📊 {collection}: {info.row_count} 条记录")
                            
                    except Exception as e:
                        collection_data = {
                            "name": collection,
                            "error": str(e)
                        }
                        status_data["components"]["collections"][collection] = collection_data
                        
                        if not json_output:
                            console.print(f"  ❌ {collection}: {str(e)}")
                
                if detailed and not json_output:
                    console.print("\n[bold cyan]📋 详细集合信息[/bold cyan]")
                    display_table(collection_stats, "集合状态")
                    
            else:
                if not json_output:
                    console.print("\n[yellow]⚠️  没有找到任何集合[/yellow]")
                status_data["components"]["collections"] = {}
        
        # Ollama状态检查
        try:
            data_helper = DataHelper()
            test_embedding = data_helper.embed_text("测试连接")
            ollama_status = "healthy" if test_embedding else "unhealthy"
            
            status_data["components"]["ollama"] = {
                "status": ollama_status,
                "host": settings.ollama_host,
                "model": settings.embedding_model
            }
            
            if not json_output:
                if ollama_status == "healthy":
                    console.print(f"\n[green]✅ Ollama服务正常[/green]")
                    console.print(f"   地址: {settings.ollama_host}")
                    console.print(f"   模型: {settings.embedding_model}")
                else:
                    console.print(f"\n[red]❌ Ollama服务异常[/red]")
                    
        except Exception as e:
            status_data["components"]["ollama"] = {
                "status": "error",
                "error": str(e)
            }
            if not json_output:
                console.print(f"\n[red]❌ Ollama连接失败: {e}[/red]")
        
        # 整体状态评估
        all_healthy = (
            status_data["components"]["vector_db"]["status"] == "healthy" and
            status_data["components"]["ollama"]["status"] == "healthy"
        )
        status_data["system_status"] = "healthy" if all_healthy else "degraded"
        
        if json_output:
            console.print_json(data=status_data)
        else:
            overall_status = "正常" if all_healthy else "异常"
            console.print(f"\n[bold]系统整体状态: [green]{overall_status}[/green][/bold]")
            
    except Exception as e:
        status_data["system_status"] = "error"
        status_data["error"] = str(e)
        
        if json_output:
            console.print_json(data=status_data)
        else:
            console.print(f"[red]❌ 状态检查失败: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="🔍 搜索查询文本"),
    collection: str = typer.Option("knowledge", "--collection", "-c", help="📂 搜索的集合名称"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="📊 返回结果数量"),
    threshold: float = typer.Option(0.0, "--threshold", "-t", help="🎯 相似度阈值"),
    output_format: str = typer.Option("table", "--format", "-f", help="📋 输出格式 (table/json)")
):
    """
    🔍 智能语义搜索
    
    在向量数据库中进行语义搜索：
    • 支持自然语言查询
    • 智能相似度匹配
    • 多种输出格式
    • 可调节相似度阈值
    """
    console.print(f"[bold blue]🔍 在集合 '{collection}' 中搜索: [cyan]{query}[/cyan][/bold blue]\n")
    
    try:
        # 创建数据处理助手
        data_helper = DataHelper()
        
        # 向量化查询文本
        if collection == "knowledge":
            # 构造知识库查询格式
            query_text = f"查询: {query}"
        else:
            # 构造反馈查询格式
            query_text = f"用户反馈: {query}"
        
        console.print(f"[dim]正在向量化查询文本...[/dim]")
        embedding = data_helper.embed_text(query_text)
        if not embedding:
            console.print("[red]❌ 查询文本向量化失败[/red]")
            raise typer.Exit(1)
        
        # 执行搜索
        with get_vector_db() as local_db:
            results = local_db.search(collection, [embedding], top_k=top_k)
            
            if results and results[0]:
                # 过滤低于阈值的结果
                filtered_results = [r for r in results[0] if r.score >= threshold]
                
                if output_format == "json":
                    # JSON输出
                    json_results = {
                        "query": query,
                        "collection": collection,
                        "total_results": len(filtered_results),
                        "threshold": threshold,
                        "results": [r.to_dict() for r in filtered_results]
                    }
                    console.print_json(data=json_results)
                    
                else:
                    # 表格输出
                    console.print(f"[green]✅ 找到 {len(filtered_results)} 个结果[/green]")
                    if threshold > 0:
                        console.print(f"[dim]应用相似度阈值: {threshold}[/dim]")
                    console.print()
                    
                    table_data = []
                    for i, result in enumerate(filtered_results, 1):
                        if collection == "knowledge":
                            table_data.append({
                                "排名": i,
                                "ID": result.id,
                                "相似度": f"{result.score:.3f}",
                                "维度": result.metadata.get("aspect", "N/A"),
                                "观点": result.metadata.get("insight", "N/A")[:50] + "...",
                                "情感": result.metadata.get("sentiment", "N/A")
                            })
                        else:
                            table_data.append({
                                "排名": i,
                                "ID": result.id,
                                "相似度": f"{result.score:.3f}",
                                "反馈内容": result.metadata.get("raw_text", "N/A")[:60] + "...",
                                "匹配数": len(result.metadata.get("mapped_perspectives", []))
                            })
                    
                    if table_data:
                        display_table(table_data, f"搜索结果 - {collection}")
                        
                        # 显示详细信息（仅前3个结果）
                        for i, result in enumerate(filtered_results[:3], 1):
                            console.print(f"\n[bold cyan]详细信息 #{i}[/bold cyan]")
                            console.print(f"ID: {result.id}")
                            console.print(f"相似度: {result.score:.3f}")
                            console.print(f"距离: {result.distance:.3f}")
                            
                            if collection == "knowledge":
                                console.print(f"维度: {result.metadata.get('aspect', 'N/A')}")
                                console.print(f"观点: {result.metadata.get('insight', 'N/A')}")
                                console.print(f"情感: {result.metadata.get('sentiment', 'N/A')}")
                                if 'description' in result.metadata:
                                    console.print(f"描述: {result.metadata['description'][:100]}...")
                            else:
                                console.print(f"原文: {result.metadata.get('raw_text', 'N/A')[:150]}...")
                                if 'summary' in result.metadata:
                                    console.print(f"摘要: {result.metadata['summary'][:100]}...")
                                mapped = result.metadata.get('mapped_perspectives', [])
                                if mapped:
                                    console.print(f"匹配观点数: {len(mapped)}")
                    else:
                        console.print("[yellow]⚠️  没有满足阈值条件的结果[/yellow]")
            else:
                console.print("[yellow]⚠️  没有找到匹配的结果[/yellow]")
                
    except Exception as e:
        console.print(f"[red]❌ 搜索失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def collections(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="📊 显示详细信息")
):
    """
    📋 列出所有集合
    
    显示向量数据库中的所有集合及其统计信息：
    • 集合名称和记录数
    • 状态和健康信息
    • 索引配置详情
    """
    console.print("[bold blue]📋 集合列表[/bold blue]\n")
    
    try:
        with get_vector_db() as local_db:
            collections = local_db.list_collections()
            
            if collections:
                table_data = []
                for collection in collections:
                    try:
                        info = local_db.get_collection_info(collection)
                        row_data = {
                            "集合名称": collection,
                            "记录数": info.row_count,
                            "状态": info.status
                        }
                        
                        if detailed and info.index_info:
                            row_data["索引类型"] = info.index_info.get("index_type", "N/A")
                            row_data["相似度度量"] = info.index_info.get("metric_type", "N/A")
                        
                        table_data.append(row_data)
                        
                    except Exception as e:
                        table_data.append({
                            "集合名称": collection,
                            "记录数": "N/A",
                            "状态": f"error: {str(e)[:30]}..."
                        })
                
                display_table(table_data, "向量数据库集合")
                
                # 显示总结
                total_records = sum(
                    row.get("记录数", 0) for row in table_data 
                    if isinstance(row.get("记录数"), int)
                )
                healthy_collections = sum(
                    1 for row in table_data 
                    if row.get("状态") == "loaded"
                )
                
                console.print(f"\n[bold]总结:[/bold]")
                console.print(f"  集合总数: {len(collections)}")
                console.print(f"  健康集合: {healthy_collections}")
                console.print(f"  总记录数: {total_records}")
                
            else:
                console.print("[yellow]⚠️  没有找到任何集合[/yellow]")
                console.print("\n[dim]提示: 使用 'process' 命令创建集合并导入数据[/dim]")
                
    except Exception as e:
        console.print(f"[red]❌ 获取集合列表失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def clean(
    collection: str = typer.Argument(..., help="🗑️ 要删除的集合名称"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="✅ 确认删除")
):
    """
    🗑️ 删除集合
    
    删除指定的向量数据库集合及其所有数据。
    ⚠️ 此操作不可逆！
    """
    if not confirm:
        console.print(f"[red]⚠️  危险操作！这将删除集合 '{collection}' 及其所有数据[/red]")
        console.print(f"[dim]集合中可能包含宝贵的向量化数据，删除后需要重新处理[/dim]")
        confirm = typer.confirm("确认删除？")
    
    if not confirm:
        console.print("[yellow]🚫 操作已取消[/yellow]")
        return
    
    console.print(f"[bold blue]🗑️  删除集合 '{collection}'...[/bold blue]\n")
    
    try:
        with get_vector_db() as local_db:
            # 获取删除前的信息
            try:
                info = local_db.get_collection_info(collection)
                console.print(f"[yellow]即将删除:[/yellow]")
                console.print(f"  集合名称: {collection}")
                console.print(f"  记录数: {info.row_count}")
                console.print(f"  状态: {info.status}")
            except:
                pass
            
            if local_db.drop_collection(collection):
                console.print(f"[green]✅ 集合 '{collection}' 删除成功[/green]")
            else:
                console.print(f"[red]❌ 集合 '{collection}' 删除失败[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]❌ 删除集合失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    show_sensitive: bool = typer.Option(False, "--show-sensitive", help="🔐 显示敏感信息"),
    output_format: str = typer.Option("table", "--format", "-f", help="📋 输出格式 (table/json)")
):
    """
    ⚙️ 显示当前配置
    
    展示系统的完整配置信息：
    • 数据库连接设置
    • 模型和向量配置
    • 性能和安全参数
    • 文件路径配置
    """
    if output_format == "json":
        config_dict = settings.to_dict()
        if not show_sensitive:
            # 隐藏敏感信息
            sensitive_keys = ["milvus_password", "api_key"]
            for key in sensitive_keys:
                if key in config_dict and config_dict[key]:
                    config_dict[key] = "***"
        console.print_json(data=config_dict)
        return
    
    console.print("[bold blue]⚙️  当前配置[/bold blue]\n")
    
    # 基础配置
    basic_config = [
        {"配置项": "应用名称", "值": settings.app_name},
        {"配置项": "应用版本", "值": settings.app_version},
        {"配置项": "调试模式", "值": "是" if settings.debug else "否"},
    ]
    display_table(basic_config, "基础配置")
    
    # 数据库配置
    db_config = [
        {"配置项": "数据库类型", "值": settings.vector_db_type.value},
        {"配置项": "数据库路径", "值": settings.db_path},
        {"配置项": "使用服务器模式", "值": "是" if settings.milvus_use_server else "否"},
        {"配置项": "Milvus服务器", "值": f"{settings.milvus_host}:{settings.milvus_port}"},
        {"配置项": "Milvus用户名", "值": settings.milvus_username or "未设置"},
    ]
    
    if show_sensitive and settings.milvus_password:
        db_config.append({"配置项": "Milvus密码", "值": settings.milvus_password})
    else:
        db_config.append({"配置项": "Milvus密码", "值": "***" if settings.milvus_password else "未设置"})
    
    display_table(db_config, "数据库配置")
    
    # 模型配置
    model_config = [
        {"配置项": "Ollama地址", "值": settings.ollama_host},
        {"配置项": "Ollama超时", "值": f"{settings.ollama_timeout}秒"},
        {"配置项": "嵌入模型", "值": settings.embedding_model},
        {"配置项": "向量维度", "值": settings.vector_dim},
        {"配置项": "相似度度量", "值": settings.similarity_metric},
        {"配置项": "索引类型", "值": "FLAT" if settings.use_flat_index else "IVF_FLAT"},
        {"配置项": "返回结果数", "值": settings.top_k},
    ]
    display_table(model_config, "模型配置")
    
    # 性能配置
    performance_config = [
        {"配置项": "批处理大小", "值": settings.batch_size},
        {"配置项": "最大工作线程数", "值": settings.max_workers},
        {"配置项": "缓存大小", "值": settings.cache_size},
        {"配置项": "频率限制", "值": f"{settings.rate_limit}/分钟"},
    ]
    display_table(performance_config, "性能配置")
    
    # 路径配置
    path_config = [
        {"配置项": "数据目录", "值": str(settings.data_dir)},
        {"配置项": "知识库目录", "值": str(settings.canonical_perspectives_dir)},
        {"配置项": "反馈目录", "值": str(settings.user_feedbacks_dir)},
        {"配置项": "处理后目录", "值": str(settings.processed_dir)},
        {"配置项": "嵌入缓存目录", "值": str(settings.embeddings_dir)},
    ]
    display_table(path_config, "路径配置")
    
    # 日志配置
    log_config = [
        {"配置项": "日志级别", "值": settings.log_level.value},
        {"配置项": "日志文件", "值": str(settings.log_file) if settings.log_file else "未设置"},
        {"配置项": "日志轮转", "值": settings.log_rotation},
        {"配置项": "日志保留", "值": settings.log_retention},
    ]
    display_table(log_config, "日志配置")


@app.command()
def benchmark(
    test_size: int = typer.Option(100, "--size", "-s", help="🧪 测试数据大小"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="🔄 测试迭代次数")
):
    """
    🧪 性能基准测试
    
    测试系统各组件的性能：
    • 向量化速度测试
    • 数据库插入性能
    • 搜索响应时间
    • 内存使用情况
    """
    console.print(f"[bold blue]🧪 性能基准测试 (大小: {test_size}, 迭代: {iterations})[/bold blue]\n")
    
    try:
        import time
        import random
        import string
        
        # 生成测试数据
        def generate_test_text():
            length = random.randint(20, 200)
            return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
        
        test_texts = [generate_test_text() for _ in range(test_size)]
        
        # 初始化组件
        data_helper = DataHelper()
        
        results = {
            "embedding_times": [],
            "search_times": [],
            "total_time": 0
        }
        
        # 嵌入性能测试
        console.print("[cyan]🧠 测试嵌入性能...[/cyan]")
        start_time = time.time()
        
        for i in range(iterations):
            iteration_start = time.time()
            embeddings = data_helper.embed_batch(test_texts[:10], show_progress=False)
            iteration_time = time.time() - iteration_start
            results["embedding_times"].append(iteration_time)
            console.print(f"  迭代 {i+1}: {iteration_time:.3f}秒")
        
        # 搜索性能测试（如果有集合的话）
        try:
            with get_vector_db() as db:
                collections = db.list_collections()
                if "knowledge" in collections:
                    console.print("\n[cyan]🔍 测试搜索性能...[/cyan]")
                    test_embedding = data_helper.embed_text("测试查询")
                    
                    for i in range(iterations):
                        iteration_start = time.time()
                        db.search("knowledge", [test_embedding], top_k=5)
                        iteration_time = time.time() - iteration_start
                        results["search_times"].append(iteration_time)
                        console.print(f"  迭代 {i+1}: {iteration_time:.3f}秒")
                else:
                    console.print("\n[yellow]⚠️  没有找到知识库集合，跳过搜索测试[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ 搜索测试失败: {e}[/red]")
        
        results["total_time"] = time.time() - start_time
        
        # 显示结果
        console.print("\n[bold green]📊 基准测试结果[/bold green]")
        
        perf_data = []
        if results["embedding_times"]:
            avg_embedding = sum(results["embedding_times"]) / len(results["embedding_times"])
            perf_data.append({
                "测试项目": "嵌入生成",
                "平均时间": f"{avg_embedding:.3f}秒",
                "吞吐量": f"{10/avg_embedding:.1f} 文本/秒"
            })
        
        if results["search_times"]:
            avg_search = sum(results["search_times"]) / len(results["search_times"])
            perf_data.append({
                "测试项目": "向量搜索",
                "平均时间": f"{avg_search:.3f}秒",
                "吞吐量": f"{1/avg_search:.1f} 查询/秒"
            })
        
        perf_data.append({
            "测试项目": "总测试时间",
            "平均时间": f"{results['total_time']:.3f}秒",
            "吞吐量": "N/A"
        })
        
        display_table(perf_data, "性能基准")
        
        # 显示缓存统计
        if hasattr(data_helper, 'get_stats'):
            cache_stats = data_helper.get_stats()
            console.print("\n[bold cyan]💾 缓存统计[/bold cyan]")
            display_summary(cache_stats)
        
    except Exception as e:
        console.print(f"[red]❌ 基准测试失败: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()