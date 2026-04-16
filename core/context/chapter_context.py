"""
章节上下文管理器

实现章节级别的上下文管理，包括配置加载、记忆管理和资源清理
"""

import os
import json
import yaml
import shutil
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 配置数据
        
    Raises:
        FileNotFoundError: 当配置文件不存在时
        yaml.YAMLError: 当配置文件格式错误时
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_global_memory(memory_path: str = "global_memory.json") -> List[Dict[str, Any]]:
    """
    加载全局记忆
    
    Args:
        memory_path: 记忆文件路径
        
    Returns:
        List[Dict[str, Any]]: 全局记忆列表
    """
    memory_file = Path(memory_path)
    if memory_file.exists():
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to load global memory: {e}")
    return []


def save_global_memory(memory: List[Dict[str, Any]], memory_path: str = "global_memory.json") -> None:
    """
    保存全局记忆
    
    Args:
        memory: 全局记忆列表
        memory_path: 记忆文件路径
    """
    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def create_chapter_dir(chapter_id: int, base_dir: str = ".") -> str:
    """
    创建章节目录
    
    Args:
        chapter_id: 章节ID
        base_dir: 基础目录
        
    Returns:
        str: 章节目录路径
    """
    chapter_dir = Path(base_dir) / f"chapter_{chapter_id}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    return str(chapter_dir)


def cleanup_chapter_dir(chapter_dir: str) -> None:
    """
    清理章节目录
    
    Args:
        chapter_dir: 章节目录路径
    """
    dir_path = Path(chapter_dir)
    if dir_path.exists():
        shutil.rmtree(chapter_dir)
        logger.info(f"Cleaned up chapter directory: {chapter_dir}")


class ChapterContextData:
    """
    章节上下文数据
    
    封装章节处理过程中需要的所有数据
    
    Attributes:
        config: 全局配置
        global_memory: 全局记忆
        chapter_memory: 章节记忆
        chapter_dir: 章节目录路径
        chapter_id: 章节ID
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        global_memory: List[Dict[str, Any]],
        chapter_memory: Dict[str, Any],
        chapter_dir: str,
        chapter_id: int
    ):
        self.config = config
        self.global_memory = global_memory
        self.chapter_memory = chapter_memory
        self.chapter_dir = chapter_dir
        self.chapter_id = chapter_id
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
    
    def get_global_memory(self) -> List[Dict[str, Any]]:
        """获取全局记忆"""
        return self.global_memory
    
    def get_chapter_memory(self) -> Dict[str, Any]:
        """获取章节记忆"""
        return self.chapter_memory
    
    def get_chapter_dir(self) -> str:
        """获取章节目录"""
        return self.chapter_dir
    
    def get_chapter_id(self) -> int:
        """获取章节ID"""
        return self.chapter_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config": self.config,
            "global": self.global_memory,
            "chapter": self.chapter_memory,
            "chapter_dir": self.chapter_dir,
            "chapter_id": self.chapter_id
        }


@contextmanager
def ChapterContext(
    chapter_id: int,
    config_path: str = "config.yaml",
    memory_path: str = "global_memory.json",
    base_dir: str = "."
) -> Generator[ChapterContextData, None, None]:
    """
    章节上下文管理器
    
    提供章节级别的上下文管理，自动处理资源加载和清理
    
    Args:
        chapter_id: 章节ID
        config_path: 配置文件路径
        memory_path: 记忆文件路径
        base_dir: 基础目录
        
    Yields:
        ChapterContextData: 章节上下文数据
        
    Example:
        >>> with ChapterContext(1) as ctx:
        ...     print(ctx.get_chapter_id())
        ...     print(ctx.get_config())
    """
    # 加载配置和记忆
    config = load_config(config_path)
    global_mem = load_global_memory(memory_path)
    chapter_mem = {"characters": {}, "events": []}
    
    # 创建章节目录
    chapter_dir = create_chapter_dir(chapter_id, base_dir)
    
    # 创建上下文数据对象
    context_data = ChapterContextData(
        config=config,
        global_memory=global_mem,
        chapter_memory=chapter_mem,
        chapter_dir=chapter_dir,
        chapter_id=chapter_id
    )
    
    logger.info(f"Chapter context initialized for chapter {chapter_id}")
    
    try:
        yield context_data
    except Exception as e:
        logger.error(f"Error in chapter {chapter_id}: {e}")
        raise
    finally:
        # 保存全局记忆
        # TODO: 调用 memory_summarizer
        # summary = memory_summarizer(chapter_mem)
        # global_mem["recent_detailed"].append(summary)
        save_global_memory(global_mem, memory_path)
        
        # 清理章节目录
        cleanup_chapter_dir(chapter_dir)
        
        logger.info(f"Chapter context cleaned up for chapter {chapter_id}")
