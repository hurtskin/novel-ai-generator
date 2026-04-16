"""
接口层 - 抽象接口定义

该模块定义了系统的所有抽象接口，实现业务逻辑与具体实现的解耦。
所有实现类都应该实现这些接口。
"""

from .llm_client import (
    LLMClient,
    LLMClientFactory,
    ChatMessage,
    ChatResponse,
    TokenUsage,
    PerformanceMetrics,
    StreamCallback,
)
from .memory import MemoryStore, MemoryRetriever, MemoryUpdate, RetrievalResult
from .observability import ObservabilityBackend, Span
from .config import ConfigProvider
from .storage import StorageBackend
from .embedding import EmbeddingClient, VectorStore

__all__ = [
    # LLM Client
    "LLMClient",
    "LLMClientFactory",
    "ChatMessage",
    "ChatResponse",
    "TokenUsage",
    "PerformanceMetrics",
    "StreamCallback",
    # Memory
    "MemoryStore",
    "MemoryRetriever",
    "MemoryUpdate",
    "RetrievalResult",
    # Observability
    "ObservabilityBackend",
    "Span",
    # Config
    "ConfigProvider",
    # Storage
    "StorageBackend",
    # Embedding
    "EmbeddingClient",
    "VectorStore",
]
