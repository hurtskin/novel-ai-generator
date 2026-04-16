"""
存储实现模块

提供多种存储后端实现：
- JsonStorageBackend: JSON 文件存储
- StorageBackendFactoryImpl: 工厂类

使用示例：
    from implementations.storage import JsonStorageBackend, get_factory
    
    # 直接创建后端
    backend = JsonStorageBackend("./storage")
    
    # 或使用工厂
    factory = get_factory()
    backend = factory.get_default_backend()
    
    # 保存数据
    backend.save("key", {"name": "test", "value": 123})
    
    # 加载数据
    data = backend.load("key")
    
    # 检查存在性
    if backend.exists("key"):
        print("Key exists")
    
    # 列出所有键
    keys = backend.list_keys()
    
    # 删除数据
    backend.delete("key")
"""

from implementations.storage.json_storage import JsonStorageBackend
from implementations.storage.factory import (
    StorageBackendFactoryImpl,
    get_factory,
    reset_factory,
)

__all__ = [
    "JsonStorageBackend",
    "StorageBackendFactoryImpl",
    "get_factory",
    "reset_factory",
]
