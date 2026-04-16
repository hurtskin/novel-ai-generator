"""
空可观测性后端实现

实现 ObservabilityBackend 接口作为空操作（No-Op）
用于禁用观测功能，减少性能开销
"""

from typing import Any, Dict, List, Optional

from interfaces.observability import (
    ObservabilityBackend,
    LogLevel,
    Span,
    NodeMetrics,
    ChapterMetrics,
    PerformanceSummary,
    TotalMetrics,
)


class NullObservabilityBackend(ObservabilityBackend):
    """
    空可观测性后端实现
    
    功能特性：
    - 所有操作都是空操作（No-Op）
    - 不产生任何副作用
    - 返回预期的默认值或空结果
    - 零性能开销
    
    适用场景：
    - 生产环境禁用观测
    - 测试环境减少干扰
    - 性能敏感场景
    """

    def __init__(self):
        """初始化空观测性后端"""
        pass

    def log_event(
        self,
        level: LogLevel,
        chapter: int,
        node: str,
        message: str
    ) -> None:
        """
        记录日志事件（空操作）
        
        Args:
            level: 日志级别
            chapter: 章节ID
            node: 节点ID
            message: 日志消息
        """
        pass

    def start_span(self, chapter: int, node: str) -> Span:
        """
        开始一个追踪 Span（返回空 Span）
        
        Args:
            chapter: 章节ID
            node: 节点ID
            
        Returns:
            Span: 空的 Span 对象
        """
        return Span(
            trace_id="",
            span_id="",
            chapter=chapter,
            node=node,
            event="enter",
            timestamp="",
        )

    def end_span(
        self,
        span: Span,
        usage: Dict[str, int],
        performance: Dict[str, float]
    ) -> None:
        """
        结束一个追踪 Span（空操作）
        
        Args:
            span: Span 对象
            usage: Token 使用统计
            performance: 性能指标
        """
        pass

    def record_node_metrics(self, metrics: NodeMetrics) -> None:
        """
        记录节点性能指标（空操作）
        
        Args:
            metrics: 节点指标数据
        """
        pass

    def record_chapter_metrics(self, metrics: ChapterMetrics) -> None:
        """
        记录章节性能指标（空操作）
        
        Args:
            metrics: 章节指标数据
        """
        pass

    def get_performance_summary(self) -> PerformanceSummary:
        """
        获取性能汇总报告（返回空汇总）
        
        Returns:
            PerformanceSummary: 空的性能汇总
        """
        return PerformanceSummary(
            per_node=[],
            per_chapter=[],
            total=TotalMetrics(
                total_chapters=0,
                total_duration_ms=0,
                total_tokens=0,
                total_cost_usd=0.0,
            ),
        )

    def register_ws_connection(self, connection: Any) -> None:
        """
        注册 WebSocket 连接（空操作）
        
        Args:
            connection: WebSocket 连接对象
        """
        pass

    def unregister_ws_connection(self, connection: Any) -> None:
        """
        注销 WebSocket 连接（空操作）
        
        Args:
            connection: WebSocket 连接对象
        """
        pass

    def broadcast(self, msg_type: str, data: Any) -> None:
        """
        广播消息到所有 WebSocket 连接（空操作）
        
        Args:
            msg_type: 消息类型
            data: 消息数据
        """
        pass

    def save_snapshot(
        self,
        state: Dict[str, Any],
        snapshot_id: Optional[str] = None
    ) -> str:
        """
        保存状态快照（返回空ID）
        
        Args:
            state: 应用状态
            snapshot_id: 快照ID（可选）
            
        Returns:
            str: 空字符串
        """
        return snapshot_id or ""

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        加载状态快照（返回 None）
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            None: 始终返回 None
        """
        return None

    def list_snapshots(self) -> List[str]:
        """
        列出所有快照ID（返回空列表）
        
        Returns:
            List[str]: 空列表
        """
        return []

    def close(self) -> None:
        """关闭观测性后端（空操作）"""
        pass
