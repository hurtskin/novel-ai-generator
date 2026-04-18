"""
服务层模块

提供核心业务逻辑服务，包括小说生成、状态管理、快照管理、版本选择、节点重试等功能
"""

from services.interfaces import (
    NovelGeneratorService,
    StateManagerService,
    SnapshotManagerService,
    VersionSelectorService,
    NodeRetryService,
    NodeRegenerateService,
    PerformanceMetricsService,
    GenerationRequest,
    GenerationResult,
    GenerationProgress,
    GenerationStatus,
    ChapterResult,
    SnapshotInfo,
    StateSnapshot,
    VersionInfo,
    VersionSelectionResult,
    NodeRetryResult,
    NodeRegenerateResult,
    PerformanceMetricsData,
    PerformanceMetricsSummary,
    NovelStyle,
    ServiceError,
    GenerationError,
    StateError,
    SnapshotError,
    VersionSelectionError,
    NodeRetryError,
    NodeRegenerateError,
    PerformanceMetricsError,
    ConfigManagerError
)

from services.novel_generator import NovelGenerator
from services.state_manager import StateManager
from services.snapshot_manager import SnapshotManager
from services.version_selector import VersionSelector
from services.node_retry import NodeRetryManager
from services.node_regenerate import NodeRegenerateManager
from services.performance_metrics import PerformanceMetricsCollector
from services.config_manager import ConfigManager
from services.debug_log import DebugLogManager
from services.websocket_broadcast import WebSocketBroadcastManager
from services.file_output import FileOutputManager
from services.rag_retrieval import RAGRetrievalManager



__all__ = [
    # 服务接口
    "NovelGeneratorService",
    "StateManagerService",
    "SnapshotManagerService",
    "VersionSelectorService",
    "NodeRetryService",
    "NodeRegenerateService",
    "PerformanceMetricsService",
    "ConfigManagerService",
    "DebugLogService",
    "WebSocketBroadcastService",
    "FileOutputService",
    "RAGRetrievalService",
    # 服务实现
    "NovelGenerator",
    "StateManager",
    "SnapshotManager",
    "VersionSelector",
    "NodeRetryManager",
    "NodeRegenerateManager",
    "PerformanceMetricsCollector",
    "ConfigManager",
    "DebugLogManager",
    "WebSocketBroadcastManager",
    "FileOutputManager",
    "RAGRetrievalManager",
    # 数据类
    "GenerationRequest",
    "GenerationResult",
    "GenerationProgress",
    "GenerationStatus",
    "ChapterResult",
    "SnapshotInfo",
    "StateSnapshot",
    "VersionInfo",
    "VersionSelectionResult",
    "NodeRetryResult",
    "NodeRegenerateResult",
    "PerformanceMetricsData",
    "PerformanceMetricsSummary",
    "NovelStyle",
    # 异常类
    "ServiceError",
    "GenerationError",
    "StateError",
    "SnapshotError",
    "VersionSelectionError",
    "NodeRetryError",
    "NodeRegenerateError",
    "PerformanceMetricsError",
    "ConfigManagerError"
]
