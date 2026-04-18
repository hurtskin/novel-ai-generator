"""
服务层接口定义

定义所有服务的抽象接口，实现业务逻辑与实现的解耦
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GenerationStatus(str, Enum):
    """生成状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class NovelStyle(str, Enum):
    """小说文体枚举"""
    NOVEL = "novel"
    SCRIPT = "script"
    GAME_STORY = "game_story"
    DIALOGUE = "dialogue"
    ARTICLE = "article"


@dataclass
class GenerationRequest:
    """生成请求数据类"""
    theme: str
    style: NovelStyle = NovelStyle.NOVEL
    total_words: int = 10000
    character_count: int = 3
    genre: str = "modern"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class GenerationProgress:
    """生成进度数据类"""
    current_chapter: int
    total_chapters: int
    current_node: str
    percentage: float
    status: GenerationStatus
    message: Optional[str] = None


@dataclass
class ChapterResult:
    """章节结果数据类"""
    chapter_number: int
    title: str
    content: str
    word_count: int
    node_results: Dict[str, Any]


@dataclass
class GenerationResult:
    """生成结果数据类"""
    task_id: str
    status: GenerationStatus
    chapters: List[ChapterResult]
    total_word_count: int
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SnapshotInfo:
    """快照信息数据类"""
    id: str
    name: str
    description: Optional[str]
    created_at: str
    chapter: int
    node: str
    version: str = "1.0"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StateSnapshot:
    """状态快照数据类"""
    generation_state: Dict[str, Any]
    memory_state: Dict[str, Any]
    observability_state: Dict[str, Any]
    timestamp: str
    version: str = "1.0"


class NovelGeneratorService(ABC):
    """
    小说生成服务接口
    
    职责：
    - 接收并验证生成请求
    - 协调各节点完成内容生成
    - 管理生成进度和状态
    - 提供错误处理和重试机制
    """
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        执行小说生成
        
        Args:
            request: 生成请求
            
        Returns:
            GenerationResult: 生成结果
            
        Raises:
            GenerationError: 生成失败时
        """
        pass
    
    @abstractmethod
    async def generate_chapter(
        self,
        chapter_number: int,
        context: Dict[str, Any],
    ) -> ChapterResult:
        """
        生成单个章节
        
        Args:
            chapter_number: 章节号
            context: 生成上下文
            
        Returns:
            ChapterResult: 章节结果
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: GenerationRequest) -> bool:
        """
        验证生成请求
        
        Args:
            request: 生成请求
            
        Returns:
            bool: 验证是否通过
        """
        pass


class StateManagerService(ABC):
    """
    状态管理服务接口
    
    职责：
    - 维护生成过程状态
    - 提供状态查询和更新
    - 实现状态持久化
    - 支持状态变更通知
    """
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict[str, Any]: 当前状态
        """
        pass
    
    @abstractmethod
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        更新状态
        
        Args:
            updates: 状态更新
        """
        pass
    
    @abstractmethod
    def reset_state(self) -> None:
        """重置状态"""
        pass
    
    @abstractmethod
    def get_progress(self) -> GenerationProgress:
        """
        获取生成进度
        
        Returns:
            GenerationProgress: 生成进度
        """
        pass
    
    @abstractmethod
    def subscribe(self, callback: Callable[[str, Any], None]) -> str:
        """
        订阅状态变更
        
        Args:
            callback: 回调函数
            
        Returns:
            str: 订阅ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
        """
        pass
    
    @abstractmethod
    async def save_state(self) -> None:
        """保存状态到持久化存储"""
        pass
    
    @abstractmethod
    async def load_state(self) -> None:
        """从持久化存储加载状态"""
        pass


class SnapshotManagerService(ABC):
    """
    快照管理服务接口
    
    职责：
    - 创建和管理快照
    - 支持快照回滚
    - 实现版本控制
    - 管理快照元数据
    """
    
    @abstractmethod
    async def create_snapshot(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> SnapshotInfo:
        """
        创建快照
        
        Args:
            name: 快照名称
            description: 快照描述
            
        Returns:
            SnapshotInfo: 快照信息
        """
        pass
    
    @abstractmethod
    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        恢复快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 恢复是否成功
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    def list_snapshots(self) -> List[SnapshotInfo]:
        """
        获取快照列表
        
        Returns:
            List[SnapshotInfo]: 快照列表
        """
        pass
    
    @abstractmethod
    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotInfo]:
        """
        获取快照信息
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[SnapshotInfo]: 快照信息
        """
        pass
    
    @abstractmethod
    async def auto_snapshot(self, trigger: str) -> Optional[SnapshotInfo]:
        """
        自动创建快照
        
        Args:
            trigger: 触发条件
            
        Returns:
            Optional[SnapshotInfo]: 快照信息（如果不满足条件则返回None）
        """
        pass


