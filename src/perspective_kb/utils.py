"""
工具函数模块
"""
import logging
import time
import functools
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

import structlog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# 类型变量
T = TypeVar('T')

# 全局控制台实例
console = Console()


def timer(func: Callable[..., T]) -> Callable[..., T]:
    """函数执行时间装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start
        
        # 使用rich输出
        console.print(f"⏱️  [green]Function[/green] [bold]{func.__name__}[/bold] "
                     f"[yellow]executed in[/yellow] [bold]{duration:.4f}s[/bold]")
        return result
    return wrapper


def get_logger(name: str = "perspective_kb", 
               level: str = "INFO",
               log_file: Optional[Path] = None) -> structlog.BoundLogger:
    """获取结构化日志记录器"""
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 获取logger
    logger = structlog.get_logger(name)
    
    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # 添加文件处理器（如果指定）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        
        # 获取标准库logger并添加处理器
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.addHandler(file_handler)
        stdlib_logger.setLevel(numeric_level)
    
    return logger


def create_progress_bar(description: str = "Processing...") -> Progress:
    """创建进度条"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        description=description
    )


def display_table(data: list, title: str = "数据表", columns: Optional[list] = None) -> None:
    """显示数据表格"""
    if not data:
        console.print(Panel("暂无数据", title=title))
        return
    
    # 如果没有指定列，使用第一条数据的键
    if columns is None:
        columns = list(data[0].keys())
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    # 添加列
    for col in columns:
        table.add_column(col, style="cyan", no_wrap=True)
    
    # 添加行
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])
    
    console.print(table)


def display_summary(stats: dict, title: str = "处理摘要") -> None:
    """显示处理摘要"""
    content = []
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            content.append(f"{key}: [bold green]{value}[/bold green]")
        else:
            content.append(f"{key}: [bold blue]{value}[/bold blue]")
    
    panel = Panel("\n".join(content), title=title, border_style="green")
    console.print(panel)


def safe_operation(operation: Callable[..., T], 
                  error_msg: str = "操作失败",
                  default: Optional[T] = None) -> Optional[T]:
    """安全操作装饰器，捕获异常并返回默认值"""
    try:
        return operation()
    except Exception as e:
        console.print(f"[red]❌ {error_msg}: {e}[/red]")
        return default


def batch_process(items: list, 
                  processor: Callable[[Any], Any], 
                  batch_size: int = 100,
                  description: str = "批处理中...") -> list:
    """批处理函数"""
    results = []
    
    with create_progress_bar(description) as progress:
        task = progress.add_task(description, total=len(items))
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = [processor(item) for item in batch]
            results.extend(batch_results)
            
            progress.update(task, advance=len(batch))
    
    return results


def ensure_directory(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
