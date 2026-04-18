"""
依赖注入容器配置

提供容器初始化函数，注册所有核心服务实现
"""

import logging
from typing import Optional

from core.container import Container, Scope
from interfaces import (
    LLMClient,
    LLMClientFactory,
    MemoryStore,
    ObservabilityBackend,
    ConfigProvider,
    StorageBackend,
)
from services.interfaces import (
    VersionSelectorService,
    NodeRetryService,
    NodeRegenerateService,
    PerformanceMetricsService,
    ConfigManagerService,
    DebugLogService,
    WebSocketBroadcastService,
    FileOutputService,
    RAGRetrievalService,
    NovelGeneratorService,
    StateManagerService,
)
from services.novel_generator import NovelGenerator

# 实现类导入
from implementations.llm.moonshot_client import MoonshotClient
from implementations.memory.simple_memory_store import SimpleMemoryStore
from implementations.observability.file_backend import FileObservabilityBackend
from implementations.config.yaml_config import YamlConfigProvider
from implementations.storage.json_storage import JsonStorageBackend
from implementations.llm.factory import LLMClientFactoryImpl
from services.version_selector import VersionSelector
from services.node_retry import NodeRetryManager
from services.node_regenerate import NodeRegenerateManager
from services.performance_metrics import PerformanceMetricsCollector
from services.config_manager import ConfigManager
from services.debug_log import DebugLogManager
from services.websocket_broadcast import WebSocketBroadcastManager
from services.file_output import FileOutputManager
from services.rag_retrieval import RAGRetrievalManager



logger = logging.getLogger(__name__)


