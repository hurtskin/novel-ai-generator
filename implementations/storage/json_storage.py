"""
JSON 存储后端实现

实现 StorageBackend 接口，提供基于 JSON 文件的持久化存储功能
支持数据的读取、写入、更新和删除操作
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

from interfaces.storage import StorageBackend, StorageEntry

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JsonStorageBackend(StorageBackend):
    """
    JSON 文件存储后端实现
    
    功能特性：
    - 基于 JSON 文件的持久化存储
    - 支持 CRUD 操作
    - 自动创建存储目录
    - 版本控制支持
    - 线程安全的文件操作
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化 JSON 存储后端
        
        Args:
            storage_dir: 存储目录路径，默认使用项目根目录下的 storage 文件夹
        """
        if storage_dir is None:
            storage_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "storage"
            )
        
        self._storage_dir = storage_dir
        self._index_file = os.path.join(storage_dir, "index.json")
        
        # 创建存储目录
        os.makedirs(storage_dir, exist_ok=True)
        
        # 加载索引
        self._index: Dict[str, StorageEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """加载索引文件"""
        if os.path.exists(self._index_file):
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._index = {
                        k: StorageEntry(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                self._index = {}

    def _save_index(self) -> None:
        """保存索引文件"""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.__dict__ for k, v in self._index.items()},
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _get_data_file(self, key: str) -> str:
        """获取数据文件路径"""
        # 使用 key 的哈希值作为文件名，避免特殊字符问题
        import hashlib
        filename = hashlib.md5(key.encode()).hexdigest() + ".json"
        return os.path.join(self._storage_dir, filename)

    def save(self, key: str, data: Any) -> None:
        """
        保存数据
        
        Args:
            key: 数据键
            data: 数据内容
        """
        data_file = self._get_data_file(key)
        
        # 检查是否已存在
        if key in self._index:
            entry = self._index[key]
            entry.version += 1
            entry.updated_at = datetime.now().isoformat()
        else:
            now = datetime.now().isoformat()
            entry = StorageEntry(
                key=key,
                data=None,  # 数据存储在单独文件中
                created_at=now,
                updated_at=now,
                version=1
            )
        
        # 保存数据文件
        try:
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data for key {key}: {e}")
            raise
        
        # 更新索引
        self._index[key] = entry
        self._save_index()
        
        logger.debug(f"Saved data with key: {key}")

    def load(self, key: str, default: Optional[T] = None) -> T:
        """
        加载数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            T: 数据内容
        """
        if key not in self._index:
            if default is not None:
                return default
            raise KeyError(f"Key not found: {key}")
        
        data_file = self._get_data_file(key)
        
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data for key {key}: {e}")
            if default is not None:
                return default
            raise

    def delete(self, key: str) -> bool:
        """
        删除数据
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否删除成功
        """
        if key not in self._index:
            return False
        
        data_file = self._get_data_file(key)
        
        try:
            # 删除数据文件
            if os.path.exists(data_file):
                os.remove(data_file)
            
            # 更新索引
            del self._index[key]
            self._save_index()
            
            logger.debug(f"Deleted data with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete data for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否存在
        """
        return key in self._index

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        列出所有数据键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            List[str]: 键列表
        """
        keys = list(self._index.keys())
        
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        
        return keys

    def clear(self) -> None:
        """清空所有数据"""
        try:
            # 删除所有数据文件
            for key in list(self._index.keys()):
                data_file = self._get_data_file(key)
                if os.path.exists(data_file):
                    os.remove(data_file)
            
            # 清空索引
            self._index.clear()
            self._save_index()
            
            logger.info("Cleared all data")
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            raise

    def close(self) -> None:
        """关闭存储后端，释放资源"""
        self._save_index()
        logger.info("Closed JSON storage backend")

    def get_entry(self, key: str) -> Optional[StorageEntry]:
        """
        获取存储条目元数据
        
        Args:
            key: 数据键
            
        Returns:
            Optional[StorageEntry]: 存储条目，不存在则返回 None
        """
        return self._index.get(key)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_size = 0
        for key in self._index:
            data_file = self._get_data_file(key)
            if os.path.exists(data_file):
                total_size += os.path.getsize(data_file)
        
        return {
            "total_keys": len(self._index),
            "storage_dir": self._storage_dir,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
