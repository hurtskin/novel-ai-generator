"""
上下文管理模块

提供章节级别的上下文管理功能

模块结构：
- chapter_context: 章节上下文管理器

使用示例：
    from core.context import ChapterContext, ChapterContextData
    
    with ChapterContext(1) as ctx:
        print(ctx.get_chapter_id())
        print(ctx.get_config())
"""

from core.context.chapter_context import (
    ChapterContext,
    ChapterContextData,
    load_config,
    load_global_memory,
    save_global_memory,
    create_chapter_dir,
    cleanup_chapter_dir,
)

__all__ = [
    "ChapterContext",
    "ChapterContextData",
    "load_config",
    "load_global_memory",
    "save_global_memory",
    "create_chapter_dir",
    "cleanup_chapter_dir",
]
