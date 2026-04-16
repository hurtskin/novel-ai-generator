"""
实现层包

提供所有接口的具体实现，包括：
- LLM 客户端实现 (llm/)
- 嵌入服务实现 (embedding/)
- 记忆存储实现 (memory/)
- 可观测性实现 (observability/)
- 持久化存储实现 (storage/)
- 配置管理实现 (config/)

使用示例：
    # 从实现层导入具体类
    from implementations.llm import MoonshotClient, OllamaClient
    from implementations.memory import SimpleMemoryStore, RAGMemoryStore
    from implementations.observability import FileObservabilityBackend
    from implementations.storage import JsonStorageBackend
    from implementations.config import YamlConfigProvider
    
    # 或使用工厂获取默认实例
    from implementations.llm import get_factory as get_llm_factory
    from implementations.memory import get_factory as get_memory_factory
    from implementations.observability import get_factory as get_obs_factory
    from implementations.storage import get_factory as get_storage_factory
    from implementations.config import get_factory as get_config_factory
    
    # 获取默认客户端/存储/后端
    llm_client = get_llm_factory().get_default_client()
    memory_store = get_memory_factory().get_default_store()
    obs_backend = get_obs_factory().get_default_backend()
    storage_backend = get_storage_factory().get_default_backend()
    config_provider = get_config_factory().get_default_provider()

架构说明：
    实现层遵循依赖注入原则，所有实现类都实现了 interfaces/ 中定义的对应接口。
    通过工厂模式管理实例生命周期，支持配置驱动的实现切换。
"""

# LLM 客户端实现
from implementations.llm import (
    MoonshotClient,
    OllamaClient,
    LLMClientFactoryImpl,
    get_factory as get_llm_factory,
    reset_factory as reset_llm_factory,
)

# 嵌入服务实现
from implementations.embedding import (
    InfiniEmbeddingClient,
    SimpleVectorStore,
    EmbeddingClientFactoryImpl,
    get_factory as get_embedding_factory,
    reset_factory as reset_embedding_factory,
)

# 记忆存储实现
from implementations.memory import (
    SimpleMemoryStore,
    RAGMemoryStore,
    MemoryStoreFactoryImpl,
    get_factory as get_memory_factory,
    reset_factory as reset_memory_factory,
)

# 可观测性实现
from implementations.observability import (
    FileObservabilityBackend,
    NullObservabilityBackend,
    ObservabilityFactoryImpl,
    get_factory as get_observability_factory,
    reset_factory as reset_observability_factory,
)

# 持久化存储实现
from implementations.storage import (
    JsonStorageBackend,
    StorageBackendFactoryImpl,
    get_factory as get_storage_factory,
    reset_factory as reset_storage_factory,
)

# 配置管理实现
from implementations.config import (
    YamlConfigProvider,
    ConfigProviderFactoryImpl,
    get_factory as get_config_factory,
    reset_factory as reset_config_factory,
)

__all__ = [
    # LLM
    "MoonshotClient",
    "OllamaClient",
    "LLMClientFactoryImpl",
    "get_llm_factory",
    "reset_llm_factory",
    # Embedding
    "InfiniEmbeddingClient",
    "SimpleVectorStore",
    "EmbeddingClientFactoryImpl",
    "get_embedding_factory",
    "reset_embedding_factory",
    # Memory
    "SimpleMemoryStore",
    "RAGMemoryStore",
    "MemoryStoreFactoryImpl",
    "get_memory_factory",
    "reset_memory_factory",
    # Observability
    "FileObservabilityBackend",
    "NullObservabilityBackend",
    "ObservabilityFactoryImpl",
    "get_observability_factory",
    "reset_observability_factory",
    # Storage
    "JsonStorageBackend",
    "StorageBackendFactoryImpl",
    "get_storage_factory",
    "reset_storage_factory",
    # Config
    "YamlConfigProvider",
    "ConfigProviderFactoryImpl",
    "get_config_factory",
    "reset_config_factory",
]
