"""
嵌入客户端工厂实现

实现 EmbeddingClientFactory 接口，创建对应的嵌入客户端实例
"""

import logging
import os
from typing import Optional

from interfaces.embedding import EmbeddingClient, VectorStore
from implementations.embedding.infini_embedding import InfiniEmbeddingClient, SimpleVectorStore

logger = logging.getLogger(__name__)


class EmbeddingClientFactoryImpl:
    """
    嵌入客户端工厂实现
    
    职责：
    - 根据配置创建嵌入客户端实例
    - 支持多种嵌入服务（Infini、OpenAI等）
    - 管理客户端实例的生命周期
    """

    def __init__(self):
        """初始化工厂"""
        self._clients: dict[str, EmbeddingClient] = {}
        self._vector_stores: dict[str, VectorStore] = {}

    def create_client(
        self,
        client_type: str = "infini",
        model: str = "infini-embedding-v1",
        dimensions: int = 768,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> EmbeddingClient:
        """
        创建嵌入客户端
        
        Args:
            client_type: 客户端类型（"infini", "openai"）
            model: 嵌入模型名称
            dimensions: 嵌入维度
            api_key: API 密钥
            base_url: API 基础 URL
            
        Returns:
            EmbeddingClient: 嵌入客户端实例
            
        Raises:
            ValueError: 不支持的客户端类型
        """
        # 检查缓存
        cache_key = f"{client_type}_{model}"
        if cache_key in self._clients:
            return self._clients[cache_key]

        # 创建新实例
        if client_type == "infini":
            client = InfiniEmbeddingClient(
                model=model,
                dimensions=dimensions,
                api_key=api_key,
                base_url=base_url,
            )
        elif client_type == "openai":
            # 预留 OpenAI 客户端支持
            raise NotImplementedError("OpenAI embedding client not implemented yet")
        else:
            raise ValueError(f"Unsupported embedding client type: {client_type}")

        # 缓存实例
        self._clients[cache_key] = client
        logger.info(f"Created {client_type} embedding client with model {model}")
        return client

    def create_vector_store(self, storage_path: Optional[str] = None) -> VectorStore:
        """
        创建向量存储
        
        Args:
            storage_path: 存储文件路径
            
        Returns:
            VectorStore: 向量存储实例
        """
        # 检查缓存
        cache_key = storage_path or "memory"
        if cache_path in self._vector_stores:
            return self._vector_stores[cache_key]

        # 创建新实例
        store = SimpleVectorStore(storage_path)
        
        # 缓存实例
        self._vector_stores[cache_key] = store
        logger.info(f"Created vector store with path: {storage_path}")
        return store

    def get_default_client(self) -> EmbeddingClient:
        """
        获取默认嵌入客户端
        
        Returns:
            EmbeddingClient: 默认嵌入客户端实例（Infini）
        """
        return self.create_client("infini")

    def close_all(self) -> None:
        """关闭所有缓存的客户端实例"""
        # 保存向量存储
        for store in self._vector_stores.values():
            store.save()
        
        self._clients.clear()
        self._vector_stores.clear()
        logger.info("Closed all embedding clients and vector stores")


# 全局工厂实例（单例）
_factory: Optional[EmbeddingClientFactoryImpl] = None


def get_factory() -> EmbeddingClientFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Returns:
        EmbeddingClientFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = EmbeddingClientFactoryImpl()
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    if _factory is not None:
        _factory.close_all()
    _factory = None
