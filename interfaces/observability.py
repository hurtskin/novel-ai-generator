"""
可观测性接口定义

定义日志、追踪、性能指标收集的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class NodeMetrics:
    """节点性能指标"""
    node_id: str
    chapter: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    ttf_ms: float  # Time To First Token
    tps: float  # Tokens Per Second
    duration_ms: float
    api_latency_ms: float
    retry_count: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChapterMetrics:
    """章节性能指标"""
    chapter_id: int
    total_nodes: int
    total_duration_ms: float
    total_tokens: int
    total_retries: int
    total_cost_usd: float
    avg_tps: float = 0.0


@dataclass
class TotalMetrics:
    """总体性能指标"""
    total_chapters: int
    total_duration_ms: float
    total_tokens: int
    total_cost_usd: float
    avg_chapter_time_min: float = 0.0


@dataclass
class Span:
    """追踪Span"""
    trace_id: str
    span_id: str
    chapter: int
    node: str
    event: str  # "enter" or "exit"
    timestamp: str
    duration_ms: Optional[float] = None
    output_hash: Optional[str] = None
    cost_usd: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


@dataclass
class PerformanceSummary:
    """性能汇总报告"""
    per_node: List[NodeMetrics]
    per_chapter: List[ChapterMetrics]
    total: TotalMetrics


class ObservabilityBackend(ABC):
    """
    可观测性后端抽象基类
    
    职责：
    - 日志记录
    - 分布式追踪
    - 性能指标收集
    - WebSocket广播
    
    实现类：
    - FileObservabilityBackend: 文件日志实现
    - NullObservabilityBackend: 空实现（禁用观测）
    """
    
    @abstractmethod
    def log_event(
        self,
        level: LogLevel,
        chapter: int,
        node: str,
        message: str
    ) -> None:
        """
        记录日志事件
        
        Args:
            level: 日志级别
            chapter: 章节ID
            node: 节点ID
            message: 日志消息
        """
        pass
    
    @abstractmethod
    def start_span(self, chapter: int, node: str) -> Span:
        """
        开始一个追踪Span
        
        Args:
            chapter: 章节ID
            node: 节点ID
            
        Returns:
            Span: Span对象
        """
        pass
    
    @abstractmethod
    def end_span(
        self,
        span: Span,
        usage: Dict[str, int],
        performance: Dict[str, float]
    ) -> None:
        """
        结束一个追踪Span
        
        Args:
            span: Span对象
            usage: Token使用统计
            performance: 性能指标
        """
        pass
    
    @abstractmethod
    def record_node_metrics(self, metrics: NodeMetrics) -> None:
        """
        记录节点性能指标
        
        Args:
            metrics: 节点指标数据
        """
        pass
    
    @abstractmethod
    def record_chapter_metrics(self, metrics: ChapterMetrics) -> None:
        """
        记录章节性能指标
        
        Args:
            metrics: 章节指标数据
        """
        pass
    
    @abstractmethod
    def get_performance_summary(self) -> PerformanceSummary:
        """
        获取性能汇总报告
        
        Returns:
            PerformanceSummary: 性能汇总
        """
        pass
    
    @abstractmethod
    def register_ws_connection(self, connection: Any) -> None:
        """
        注册WebSocket连接
        
        Args:
            connection: WebSocket连接对象
        """
        pass
    
    @abstractmethod
    def unregister_ws_connection(self, connection: Any) -> None:
        """
        注销WebSocket连接
        
        Args:
            connection: WebSocket连接对象
        """
        pass
    
    @abstractmethod
    def broadcast(self, msg_type: str, data: Any) -> None:
        """
        广播消息到所有WebSocket连接
        
        Args:
            msg_type: 消息类型
            data: 消息数据
        """
        pass
    
    @abstractmethod
    def save_snapshot(self, state: Dict[str, Any], snapshot_id: Optional[str] = None) -> str:
        """
        保存状态快照
        
        Args:
            state: 应用状态
            snapshot_id: 快照ID（可选）
            
        Returns:
            str: 快照ID
        """
        pass
    
    @abstractmethod
    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[Dict[str, Any]]: 状态数据，不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_snapshots(self) -> List[str]:
        """
        列出所有快照ID
        
        Returns:
            List[str]: 快照ID列表
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭观测性后端，释放资源"""
        pass


class ObservabilityFactory(ABC):
    """可观测性后端工厂"""
    
    @abstractmethod
    def create_backend(self, backend_type: str) -> ObservabilityBackend:
        """
        创建观测性后端
        
        Args:
            backend_type: 后端类型（"file", "null"）
            
        Returns:
            ObservabilityBackend: 观测性后端实例
        """
        pass
    
    @abstractmethod
    def get_default_backend(self) -> ObservabilityBackend:
        """获取默认观测性后端"""
        pass
