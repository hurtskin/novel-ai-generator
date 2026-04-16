"""
服务层模块

提供核心业务逻辑服务，包括小说生成、状态管理、快照管理等功能
"""

from services.interfaces import (
    NovelGeneratorService,
    StateManagerService,
    SnapshotManagerService,
    GenerationRequest,
    GenerationResult,
    GenerationProgress,
    GenerationStatus,
    ChapterResult,
    SnapshotInfo,
    StateSnapshot,
    NovelStyle,
    ServiceError,
    GenerationError,
    StateError,
    SnapshotError,
)

from services.novel_generator import NovelGenerator
from services.state_manager import StateManager
from services.snapshot_manager import SnapshotManager

__all__ = [
    # 服务接口
    "NovelGeneratorService",
    "StateManagerService",
    "SnapshotManagerService",
    # 服务实现
    "NovelGenerator",
    "StateManager",
    "SnapshotManager",
    # 数据类
    "GenerationRequest",
    "GenerationResult",
    "GenerationProgress",
    "GenerationStatus",
    "ChapterResult",
    "SnapshotInfo",
    "StateSnapshot",
    "NovelStyle",
    # 异常类
    "ServiceError",
    "GenerationError",
    "StateError",
    "SnapshotError",
]
