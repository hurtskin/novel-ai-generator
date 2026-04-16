"""
持久化存储接口定义

定义数据持久化的抽象接口，支持多种存储后端（JSON文件、SQLite等）
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

T = TypeVar("T")


@dataclass
class StorageEntry:
    """存储条目"""
    key: str
    data: Any
    created_at: str
    updated_at: str
    version: int = 1


class StorageBackend(ABC):
    """
    存储后端抽象基类
    
    职责：
    - 数据持久化存储
    - 支持CRUD操作
    - 支持事务（可选）
    
    实现类：
    - JsonStorageBackend: JSON文件存储
    - SQLiteStorageBackend: SQLite数据库存储
    """
    
    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        """
        保存数据
        
        Args:
            key: 数据键
            data: 数据内容
        """
        pass
    
    @abstractmethod
    def load(self, key: str, default: Optional[T] = None) -> T:
        """
        加载数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            T: 数据内容
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除数据
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        列出所有数据键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            List[str]: 键列表
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有数据"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭存储后端，释放资源"""
        pass


class StorageBackendFactory(ABC):
    """存储后端工厂"""
    
    @abstractmethod
    def create_backend(self, backend_type: str, **kwargs) -> StorageBackend:
        """
        创建存储后端
        
        Args:
            backend_type: 后端类型（"json", "sqlite"）
            **kwargs: 后端特定参数
            
        Returns:
            StorageBackend: 存储后端实例
        """
        pass
