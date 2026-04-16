"""
存储后端工厂实现

实现 StorageBackendFactory 接口，根据配置创建对应的存储后端实例
"""

import logging
from typing import Optional

from interfaces.storage import StorageBackend, StorageBackendFactory
from implementations.storage.json_storage import JsonStorageBackend

logger = logging.getLogger(__name__)


class StorageBackendFactoryImpl(StorageBackendFactory):
    """
    存储后端工厂实现
    
    职责：
    - 根据配置创建存储后端实例
    - 支持多种后端类型切换
    - 管理后端实例的生命周期
    """

    def __init__(self, default_storage_dir: Optional[str] = None):
        """
        初始化工厂
        
        Args:
            default_storage_dir: 默认存储目录
        """
        self._default_storage_dir = default_storage_dir
        self._backends: dict[str, StorageBackend] = {}

    def create_backend(self, backend_type: str, **kwargs) -> StorageBackend:
        """
        创建存储后端
        
        Args:
            backend_type: 后端类型（"json", "sqlite"）
            **kwargs: 后端特定参数
            
        Returns:
            StorageBackend: 存储后端实例
            
        Raises:
            ValueError: 不支持的后端类型
        """
        # 检查缓存
        cache_key = f"{backend_type}_{kwargs.get('storage_dir', 'default')}"
        if cache_key in self._backends:
            return self._backends[cache_key]

        # 创建新实例
        if backend_type == "json":
            storage_dir = kwargs.get("storage_dir", self._default_storage_dir)
            backend = JsonStorageBackend(storage_dir)
        elif backend_type == "sqlite":
            # 预留 SQLite 后端支持
            raise NotImplementedError("SQLite backend not implemented yet")
        else:
            raise ValueError(f"Unsupported storage backend type: {backend_type}")

        # 缓存实例
        self._backends[cache_key] = backend
        logger.info(f"Created {backend_type} storage backend")
        return backend

    def get_default_backend(self) -> StorageBackend:
        """
        获取默认存储后端
        
        Returns:
            StorageBackend: 默认存储后端实例（JSON）
        """
        return self.create_backend("json")

    def close_all(self) -> None:
        """关闭所有缓存的后端实例"""
        for backend in self._backends.values():
            backend.close()
        self._backends.clear()
        logger.info("Closed all storage backends")


# 全局工厂实例（单例）
_factory: Optional[StorageBackendFactoryImpl] = None


def get_factory(default_storage_dir: Optional[str] = None) -> StorageBackendFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Args:
        default_storage_dir: 默认存储目录
        
    Returns:
        StorageBackendFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = StorageBackendFactoryImpl(default_storage_dir)
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    if _factory is not None:
        _factory.close_all()
    _factory = None