class ServiceError(Exception):
    """服务层基础异常"""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class GenerationError(ServiceError):
    """生成服务异常"""
    
    def __init__(self, message: str, node: Optional[str] = None):
        self.node = node
        super().__init__(message, "GENERATION_ERROR")


class StateError(ServiceError):
    """状态服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "STATE_ERROR")


class SnapshotError(ServiceError):
    """快照服务异常"""
    
    def __init__(self, message: str, snapshot_id: Optional[str] = None):
        self.snapshot_id = snapshot_id
        super().__init__(message, "SNAPSHOT_ERROR")


@dataclass
class VersionInfo:
    """版本信息数据类"""
    index: int
    content: str
    created_at: str
    metrics: Dict[str, Any]
    is_selected: bool = False


@dataclass
class VersionSelectionResult:
    """版本选择结果数据类"""
    success: bool
    selected_version: int
    message: str
    previous_version: Optional[int] = None


class VersionSelectorService(ABC):
    """
    版本选择服务接口
    
    职责：
    - 管理节点生成的多个版本
    - 支持版本选择和切换
    - 记录版本历史
    - 提供版本比较功能
    """
    
    @abstractmethod
    def register_version(
        self,
        chapter_id: int,
        node_id: str,
        content: str,
        metrics: Dict[str, Any],
    ) -> int:
        """
        注册新版本
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            content: 版本内容
            metrics: 性能指标
            
        Returns:
            int: 版本索引
        """
        pass
    
    @abstractmethod
    def select_version(
        self,
        chapter_id: int,
        node_id: str,
        version_index: int,
    ) -> VersionSelectionResult:
        """
        选择版本
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            version_index: 版本索引
            
        Returns:
            VersionSelectionResult: 选择结果
        """
        pass
    
    @abstractmethod
    def get_versions(
        self,
        chapter_id: int,
        node_id: str,
    ) -> List[VersionInfo]:
        """
        获取版本列表
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            List[VersionInfo]: 版本列表
        """
        pass
    
    @abstractmethod
    def get_selected_version(
        self,
        chapter_id: int,
        node_id: str,
    ) -> Optional[VersionInfo]:
        """
        获取当前选中的版本
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            Optional[VersionInfo]: 选中的版本信息
        """
        pass
    
    @abstractmethod
    def clear_versions(
        self,
        chapter_id: int,
        node_id: str,
    ) -> bool:
        """
        清除版本历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            bool: 是否成功清除
        """
        pass


class VersionSelectionError(ServiceError):
    """版本选择服务异常"""
    
    def __init__(self, message: str, chapter_id: Optional[int] = None, node_id: Optional[str] = None):
        self.chapter_id = chapter_id
        self.node_id = node_id
        super().__init__(message, "VERSION_SELECTION_ERROR")


@dataclass
class NodeRetryResult:
    """节点重试结果数据类"""
    success: bool
    chapter_id: int
    node_id: str
    retry_count: int
    message: str
    previous_error: Optional[str] = None


class NodeRetryService(ABC):
    """
    节点重试服务接口
    
    职责：
    - 管理节点重试逻辑
    - 记录重试次数和历史
    - 支持最大重试次数限制
    - 提供重试策略配置
    """
    
    @abstractmethod
    async def retry_node(
        self,
        chapter_id: int,
        node_id: str,
    ) -> NodeRetryResult:
        """
        重试指定节点
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            NodeRetryResult: 重试结果
        """
        pass
    
    @abstractmethod
    def get_retry_count(
        self,
        chapter_id: int,
        node_id: str,
    ) -> int:
        """
        获取节点重试次数
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            int: 重试次数
        """
        pass
    
    @abstractmethod
    def can_retry(
        self,
        chapter_id: int,
        node_id: str,
        max_retries: int = 3,
    ) -> bool:
        """
        检查是否可以重试
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否可以重试
        """
        pass
    
    @abstractmethod
    def clear_retry_history(
        self,
        chapter_id: int,
        node_id: str,
    ) -> bool:
        """
        清除重试历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            bool: 是否成功清除
        """
        pass
    
    @abstractmethod
    def record_failure(
        self,
        chapter_id: int,
        node_id: str,
        error_message: str,
    ) -> None:
        """
        记录节点失败
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            error_message: 错误信息
        """
        pass


class NodeRetryError(ServiceError):
    """节点重试服务异常"""
    
    def __init__(self, message: str, chapter_id: Optional[int] = None, node_id: Optional[str] = None):
        self.chapter_id = chapter_id
        self.node_id = node_id
        super().__init__(message, "NODE_RETRY_ERROR")


@dataclass
class NodeRegenerateResult:
    """节点再生结果数据类"""
    success: bool
    chapter_id: int
    node_id: str
    status: str
    message: str
    previous_versions: int = 0


class NodeRegenerateService(ABC):
    """
    节点再生服务接口
    
    职责：
    - 管理节点内容再生
    - 触发指定章节和节点的重新生成
    - 记录再生历史
    - 支持版本管理集成
    """
    
    @abstractmethod
    async def regenerate_node(
        self,
        chapter_id: int,
        node_id: str,
    ) -> NodeRegenerateResult:
        """
        再生指定节点
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            NodeRegenerateResult: 再生结果
        """
        pass
    
    @abstractmethod
    def can_regenerate(
        self,
        chapter_id: int,
        node_id: str,
    ) -> bool:
        """
        检查是否可以再生节点
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            bool: 是否可以再生
        """
        pass
    
    @abstractmethod
    def get_regenerate_history(
        self,
        chapter_id: int,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """
        获取节点再生历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            List[Dict[str, Any]]: 再生历史记录列表
        """
        pass
    
    @abstractmethod
    def clear_regenerate_history(
        self,
        chapter_id: int,
        node_id: str,
    ) -> bool:
        """
        清除节点再生历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            bool: 是否成功清除
        """
        pass


class NodeRegenerateError(ServiceError):
    """节点再生服务异常"""
    
    def __init__(self, message: str, chapter_id: Optional[int] = None, node_id: Optional[str] = None):
        self.chapter_id = chapter_id
        self.node_id = node_id
        super().__init__(message, "NODE_REGENERATE_ERROR")


@dataclass
class PerformanceMetricsSummary:
    """性能指标汇总数据类"""
    total_chapters: int
    total_duration_min: float
    total_tokens: int
    total_cost_usd: float
    avg_chapter_time_min: float


@dataclass
class PerformanceMetricsData:
    """性能指标数据类"""
    per_node: List[Dict[str, Any]]
    per_chapter: List[Dict[str, Any]]
    summary: PerformanceMetricsSummary


class PerformanceMetricsService(ABC):
    """
    性能指标服务接口
    
    职责：
    - 收集和汇总性能指标
    - 提供性能数据查询
    - 支持节点/章节/总体三级指标
    - 成本计算和预估
    """
    
    @abstractmethod
    def get_performance_metrics(self) -> PerformanceMetricsData:
        """
        获取性能指标汇总
        
        Returns:
            PerformanceMetricsData: 性能指标数据
        """
        pass
    
    @abstractmethod
    def get_node_metrics(self) -> List[Dict[str, Any]]:
        """
        获取节点级性能指标
        
        Returns:
            List[Dict[str, Any]]: 节点指标列表
        """
        pass
    
    @abstractmethod
    def get_chapter_metrics(self) -> List[Dict[str, Any]]:
        """
        获取章节级性能指标
        
        Returns:
            List[Dict[str, Any]]: 章节指标列表
        """
        pass
    
    @abstractmethod
    def get_summary_metrics(self) -> PerformanceMetricsSummary:
        """
        获取总体性能指标汇总
        
        Returns:
            PerformanceMetricsSummary: 总体指标
        """
        pass
    
    @abstractmethod
    def clear_metrics(self) -> bool:
        """
        清除所有性能指标
        
        Returns:
            bool: 是否成功清除
        """
        pass


class PerformanceMetricsError(ServiceError):
    """性能指标服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "PERFORMANCE_METRICS_ERROR")


