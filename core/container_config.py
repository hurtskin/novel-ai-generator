"""
依赖注入容器配置

提供容器初始化函数，注册所有核心服务实现
"""

import logging
from typing import Optional

from core.container import Container, Scope
from interfaces import (
    LLMClient,
    MemoryStore,
    ObservabilityBackend,
    ConfigProvider,
    StorageBackend,
)

# 实现类导入
from implementations.llm.moonshot_client import MoonshotClient
from implementations.memory.simple_memory_store import SimpleMemoryStore
from implementations.observability.file_backend import FileObservabilityBackend
from implementations.config.yaml_config import YamlConfigProvider
from implementations.storage.json_storage import JsonStorageBackend

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
            LLMClient,
            MoonshotClient,
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClient -> MoonshotClient (Singleton)")
        
        # 3. 注册 MemoryStore (Transient)
        # SimpleMemoryStore 是有状态的（存储特定章节的记忆），每次请求需要新实例
        container.register(
            MemoryStore,
            SimpleMemoryStore,
            scope=Scope.TRANSIENT
        )
        logger.info("Registered MemoryStore -> SimpleMemoryStore (Transient)")
        
        # 4. 注册 ObservabilityBackend (Singleton)
        # FileObservabilityBackend 使用单例模式管理文件资源和 WebSocket 连接
        container.register(
            ObservabilityBackend,
            FileObservabilityBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered ObservabilityBackend -> FileObservabilityBackend (Singleton)")
        
        # 5. 注册 StorageBackend (Singleton)
        # JsonStorageBackend 线程安全，且需要维护文件索引，使用单例
        container.register(
            StorageBackend,
            JsonStorageBackend,
            scope=Scope.SINGLETON
        )
        logger.info("Registered StorageBackend -> JsonStorageBackend (Singleton)")
        
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
        
        # 注册 LLMClient (Singleton)
        container.register(
            LLMClient,
            MoonshotClient,
            scope=Scope.SINGLETON
        )
        logger.info("Registered LLMClient -> MoonshotClient (Singleton)")
        
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