def initialize_container(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None
) -> Container:
    """
    初始化依赖注入容器
    
    注册所有核心服务的接口到实现的映射关系，配置适当的生命周期管理策略。
    
    注册的服务及生命周期策略：
    - LLMClient -> MoonshotClient (Singleton): LLM客户端是线程安全的，配置不变时使用单例
    - MemoryStore -> SimpleMemoryStore (Transient): 有状态，每次请求创建新实例
    - ObservabilityBackend -> FileObservabilityBackend (Singleton): 文件后端使用单例模式
    - ConfigProvider -> YamlConfigProvider (Singleton): 配置提供者线程安全，使用单例
    - StorageBackend -> JsonStorageBackend (Singleton): 存储后端线程安全，使用单例
    
    Args:
        config_path: 配置文件路径，默认为项目根目录的 config.yaml
        storage_dir: 存储目录路径，默认为项目根目录下的 storage 文件夹
        
    Returns:
        Container: 配置完成的依赖注入容器
        
    Raises:
        RegistrationError: 服务注册失败时抛出
        Exception: 其他初始化错误
        
    Example:
        >>> container = initialize_container()
        >>> llm_client = container.resolve(LLMClient)
        >>> memory_store = container.resolve(MemoryStore)
    """
    container = Container()
    
    try:
        # 1. 注册 ConfigProvider (Singleton)
        # 配置提供者线程安全，且在应用生命周期内配置相对稳定，使用单例
        container.register(
            ConfigProvider,
            YamlConfigProvider,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ConfigProvider -> YamlConfigProvider (Singleton)")
        
        # 2. 注册 LLMClient (Singleton)
        # MoonshotClient 是线程安全的，且 API 密钥和配置在应用生命周期内不变，使用单例
        container.register(
            LLMClientFactory,
            LLMClientFactoryImpl,
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClientFactory -> LLMClientFactoryImpl (Singleton)")

        # 3. 注册 LLMClient (Singleton)
        # 使用工厂根据配置创建对应的客户端
        container.register_factory(
            LLMClient,
            lambda c: c.resolve(LLMClientFactory).get_default_client(),
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClient (Singleton)")
        
        # 4. 注册 MemoryStore (Transient)
        # SimpleMemoryStore 是有状态的（存储特定章节的记忆），每次请求需要新实例
        container.register(
            MemoryStore,
            SimpleMemoryStore,
            scope=Scope.TRANSIENT
        )
        logger.info("Registered MemoryStore -> SimpleMemoryStore (Transient)")
        
        # 5. 注册 ObservabilityBackend (Singleton)
        # FileObservabilityBackend 使用单例模式管理文件资源和 WebSocket 连接
        container.register(
            ObservabilityBackend,
            FileObservabilityBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ObservabilityBackend -> FileObservabilityBackend (Singleton)")
        
        # 6. 注册 StorageBackend (Singleton)
        # JsonStorageBackend 线程安全，且需要维护文件索引，使用单例
        container.register(
            StorageBackend,
            JsonStorageBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered StorageBackend -> JsonStorageBackend (Singleton)")
        
        # 7. 注册 VersionSelectorService (Singleton)
        # VersionSelector 需要维护全局版本状态，使用单例
        container.register(
            VersionSelectorService,
            VersionSelector,
            scope=Scope.SINGLETON
        )
        logger.info("Registered VersionSelectorService -> VersionSelector (Singleton)")
        
        # 8. 注册 NodeRetryService (Singleton)
        # NodeRetryManager 需要维护全局重试状态，使用单例
        container.register(
            NodeRetryService,
            NodeRetryManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered NodeRetryService -> NodeRetryManager (Singleton)")
        
        # 9. 注册 NodeRegenerateService (Singleton)
        # NodeRegenerateManager 需要维护全局再生状态，使用单例
        container.register(
            NodeRegenerateService,
            NodeRegenerateManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered NodeRegenerateService -> NodeRegenerateManager (Singleton)")
        
        # 10. 注册 PerformanceMetricsService (Singleton)
        # PerformanceMetricsCollector 需要访问全局可观测性数据，使用单例
        container.register(
            PerformanceMetricsService,
            PerformanceMetricsCollector,
            scope=Scope.SINGLETON
        )
        logger.info("Registered PerformanceMetricsService -> PerformanceMetricsCollector (Singleton)")
        
        # 11. 注册 ConfigManagerService (Singleton)
        # ConfigManager 管理全局配置，使用单例
        container.register(
            ConfigManagerService,
            ConfigManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ConfigManagerService -> ConfigManager (Singleton)")
        
        # 12. 注册 DebugLogService (Singleton)
        # DebugLogManager 管理调试日志，使用单例
        container.register(
            DebugLogService,
            DebugLogManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered DebugLogService -> DebugLogManager (Singleton)")
        
        # 13. 注册 WebSocketBroadcastService (Singleton)
        # WebSocketBroadcastManager 管理 WebSocket 连接，使用单例模式
        container.register(
            WebSocketBroadcastService,
            WebSocketBroadcastManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered WebSocketBroadcastService -> WebSocketBroadcastServiceImpl (Singleton)")

        # 14. 注册 FileOutputService (Singleton)
        # FileOutputManager 管理文件输出，使用单例模式
        container.register(
            FileOutputService,
            FileOutputManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered FileOutputService -> FileOutputServiceImpl (Singleton)")
        
        # 15. 注册 RAGRetrievalService (Singleton)
        # RAGRetrievalManager 管理 RAG 检索，使用单例模式
        container.register_factory(
            RAGRetrievalService,
            lambda c: RAGRetrievalManager(memory_store=c.resolve(MemoryStore)),
            scope=Scope.SINGLETON
        )
        logger.info("Registered RAGRetrievalService -> RAGRetrievalManager (Singleton)")
        
        # 16. 注册 NovelGeneratorService (Singleton)
        # NovelGeneratorServiceImpl 管理小说生成，使用单例模式
        container.register_factory(
            NovelGeneratorService,
            lambda c: NovelGenerator(
                llm_client=c.resolve(LLMClient),
                memory_store=c.resolve(MemoryStore),
                observability=c.resolve(ObservabilityBackend),
                config_provider=c.resolve(ConfigProvider),
                websocket_service=c.resolve(WebSocketBroadcastService),
                file_output_service=c.resolve(FileOutputService),
                rag_service=c.resolve(RAGRetrievalService),
                state_manager=c.resolve(StateManagerService),
            ),
            scope=Scope.SINGLETON
        )

        logger.info("Container initialization completed successfully")
        return container
        
    except Exception as e:
        logger.error(f"Failed to initialize container: {e}")
        raise


def initialize_container_with_rag(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None
) -> Container:
    """
    初始化依赖注入容器（使用 RAG 记忆存储）
    
    与 initialize_container 类似，但使用 RAGMemoryStore 替代 SimpleMemoryStore
    
    Args:
        config_path: 配置文件路径
        storage_dir: 存储目录路径
        
    Returns:
        Container: 配置完成的依赖注入容器
    """
    from implementations.memory.rag_memory_store import RAGMemoryStore
    
    container = Container()
    
    try:
        # 注册 ConfigProvider (Singleton)
        container.register(
            ConfigProvider,
            YamlConfigProvider,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ConfigProvider -> YamlConfigProvider (Singleton)")
        
        # 注册 LLMClientFactory (Singleton)
        # LLMClientFactoryImpl 根据配置创建对应的 LLM 客户端
        container.register(
            LLMClientFactory,
            LLMClientFactoryImpl,
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClientFactory -> LLMClientFactoryImpl (Singleton)")

        # 注册 LLMClient (Singleton)
        # 使用工厂根据配置创建对应的客户端（支持 Moonshot/Ollama 切换）
        container.register_factory(
            LLMClient,
            lambda c: c.resolve(LLMClientFactory).get_default_client(),
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClient (Singleton)")
        
        # 注册 MemoryStore (Transient) - 使用 RAG 版本
        container.register(
            MemoryStore,
            RAGMemoryStore,
            scope=Scope.TRANSIENT
        )
        logger.info("Registered MemoryStore -> RAGMemoryStore (Transient)")
        
        # 注册 ObservabilityBackend (Singleton)
        container.register(
            ObservabilityBackend,
            FileObservabilityBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ObservabilityBackend -> FileObservabilityBackend (Singleton)")
        
        # 注册 StorageBackend (Singleton)
        container.register(
            StorageBackend,
            JsonStorageBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered StorageBackend -> JsonStorageBackend (Singleton)")

        # 注册 ConfigManagerService (Singleton)
        # ConfigManager 管理全局配置，使用单例
        container.register(
            ConfigManagerService,
            ConfigManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ConfigManagerService -> ConfigManager (Singleton)")

        # 注册 DebugLogService (Singleton)
        # DebugLogManager 管理调试日志，使用单例
        container.register(
            DebugLogService,
            DebugLogManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered DebugLogService -> DebugLogManager (Singleton)")

        # 注册 WebSocketBroadcastService (Singleton)
        # WebSocketBroadcastManager 管理 WebSocket 连接，使用单例模式
        container.register(
            WebSocketBroadcastService,
            WebSocketBroadcastManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered WebSocketBroadcastService -> WebSocketBroadcastManager (Singleton)")

        # 注册 FileOutputService (Singleton)
        # FileOutputManager 管理文件输出，使用单例模式
        container.register(
            FileOutputService,
            FileOutputManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered FileOutputService -> FileOutputManager (Singleton)")

        # 注册 VersionSelectorService (Singleton)
        container.register(
            VersionSelectorService,
            VersionSelector,
            scope=Scope.SINGLETON
        )
        logger.info("Registered VersionSelectorService -> VersionSelector (Singleton)")
        
        # 注册 NodeRetryService (Singleton)
        container.register(
            NodeRetryService,
            NodeRetryManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered NodeRetryService -> NodeRetryManager (Singleton)")
        
        # 注册 NodeRegenerateService (Singleton)
        container.register(
            NodeRegenerateService,
            NodeRegenerateManager,
            scope=Scope.SINGLETON
        )
        logger.info("Registered NodeRegenerateService -> NodeRegenerateManager (Singleton)")
        
        # 注册 PerformanceMetricsService (Singleton)
        container.register(
            PerformanceMetricsService,
            PerformanceMetricsCollector,
            scope=Scope.SINGLETON
        )
        logger.info("Registered PerformanceMetricsService -> PerformanceMetricsCollector (Singleton)")

        # 注册 RAGRetrievalService (Singleton)
        # RAGRetrievalManager 管理 RAG 检索，使用单例模式
        container.register_factory(
            RAGRetrievalService,
            lambda c: RAGRetrievalManager(memory_store=c.resolve(MemoryStore)),
            scope=Scope.SINGLETON
        )
        logger.info("Registered RAGRetrievalService -> RAGRetrievalManager (Singleton)")

        # 注册 NovelGeneratorService (Singleton)
        # NovelGenerator 管理小说生成，使用单例模式
        container.register_factory(
            NovelGeneratorService,
            lambda c: NovelGenerator(
                llm_client=c.resolve(LLMClient),
                memory_store=c.resolve(MemoryStore),
                observability=c.resolve(ObservabilityBackend),
                config_provider=c.resolve(ConfigProvider),
                websocket_service=c.resolve(WebSocketBroadcastService),
                file_output_service=c.resolve(FileOutputService),
                rag_service=c.resolve(RAGRetrievalService),
                state_manager=c.resolve(StateManagerService),
            ),
            scope=Scope.SINGLETON
        )
        logger.info("Registered NovelGeneratorService -> NovelGenerator (Singleton)")

        logger.info("Container initialization with RAG completed successfully")
        return container
        
    except Exception as e:
        logger.error(f"Failed to initialize container with RAG: {e}")
        raise


def get_global_initialized_container() -> Container:
    """
    获取全局初始化的容器（懒加载）
    
    使用单例模式确保全局只有一个初始化后的容器实例
    
    Returns:
        Container: 全局初始化的容器
    """
    from core.container import get_global_container
    
    container = get_global_container()
    
    # 检查是否已经初始化
    if not container.is_registered(LLMClient):
        # 未初始化，执行初始化
        new_container = initialize_container()
        # 复制注册到新容器
        for interface in new_container.get_registered_interfaces():
            registrations = new_container._registrations.get(interface, [])
            for reg in registrations:
                if reg.instance is not None:
                    container.register_instance(interface, reg.instance)
                elif reg.factory is not None:
                    container.register_factory(
                        interface, 
                        reg.factory, 
                        reg.scope
                    )
                else:
                    container.register(
                        interface,
                        reg.implementation,
                        reg.scope,
                        reg.name
                    )
    
    return container
