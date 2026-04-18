"""
文件可观测性后端实现

实现 ObservabilityBackend 接口，提供基于文件系统的观测功能
支持日志记录、追踪数据存储、性能指标收集和 WebSocket 广播
"""

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from interfaces.observability import (
    ObservabilityBackend,
    LogLevel,
    Span,
    NodeMetrics,
    ChapterMetrics,
    TotalMetrics,
    PerformanceSummary,
)


class FileObservabilityBackend(ObservabilityBackend):
    """
    文件可观测性后端实现
    
    功能特性：
    - 日志记录到文件（支持不同级别）
    - 分布式追踪数据存储（JSON Lines 格式）
    - 性能指标自动收集和汇总
    - WebSocket 连接管理
    - 状态快照保存和加载
    - 线程安全的单例模式
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True

        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        
        # 日志目录
        self._logs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        os.makedirs(self._logs_dir, exist_ok=True)

        # 时间戳和追踪ID
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._trace_id = f"novel_{self._timestamp}"

        # 日志文件
        self._log_file = os.path.join(self._logs_dir, f"novel_{self._timestamp}.log")
        self._trace_file = os.path.join(self._logs_dir, f"trace_{self._timestamp}.jsonl")

        # 数据存储
        self._spans: Dict[str, Dict] = {}
        self._node_metrics: List[NodeMetrics] = []
        self._chapter_metrics: Dict[int, ChapterMetrics] = {}
        self._total_metrics = TotalMetrics(
            total_chapters=0,
            total_duration_ms=0,
            total_tokens=0,
            total_cost_usd=0.0,
        )

        # WebSocket 连接
        self._ws_connections: List[Any] = []
        
        # 当前状态
        self._current_chapter = 0
        self._current_node = ""

        # 打开日志文件
        self._log_file_handle = open(self._log_file, "w", encoding="utf-8")

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_pricing(self) -> dict:
        """获取定价配置"""
        model = self._config.get("api", {}).get("model", "kimi-k2.5")
        return self._config.get("pricing", {}).get(model, {"input_per_million": 12, "output_per_million": 60})

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
        timestamp = datetime.now().isoformat()
        # 支持 LogLevel 枚举或字符串
        level_str = level.value if hasattr(level, 'value') else str(level)
        log_line = f"[{timestamp}] [{level_str}] [C{chapter}/N{node}] {message}\n"
        self._log_file_handle.write(log_line)
        self._log_file_handle.flush()

    def start_span(self, chapter: int, node: str) -> Span:
        """
        开始一个追踪 Span
        
        Args:
            chapter: 章节ID
            node: 节点ID
            
        Returns:
            Span: Span 对象
        """
        self._current_chapter = chapter
        self._current_node = node
        
        span_id = str(uuid.uuid4())[:8]
        span = Span(
            trace_id=self._trace_id,
            span_id=span_id,
            chapter=chapter,
            node=node,
            event="enter",
            timestamp=datetime.now().isoformat(),
        )
        
        self._spans[span_id] = {
            "trace_id": self._trace_id,
            "chapter": chapter,
            "node": node,
            "event": "enter",
            "timestamp": span.timestamp,
            "span_id": span_id,
        }
        
        # 写入追踪文件
        with open(self._trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(self._spans[span_id], ensure_ascii=False) + "\n")
        
        self.log_event(LogLevel.INFO, chapter, node, f"Node started, span_id={span_id}")
        
        return span

    def end_span(
        self,
        span: Span,
        usage: Dict[str, int],
        performance: Dict[str, float]
    ) -> None:
        """
        结束一个追踪 Span
        
        Args:
            span: Span 对象
            usage: Token 使用统计
            performance: 性能指标
        """
        span_id = span.span_id
        if span_id not in self._spans:
            return

        self._spans.pop(span_id)
        
        duration_ms = performance.get("duration_ms", 0)
        output_hash = hashlib.md5(str(usage).encode()).hexdigest()[:6]

        pricing = self._get_pricing()
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost_usd = (
            prompt_tokens * pricing["input_per_million"] + 
            completion_tokens * pricing["output_per_million"]
        ) / 1_000_000

        # 创建退出 Span
        exit_span = {
            "trace_id": self._trace_id,
            "chapter": self._current_chapter,
            "node": self._current_node,
            "event": "exit",
            "duration_ms": duration_ms,
            "output_hash": output_hash,
            "cost_usd": round(cost_usd, 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(self._trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(exit_span, ensure_ascii=False) + "\n")

        # 记录节点指标
        node_metric = NodeMetrics(
            node_id=self._current_node,
            chapter=self._current_chapter,
            model=self._config.get("api", {}).get("model", "kimi-k2.5"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            ttf_ms=performance.get("ttf_ms", 0),
            tps=performance.get("tps", 0),
            duration_ms=duration_ms,
            api_latency_ms=performance.get("api_latency_ms", 0),
            retry_count=int(performance.get("retry_count", 0)),
            cost_usd=round(cost_usd, 6),
        )
        self._node_metrics.append(node_metric)

        # 更新章节指标
        if self._current_chapter not in self._chapter_metrics:
            self._chapter_metrics[self._current_chapter] = ChapterMetrics(
                chapter_id=self._current_chapter,
                total_nodes=0,
                total_duration_ms=0,
                total_tokens=0,
                total_retries=0,
                total_cost_usd=0.0,
            )
        
        chapter_metric = self._chapter_metrics[self._current_chapter]
        chapter_metric.total_nodes += 1
        chapter_metric.total_duration_ms += duration_ms
        chapter_metric.total_tokens += prompt_tokens + completion_tokens
        chapter_metric.total_retries += int(performance.get("retry_count", 0))
        chapter_metric.total_cost_usd += cost_usd

        # 更新总体指标
        self._total_metrics.total_duration_ms += duration_ms
        self._total_metrics.total_tokens += prompt_tokens + completion_tokens
        self._total_metrics.total_cost_usd += cost_usd

        self.log_event(
            LogLevel.INFO,
            self._current_chapter,
            self._current_node,
            f"Node completed, duration={duration_ms}ms, cost=${cost_usd:.4f}"
        )

    def record_node_metrics(self, metrics: NodeMetrics) -> None:
        """
        记录节点性能指标
        
        Args:
            metrics: 节点指标数据
        """
        self._node_metrics.append(metrics)
        
        # 更新章节指标
        if metrics.chapter not in self._chapter_metrics:
            self._chapter_metrics[metrics.chapter] = ChapterMetrics(
                chapter_id=metrics.chapter,
                total_nodes=0,
                total_duration_ms=0,
                total_tokens=0,
                total_retries=0,
                total_cost_usd=0.0,
            )
        
        chapter_metric = self._chapter_metrics[metrics.chapter]
        chapter_metric.total_nodes += 1
        chapter_metric.total_duration_ms += metrics.duration_ms
        chapter_metric.total_tokens += metrics.total_tokens
        chapter_metric.total_retries += metrics.retry_count
        chapter_metric.total_cost_usd += metrics.cost_usd

        # 更新总体指标
        self._total_metrics.total_duration_ms += metrics.duration_ms
        self._total_metrics.total_tokens += metrics.total_tokens
        self._total_metrics.total_cost_usd += metrics.cost_usd

    def record_chapter_metrics(self, metrics: ChapterMetrics) -> None:
        """
        记录章节性能指标
        
        Args:
            metrics: 章节指标数据
        """
        self._chapter_metrics[metrics.chapter_id] = metrics

    def get_performance_summary(self) -> PerformanceSummary:
        """
        获取性能汇总报告
        
        Returns:
            PerformanceSummary: 性能汇总
        """
        total_chapters = len(self._chapter_metrics)
        total_duration_min = self._total_metrics.total_duration_ms / 60000
        avg_chapter_time_min = total_duration_min / total_chapters if total_chapters > 0 else 0

        # 构建章节汇总
        chapter_summaries = []
        for ch in sorted(self._chapter_metrics.keys()):
            cm = self._chapter_metrics[ch]
            avg_tps = (
                cm.total_tokens / (cm.total_duration_ms / 1000) 
                if cm.total_duration_ms > 0 else 0
            )
            chapter_summaries.append(ChapterMetrics(
                chapter_id=ch,
                total_nodes=cm.total_nodes,
                total_duration_ms=cm.total_duration_ms,
                total_tokens=cm.total_tokens,
                total_retries=cm.total_retries,
                total_cost_usd=round(cm.total_cost_usd, 6),
                avg_tps=avg_tps,
            ))

        # 更新总体指标
        self._total_metrics.total_chapters = total_chapters
        self._total_metrics.avg_chapter_time_min = round(avg_chapter_time_min, 2)

        return PerformanceSummary(
            per_node=self._node_metrics.copy(),
            per_chapter=chapter_summaries,
            total=self._total_metrics,
        )

    def register_ws_connection(self, connection: Any) -> None:
        """
        注册 WebSocket 连接
        
        Args:
            connection: WebSocket 连接对象
        """
        if connection not in self._ws_connections:
            self._ws_connections.append(connection)

    def unregister_ws_connection(self, connection: Any) -> None:
        """
        注销 WebSocket 连接
        
        Args:
            connection: WebSocket 连接对象
        """
        if connection in self._ws_connections:
            self._ws_connections.remove(connection)

    def broadcast(self, msg_type: str, data: Any) -> None:
        """
        广播消息到所有 WebSocket 连接
        
        Args:
            msg_type: 消息类型
            data: 消息数据
        """
        message = json.dumps({"type": msg_type, "data": data}, ensure_ascii=False)
        print(f"[BROADCAST] type={msg_type}, connections={len(self._ws_connections)}")
        
        dead_connections = []
        for ws in self._ws_connections:
            try:
                ws.send(message)
                print(f"[BROADCAST] sent to one connection")
            except Exception as e:
                print(f"[BROADCAST] error: {e}")
                dead_connections.append(ws)
        
        for dead in dead_connections:
            self.unregister_ws_connection(dead)

    def save_snapshot(
        self,
        state: Dict[str, Any],
        snapshot_id: Optional[str] = None
    ) -> str:
        """
        保存状态快照
        
        Args:
            state: 应用状态
            snapshot_id: 快照ID（可选）
            
        Returns:
            str: 快照ID
        """
        if snapshot_id is None:
            snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        snapshot_dir = os.path.join(self._logs_dir, "snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)

        snapshot_data = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": self._trace_id,
            "generation_state": state,
            "node_metrics": [
                {
                    "node_id": m.node_id,
                    "chapter": m.chapter,
                    "model": m.model,
                    "prompt_tokens": m.prompt_tokens,
                    "completion_tokens": m.completion_tokens,
                    "total_tokens": m.total_tokens,
                    "ttf_ms": m.ttf_ms,
                    "tps": m.tps,
                    "duration_ms": m.duration_ms,
                    "api_latency_ms": m.api_latency_ms,
                    "retry_count": m.retry_count,
                    "cost_usd": m.cost_usd,
                    "timestamp": m.timestamp,
                }
                for m in self._node_metrics
            ],
            "chapter_metrics": {
                str(k): {
                    "chapter_id": v.chapter_id,
                    "total_nodes": v.total_nodes,
                    "total_duration_ms": v.total_duration_ms,
                    "total_tokens": v.total_tokens,
                    "total_retries": v.total_retries,
                    "total_cost_usd": v.total_cost_usd,
                    "avg_tps": v.avg_tps,
                }
                for k, v in self._chapter_metrics.items()
            },
            "total_metrics": {
                "total_chapters": self._total_metrics.total_chapters,
                "total_duration_ms": self._total_metrics.total_duration_ms,
                "total_tokens": self._total_metrics.total_tokens,
                "total_cost_usd": self._total_metrics.total_cost_usd,
                "avg_chapter_time_min": self._total_metrics.avg_chapter_time_min,
            },
        }

        snapshot_path = os.path.join(snapshot_dir, f"{snapshot_id}.json")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

        self.log_event(LogLevel.INFO, self._current_chapter, "SNAPSHOT", f"Saved snapshot: {snapshot_id}")
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[Dict[str, Any]]: 状态数据，不存在则返回None
        """
        snapshot_dir = os.path.join(self._logs_dir, "snapshots")
        snapshot_path = os.path.join(snapshot_dir, f"{snapshot_id}.json")

        if not os.path.exists(snapshot_path):
            self.log_event(LogLevel.WARNING, 0, "SNAPSHOT", f"Snapshot not found: {snapshot_id}")
            return None

        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)

        # 恢复指标数据
        node_metrics_data = snapshot_data.get("node_metrics", [])
        self._node_metrics = [
            NodeMetrics(
                node_id=m["node_id"],
                chapter=m["chapter"],
                model=m["model"],
                prompt_tokens=m["prompt_tokens"],
                completion_tokens=m["completion_tokens"],
                total_tokens=m["total_tokens"],
                ttf_ms=m["ttf_ms"],
                tps=m["tps"],
                duration_ms=m["duration_ms"],
                api_latency_ms=m["api_latency_ms"],
                retry_count=m["retry_count"],
                cost_usd=m["cost_usd"],
                timestamp=m["timestamp"],
            )
            for m in node_metrics_data
        ]

        chapter_metrics_data = snapshot_data.get("chapter_metrics", {})
        self._chapter_metrics = {
            int(k): ChapterMetrics(
                chapter_id=v["chapter_id"],
                total_nodes=v["total_nodes"],
                total_duration_ms=v["total_duration_ms"],
                total_tokens=v["total_tokens"],
                total_retries=v["total_retries"],
                total_cost_usd=v["total_cost_usd"],
                avg_tps=v.get("avg_tps", 0.0),
            )
            for k, v in chapter_metrics_data.items()
        }

        total_data = snapshot_data.get("total_metrics", {})
        self._total_metrics = TotalMetrics(
            total_chapters=total_data.get("total_chapters", 0),
            total_duration_ms=total_data.get("total_duration_ms", 0),
            total_tokens=total_data.get("total_tokens", 0),
            total_cost_usd=total_data.get("total_cost_usd", 0.0),
            avg_chapter_time_min=total_data.get("avg_chapter_time_min", 0.0),
        )

        self.log_event(LogLevel.INFO, 0, "SNAPSHOT", f"Loaded snapshot: {snapshot_id}")
        return snapshot_data

    def list_snapshots(self) -> List[str]:
        """
        列出所有快照ID
        
        Returns:
            List[str]: 快照ID列表
        """
        snapshot_dir = os.path.join(self._logs_dir, "snapshots")
        if not os.path.exists(snapshot_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(snapshot_dir) if f.endswith(".json")]

    def close(self) -> None:
        """关闭观测性后端，释放资源"""
        if hasattr(self, "_log_file_handle") and self._log_file_handle:
            self._log_file_handle.close()
        FileObservabilityBackend._instance = None

    def get_node_metrics(self) -> List[NodeMetrics]:
        """获取所有节点指标"""
        return self._node_metrics.copy()

    def get_chapter_metrics(self, chapter: int) -> Optional[ChapterMetrics]:
        """获取指定章节指标"""
        return self._chapter_metrics.get(chapter)

    def get_total_metrics(self) -> TotalMetrics:
        """获取总体指标"""
        return self._total_metrics
