"""
API 层模块

提供 FastAPI 后端服务
"""

from api.app import app, create_app
from api.dependencies import (
    get_container,
    get_llm_client,
    get_memory_store,
    get_observability,
    get_config_provider,
    get_storage_backend,
    get_generation_state,
)

__all__ = [
    # 应用
    "app",
    "create_app",
    # 依赖项
    "get_container",
    "get_llm_client",
    "get_memory_store",
    "get_observability",
    "get_config_provider",
    "get_storage_backend",
    "get_generation_state",
]
