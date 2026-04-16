"""
记忆存储工厂实现

实现 MemoryStoreFactory 接口，根据配置创建对应的记忆存储实例
支持 SimpleMemoryStore 和 RAGMemoryStore 两种实现
"""

import os
from typing import Optional
import yaml

from interfaces.memory import MemoryStore, MemoryStoreFactory
from implementations.memory.simple_memory_store import SimpleMemoryStore
from implementations.memory.rag_memory_store import RAGMemoryStore


class MemoryStoreFactoryImpl(MemoryStoreFactory):
    """
    记忆存储工厂实现
    
    职责：
    - 根据配置创建记忆存储实例
    - 支持多种存储后端切换
    - 管理存储实例的生命周期
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化工厂
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        self._stores: dict[str, MemoryStore] = {}

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()
        # 清除缓存的存储实例，下次创建时会使用新配置
        self._stores.clear()

    def create_store(self, backend: str) -> MemoryStore:
        """
        创建记忆存储实例
        
        Args:
            backend: 后端类型（"simple", "rag"）
            
        Returns:
            MemoryStore: 存储实例
            
        Raises:
            ValueError: 不支持的存储后端
        """
        # 检查缓存
        if backend in self._stores:
            return self._stores[backend]

        # 创建新实例
        if backend == "simple":
            store = SimpleMemoryStore(self._config_path)
        elif backend == "rag":
            store = RAGMemoryStore(self._config_path)
        else:
            raise ValueError(f"Unsupported memory store backend: {backend}")

        # 缓存实例
        self._stores[backend] = store
        return store

    def get_default_store(self) -> MemoryStore:
        """
        获取默认配置的存储实例
        
        根据配置文件中的设置决定使用哪种存储后端
        
        Returns:
            MemoryStore: 默认存储实例
        """
        # 从配置中读取存储后端类型
        memory_config = self._config.get("memory", {})
        backend = memory_config.get("backend", "simple")
        
        # 检查是否启用 RAG
        if backend == "rag":
            # 检查 RAG 是否可用（需要嵌入配置）
            embedding_config = self._config.get("embedding", {})
            if embedding_config.get("api_key"):
                return self.create_store("rag")
            # RAG 配置不完整，回退到简单存储
            return self.create_store("simple")
        
        return self.create_store("simple")

    def get_store(self, backend: Optional[str] = None) -> MemoryStore:
        """
        获取存储实例（便捷方法）
        
        Args:
            backend: 后端类型，None 则使用默认配置
            
        Returns:
            MemoryStore: 存储实例
        """
        if backend is None:
            return self.get_default_store()
        return self.create_store(backend)


# 全局工厂实例（单例）
_factory: Optional[MemoryStoreFactoryImpl] = None


def get_factory(config_path: Optional[str] = None) -> MemoryStoreFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        MemoryStoreFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = MemoryStoreFactoryImpl(config_path)
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    _factory = None
