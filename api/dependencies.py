"""
API 依赖项模块

提供 FastAPI 依赖注入功能，包括服务解析、认证、请求验证等
"""

import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.container import Container
from interfaces import (
    LLMClient,
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
    NovelGeneratorService,
    StateManagerService,
)

logger = logging.getLogger(__name__)

# 安全方案
security = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    """
    获取依赖注入容器
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        Container: 依赖注入容器
        
    Raises:
        HTTPException: 容器未初始化时
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized",
        )
    return container


def get_llm_client(container: Container = Depends(get_container)) -> LLMClient:
    """
    获取 LLM 客户端
    
    Args:
        container: 依赖注入容器
        
    Returns:
        LLMClient: LLM 客户端实例
    """
    return container.resolve(LLMClient)


def get_memory_store(container: Container = Depends(get_container)) -> MemoryStore:
    """
    获取记忆存储
    
    Args:
        container: 依赖注入容器
        
    Returns:
        MemoryStore: 记忆存储实例（瞬态，每次请求新实例）
    """
    return container.resolve(MemoryStore)


def get_observability(container: Container = Depends(get_container)) -> ObservabilityBackend:
    """
    获取可观测性后端
    
    Args:
        container: 依赖注入容器
        
    Returns:
        ObservabilityBackend: 可观测性后端实例
    """
    return container.resolve(ObservabilityBackend)


def get_config_provider(container: Container = Depends(get_container)) -> ConfigProvider:
    """
    获取配置提供者
    
    Args:
        container: 依赖注入容器
        
    Returns:
        ConfigProvider: 配置提供者实例
    """
    return container.resolve(ConfigProvider)


def get_storage_backend(container: Container = Depends(get_container)) -> StorageBackend:
    """
    获取存储后端
    
    Args:
        container: 依赖注入容器
        
    Returns:
        StorageBackend: 存储后端实例
    """
    return container.resolve(StorageBackend)


def get_version_selector_service(container: Container = Depends(get_container)) -> VersionSelectorService:
    """
    获取版本选择服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        VersionSelectorService: 版本选择服务实例
    """
    return container.resolve(VersionSelectorService)


def get_node_retry_service(container: Container = Depends(get_container)) -> NodeRetryService:
    """
    获取节点重试服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        NodeRetryService: 节点重试服务实例
    """
    return container.resolve(NodeRetryService)


def get_node_regenerate_service(container: Container = Depends(get_container)) -> NodeRegenerateService:
    """
    获取节点再生服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        NodeRegenerateService: 节点再生服务实例
    """
    return container.resolve(NodeRegenerateService)


def get_performance_metrics_service(container: Container = Depends(get_container)) -> PerformanceMetricsService:
    """
    获取性能指标服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        PerformanceMetricsService: 性能指标服务实例
    """
    return container.resolve(PerformanceMetricsService)


def get_config_manager_service(container: Container = Depends(get_container)) -> ConfigManagerService:
    """
    获取配置管理服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        ConfigManagerService: 配置管理服务实例
    """
    return container.resolve(ConfigManagerService)


def get_debug_log_service(container: Container = Depends(get_container)) -> DebugLogService:
    """
    获取调试日志服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        DebugLogService: 调试日志服务实例
    """
    return container.resolve(DebugLogService)


def get_novel_generator_service(container: Container = Depends(get_container)) -> NovelGeneratorService:
    """
    获取小说生成服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        NovelGeneratorService: 小说生成服务实例
    """
    return container.resolve(NovelGeneratorService)


def get_state_manager_service(container: Container = Depends(get_container)) -> StateManagerService:
    """
    获取状态管理服务
    
    Args:
        container: 依赖注入容器
        
    Returns:
        StateManagerService: 状态管理服务实例
    """
    return container.resolve(StateManagerService)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    验证访问令牌
    
    Args:
        credentials: HTTP 认证凭据
        
    Returns:
        str: 验证通过的用户标识
        
    Raises:
        HTTPException: 验证失败时
        
    Note:
        当前为简化实现，实际生产环境应该使用 JWT 或其他安全机制
    """
    # 如果没有提供认证信息，允许匿名访问（开发环境）
    if credentials is None:
        return "anonymous"
    
    token = credentials.credentials
    
    # 简化验证：检查 token 格式
    # 实际生产环境应该验证 JWT 签名、过期时间等
    if not token or len(token) < 8:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: 实现实际的 token 验证逻辑
    # 例如：验证 JWT、查询数据库等
    
    return f"user_{token[:8]}"


class PaginationParams:
    """分页参数"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        初始化分页参数
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
        """
        self.skip = skip
        self.limit = min(limit, 1000)  # 限制最大返回数


def get_pagination(
    skip: int = 0,
    limit: int = 100,
) -> PaginationParams:
    """
    获取分页参数
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        
    Returns:
        PaginationParams: 分页参数对象
    """
    return PaginationParams(skip=skip, limit=limit)


class GenerationState:
    """生成任务状态管理"""
    
    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = False
        self.is_stopped: bool = False
        self.current_chapter: int = 0
        self.current_node: str = ""
        self.total_chapters: int = 0
        self.progress: float = 0.0
        self.error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "is_stopped": self.is_stopped,
            "current_chapter": self.current_chapter,
            "current_node": self.current_node,
            "total_chapters": self.total_chapters,
            "progress": self.progress,
            "error": self.error,
        }


# 全局生成状态（简化实现，生产环境应该使用 Redis 等）
_generation_state = GenerationState()


def get_generation_state() -> GenerationState:
    """
    获取生成任务状态
    
    Returns:
        GenerationState: 生成任务状态
    """
    return _generation_state


async def require_generation_not_running(
    state: GenerationState = Depends(get_generation_state),
) -> None:
    """
    检查没有正在运行的生成任务
    
    Args:
        state: 生成任务状态
        
    Raises:
        HTTPException: 有正在运行的任务时
    """
    if state.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A generation task is already running",
        )
