"""
迭代器模块

提供章节和节点序列的迭代功能

模块结构：
- node_sequence: 节点序列迭代器
- chapter_iterator: 章节迭代器

使用示例：
    from core.iterators import NodeSequence, ChapterIterator
    
    # 节点序列迭代
    nodes = NodeSequence([{"id": 1}, {"id": 2}])
    for node in nodes:
        print(node)
    
    # 章节迭代
    chapters = ChapterIterator(1, 5)
    for chapter_id in chapters:
        print(f"Processing chapter {chapter_id}")
"""

from core.iterators.node_sequence import NodeSequence
from core.iterators.chapter_iterator import ChapterIterator

__all__ = [
    "NodeSequence",
    "ChapterIterator",
]
