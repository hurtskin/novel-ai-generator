"""
章节迭代器

实现章节的迭代功能，支持指定起始和结束章节
"""

from typing import Iterator


class ChapterIterator:
    """
    章节迭代器
    
    用于遍历章节范围，支持指定起始和结束章节
    
    Attributes:
        start: 起始章节ID
        end: 结束章节ID（不包含）
        current: 当前章节ID
    
    Example:
        >>> chapters = ChapterIterator(1, 5)
        >>> for chapter_id in chapters:
        ...     print(f"Processing chapter {chapter_id}")
    """
    
    def __init__(self, start: int, end: int):
        """
        初始化章节迭代器
        
        Args:
            start: 起始章节ID
            end: 结束章节ID（不包含）
            
        Raises:
            ValueError: 当 start >= end 时
        """
        if start >= end:
            raise ValueError(f"start ({start}) must be less than end ({end})")
        
        self.start: int = start
        self.end: int = end
        self.current: int = start
    
    def __iter__(self) -> "ChapterIterator":
        """返回迭代器对象"""
        return self
    
    def __next__(self) -> int:
        """
        获取下一个章节ID
        
        Returns:
            int: 下一个章节ID
            
        Raises:
            StopIteration: 当遍历结束时
        """
        if self.current >= self.end:
            raise StopIteration
        
        result = self.current
        self.current += 1
        return result
    
    def get_current(self) -> int:
        """获取当前章节ID"""
        return self.current
    
    def get_start(self) -> int:
        """获取起始章节ID"""
        return self.start
    
    def get_end(self) -> int:
        """获取结束章节ID"""
        return self.end
    
    def get_total_chapters(self) -> int:
        """获取章节总数"""
        return self.end - self.start
    
    def get_progress(self) -> float:
        """
        获取当前进度百分比
        
        Returns:
            float: 进度百分比（0.0 - 100.0）
        """
        if self.get_total_chapters() == 0:
            return 100.0
        completed = self.current - self.start
        return (completed / self.get_total_chapters()) * 100.0
    
    def is_finished(self) -> bool:
        """检查是否遍历完成"""
        return self.current >= self.end
    
    def reset(self) -> None:
        """重置迭代器状态"""
        self.current = self.start
    
    def skip_to(self, chapter_id: int) -> None:
        """
        跳转到指定章节
        
        Args:
            chapter_id: 目标章节ID
            
        Raises:
            ValueError: 当章节ID超出范围时
        """
        if chapter_id < self.start or chapter_id >= self.end:
            raise ValueError(
                f"Chapter ID {chapter_id} is out of range [{self.start}, {self.end})"
            )
        self.current = chapter_id
