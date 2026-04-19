"""
文件输出服务实现

实现 FileOutputService 接口，管理输出文件的创建、追加和保存
"""

import os
import logging
import aiofiles
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from services.interfaces import FileOutputService, FileOutputResult

logger = logging.getLogger(__name__)


class FileOutputManager(FileOutputService):
    """
    文件输出管理器
    
    职责：
    - 管理输出文件创建和写入
    - 支持实时追加和最终保存
    - 管理文件命名和路径
    
    Attributes:
        output_dir: 输出目录路径
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        初始化文件输出管理器
        
        Args:
            output_dir: 输出目录路径，默认为 ./output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileOutputManager initialized, output directory: {self.output_dir.absolute()}")
    
    def create_output_file(self, task_id: str) -> str:
        """
        创建输出文件
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"novel_{task_id}_{timestamp}.txt"
        file_path = self.output_dir / filename
        
        # 创建空文件
        file_path.touch(exist_ok=True)
        logger.info(f"Created output file: {file_path}")
        
        return str(file_path)
    
    async def append_content(
        self,
        file_path: str,
        content: str,
    ) -> FileOutputResult:
        """
        追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 内容
            
        Returns:
            FileOutputResult: 操作结果
        """
        try:
            path = Path(file_path)
            
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 异步追加写入
            async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                await f.write(content)
                await f.write("\n\n")  # 添加分隔
            
            # 获取文件大小
            file_size = path.stat().st_size
            
            logger.debug(f"Appended {len(content)} chars to {file_path}, total size: {file_size} bytes")
            
            return FileOutputResult(
                success=True,
                file_path=file_path,
                bytes_written=len(content.encode("utf-8")),
                message=f"Successfully appended {len(content)} characters",
            )
            
        except Exception as e:
            logger.error(f"Failed to append content to {file_path}: {e}")
            return FileOutputResult(
                success=False,
                file_path=file_path,
                bytes_written=0,
                message=f"Error: {str(e)}",
            )
    
    async def save_final(
        self,
        file_path: str,
        content: str,
    ) -> FileOutputResult:
        """
        保存最终内容
        
        Args:
            file_path: 文件路径
            content: 完整内容
            
        Returns:
            FileOutputResult: 操作结果
        """
        try:
            path = Path(file_path)
            
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 异步写入
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
            
            file_size = path.stat().st_size
            
            logger.info(f"Saved final content to {file_path}, size: {file_size} bytes")
            
            return FileOutputResult(
                success=True,
                file_path=file_path,
                bytes_written=len(content.encode("utf-8")),
                message=f"Successfully saved {len(content)} characters",
            )
            
        except Exception as e:
            logger.error(f"Failed to save final content to {file_path}: {e}")
            return FileOutputResult(
                success=False,
                file_path=file_path,
                bytes_written=0,
                message=f"Error: {str(e)}",
            )
    
    async def save_polished_chapter(
        self,
        chapter_number: int,
        content: str,
        original_file_path: str,
    ) -> FileOutputResult:
        """
        保存润色后的章节到最终文件

        直接将润色后的章节追加到最终文件，不创建中间文件。

        Args:
            chapter_number: 章节号
            content: 润色内容
            original_file_path: 原始文件路径（用于生成最终文件名）

        Returns:
            FileOutputResult: 操作结果
        """
        try:
            original_path = Path(original_file_path)
            final_filename = f"{original_path.stem}_final{original_path.suffix}"
            final_path = original_path.parent / final_filename

            # 确保目录存在
            final_path.parent.mkdir(parents=True, exist_ok=True)

            # 直接追加到最终文件
            async with aiofiles.open(final_path, "a", encoding="utf-8") as f:
                await f.write(f"=== Chapter {chapter_number} ===\n\n")
                await f.write(content)
                await f.write("\n\n")

            logger.info(f"Appended chapter {chapter_number} to final file: {final_path}")

            return FileOutputResult(
                success=True,
                file_path=str(final_path),
                bytes_written=len(content.encode("utf-8")),
                message=f"Chapter {chapter_number} appended to final file",
            )

        except Exception as e:
            logger.error(f"Failed to save chapter {chapter_number}: {e}")
            return FileOutputResult(
                success=False,
                file_path="",
                bytes_written=0,
                message=f"Error: {str(e)}",
            )
    
    def get_output_dir(self) -> str:
        """获取输出目录路径"""
        return str(self.output_dir)
