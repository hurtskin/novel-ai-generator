"""
记忆存储实现模块

提供多种记忆存储后端实现：
- SimpleMemoryStore: 基于内存的简单存储
- RAGMemoryStore: 基于向量检索的 RAG 存储
- MemoryStoreFactoryImpl: 存储工厂

使用示例：
    from implementations.memory import SimpleMemoryStore, RAGMemoryStore
    from implementations.memory import get_factory
    
    # 直接创建存储
    store = SimpleMemoryStore()
    
    # 或使用工厂
    factory = get_factory()
    store = factory.get_default_store()
    
    # 更新记忆
    from interfaces.memory import MemoryUpdate
    update = MemoryUpdate(
        chapter_id=1,
        node_id="node_1",
        target_character="主角",
        new_memories=["遇到了一个神秘人"],
    )
    store.update_memory(update)
"""

from implementations.memory.simple_memory_store import SimpleMemoryStore
from implementations.memory.rag_memory_store import RAGMemoryStore, EmbeddingClient, VectorStore
from implementations.memory.factory import (
    MemoryStoreFactoryImpl,
    get_factory,
    reset_factory,
)

__all__ = [
    "SimpleMemoryStore",
    "RAGMemoryStore",
    "EmbeddingClient",
    "VectorStore",
    "MemoryStoreFactoryImpl",
    "get_factory",
    "reset_factory",
]
