"""
嵌入实现模块

提供嵌入服务实现：
- InfiniEmbeddingClient: Infini 嵌入客户端
- SimpleVectorStore: 简单向量存储
- EmbeddingClientFactoryImpl: 工厂类

使用示例：
    from implementations.embedding import InfiniEmbeddingClient, get_factory
    
    # 直接创建客户端
    client = InfiniEmbeddingClient(model="infini-embedding-v1")
    
    # 或使用工厂
    factory = get_factory()
    client = factory.get_default_client()
    
    # 嵌入文本
    embedding = client.embed_single("这是一段文本")
    embeddings = client.embed(["文本1", "文本2"])
    
    # 创建向量存储
    store = factory.create_vector_store("./vectors.json")
    
    # 添加文本块
    store.add(
        chunks=["文本块1", "文本块2"],
        embeddings=[embedding1, embedding2],
        metadatas=[{"chapter_id": 1}, {"chapter_id": 2}]
    )
    
    # 搜索相似向量
    results = store.search(query_embedding, top_k=5)
"""

from implementations.embedding.infini_embedding import InfiniEmbeddingClient, SimpleVectorStore
from implementations.embedding.factory import (
    EmbeddingClientFactoryImpl,
    get_factory,
    reset_factory,
)

__all__ = [
    "InfiniEmbeddingClient",
    "SimpleVectorStore",
    "EmbeddingClientFactoryImpl",
    "get_factory",
    "reset_factory",
]