@dataclass
class ConfigSaveResult:
    """配置保存结果数据类"""
    success: bool
    status: str
    message: str
    updated_keys: List[str]


class ConfigManagerService(ABC):
    """
    配置管理服务接口
    
    职责：
    - 管理配置保存和更新
    - 支持部分配置更新（深度合并）
    - 配置验证
    - 动态重新加载
    """
    
    @abstractmethod
    async def save_config(self, config_updates: Dict[str, Any]) -> ConfigSaveResult:
        """
        保存配置更新
        
        Args:
            config_updates: 配置更新字典（支持部分更新）
            
        Returns:
            ConfigSaveResult: 保存结果
            
        Raises:
            ConfigManagerError: 保存失败时
        """
        pass
    
    @abstractmethod
    def get_current_config(self) -> Dict[str, Any]:
        """
        获取当前完整配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置是否有效
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 是否有效
        """
        pass
    
    @abstractmethod
    def reload_config(self) -> bool:
        """
        重新加载配置
        
        Returns:
            bool: 是否成功
        """
        pass


class ConfigManagerError(ServiceError):
    """配置管理服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_MANAGER_ERROR")


@dataclass
class DebugLogResult:
    """调试日志操作结果数据类"""
    success: bool
    status: str
    message: str
    content: Optional[str] = None
    exists: bool = False


class DebugLogService(ABC):
    """
    调试日志服务接口
    
    职责：
    - 读取调试日志内容
    - 清空调试日志
    - 切换调试模式
    - 写入调试日志
    """
    
    @abstractmethod
    def get_debug_log(self) -> DebugLogResult:
        """
        获取调试日志内容
        
        Returns:
            DebugLogResult: 调试日志内容和状态
            
        Raises:
            DebugLogError: 读取失败时
        """
        pass
    
    @abstractmethod
    def clear_debug_log(self) -> DebugLogResult:
        """
        清空调试日志
        
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 清除失败时
        """
        pass
    
    @abstractmethod
    def write_debug_log(self, message: str, level: str = "INFO") -> DebugLogResult:
        """
        写入调试日志
        
        Args:
            message: 日志消息
            level: 日志级别（DEBUG, INFO, WARNING, ERROR）
            
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 写入失败时
        """
        pass
    
    @abstractmethod
    def set_debug_mode(self, enabled: bool) -> DebugLogResult:
        """
        设置调试模式
        
        Args:
            enabled: 是否启用调试模式
            
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 设置失败时
        """
        pass
    
    @abstractmethod
    def get_debug_mode(self) -> bool:
        """
        获取当前调试模式状态
        
        Returns:
            bool: 是否启用调试模式
        """
        pass


class DebugLogError(ServiceError):
    """调试日志服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "DEBUG_LOG_ERROR")

@dataclass
class PipelineContext:
    """流水线上下文"""
    task_id: str
    request: GenerationRequest
    plan: Dict[str, Any]  # director_general 输出
    global_memory: List[str]
    current_chapter: int = 0
    current_node: str = ""
    chapter_results: List[ChapterResult] = None
    
    def __post_init__(self):
        if self.chapter_results is None:
            self.chapter_results = []


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    node_id: str
    node_type: str
    content: str
    passed_review: bool
    revision_needed: bool
    improvement_suggestions: str
    state_change_report: Dict[str, Any]
    metrics: Dict[str, Any]


class GenerationPipelineService(ABC):
    """
    生成流水线编排服务接口
    
    职责：
    - 编排完整的生成流程
    - 管理章节和节点迭代
    - 协调各 LLM 节点调用
    - 处理审查和重试逻辑
    - 触发人工干预
    """
    
    @abstractmethod
    async def execute_pipeline(
        self,
        context: PipelineContext,
        progress_callback: Callable[[GenerationProgress], None],
        token_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> GenerationResult:
        """
        执行完整生成流水线
        
        Args:
            context: 流水线上下文
            progress_callback: 进度回调
            token_callback: Token 流回调 (chapter, node, token)
            
        Returns:
            GenerationResult: 生成结果
        """
        pass
    
    @abstractmethod
    async def execute_chapter(
        self,
        chapter_number: int,
        context: PipelineContext,
    ) -> ChapterResult:
        """
        执行单个章节生成
        
        Args:
            chapter_number: 章节号
            context: 流水线上下文
            
        Returns:
            ChapterResult: 章节结果
        """
        pass
    
    @abstractmethod
    async def execute_node(
        self,
        node: Dict[str, Any],
        chapter_number: int,
        context: PipelineContext,
    ) -> NodeExecutionResult:
        """
        执行单个节点生成
        
        Args:
            node: 节点定义
            chapter_number: 章节号
            context: 流水线上下文
            
        Returns:
            NodeExecutionResult: 节点执行结果
        """
        pass
    
    @abstractmethod
    async def handle_node_revision(
        self,
        node_result: NodeExecutionResult,
        chapter_number: int,
        context: PipelineContext,
    ) -> tuple[bool, str]:
        """
        处理节点审查修订
        
        Args:
            node_result: 节点执行结果
            chapter_number: 章节号
            context: 流水线上下文
            
        Returns:
            Tuple[bool, str]: (是否通过, 改进建议)
        """
        pass

@dataclass
class WebSocketMessage:
    """WebSocket 消息"""
    type: str  # token, progress, status, log, complete, error, need_manual_review
    data: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class WebSocketBroadcastService(ABC):
    """
    WebSocket 广播服务接口
    
    职责：
    - 管理 WebSocket 客户端连接
    - 广播各类消息到所有客户端
    - 支持消息类型路由
    - 处理客户端断开
    """
    
    @abstractmethod
    def register_client(self, client: Any) -> str:
        """
        注册客户端
        
        Args:
            client: WebSocket 客户端对象
            
        Returns:
            str: 客户端ID
        """
        pass
    
    @abstractmethod
    def unregister_client(self, client_id: str) -> bool:
        """
        注销客户端
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    async def broadcast(self, message: WebSocketMessage) -> int:
        """
        广播消息到所有客户端
        
        Args:
            message: 消息对象
            
        Returns:
            int: 成功发送的客户端数量
        """
        pass
    
    @abstractmethod
    async def broadcast_token(
        self,
        chapter: int,
        node: str,
        token: str,
    ) -> int:
        """广播 token 流"""
        pass
    
    @abstractmethod
    async def broadcast_progress(
        self,
        current: int,
        total: int,
        percentage: float,
        current_node: str,
        estimated_remaining_cost: float = 0,
    ) -> int:
        """广播进度更新"""
        pass
    
    @abstractmethod
    async def broadcast_status(self, status: Dict[str, Any]) -> int:
        """广播状态更新"""
        pass
    
    @abstractmethod
    async def broadcast_log(
        self,
        level: str,
        chapter: int,
        node: str,
        message: str,
    ) -> int:
        """广播日志"""
        pass
    
    @abstractmethod
    async def broadcast_complete(self, result: Dict[str, Any]) -> int:
        """广播完成消息"""
        pass
    
    @abstractmethod
    async def broadcast_error(self, error: str) -> int:
        """广播错误"""
        pass
    
    @abstractmethod
    async def broadcast_intervention(self, data: Dict[str, Any]) -> int:
        """广播人工干预请求"""
        pass

@dataclass
class RAGSearchResult:
    """RAG 检索结果"""
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGRetrievalService(ABC):
    """
    RAG 检索服务接口
    
    职责：
    - 执行向量相似度检索
    - 管理检索上下文
    - 支持批量查询
    """
    
    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RAGSearchResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            List[RAGSearchResult]: 检索结果
        """
        pass
    
    @abstractmethod
    async def search_multiple(
        self,
        queries: List[str],
        top_k: int = 3,
    ) -> List[List[RAGSearchResult]]:
        """
        批量检索
        
        Args:
            queries: 查询列表
            top_k: 每个查询返回结果数量
            
        Returns:
            List[List[RAGSearchResult]]: 批量检索结果
        """
        pass
    
    @abstractmethod
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        添加文档到向量存储
        
        Args:
            content: 文档内容
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        清空所有检索数据
        
        用于开始新的小说生成任务时重置 RAG 存储
        
        Returns:
            bool: 是否成功清空
        """
        pass

@dataclass
class FileOutputResult:
    """文件输出结果"""
    success: bool
    file_path: str
    bytes_written: int
    message: str


class FileOutputService(ABC):
    """
    文件输出服务接口
    
    职责：
    - 管理输出文件创建和写入
    - 支持实时追加和最终保存
    - 管理文件命名和路径
    """
    
    @abstractmethod
    def create_output_file(self, task_id: str) -> str:
        """
        创建输出文件
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 文件路径
        """
        pass
    
    @abstractmethod
    async def append_content(
        self,
        file_path: str,
        content: str,
    ) -> FileOutputResult:
        """
        追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 内容
            
        Returns:
            FileOutputResult: 操作结果
        """
        pass
    
    @abstractmethod
    async def save_final(
        self,
        file_path: str,
        content: str,
    ) -> FileOutputResult:
        """
        保存最终内容
        
        Args:
            file_path: 文件路径
            content: 完整内容
            
        Returns:
            FileOutputResult: 操作结果
        """
        pass
    
    @abstractmethod
    async def save_polished_chapter(
        self,
        chapter_number: int,
        content: str,
        original_file_path: str,
    ) -> FileOutputResult:
        """
        保存润色后的章节
        
        Args:
            chapter_number: 章节号
            content: 润色内容
            original_file_path: 原始文件路径
            
        Returns:
            FileOutputResult: 操作结果
        """
        pass