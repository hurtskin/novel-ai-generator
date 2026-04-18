"""
性能指标服务实现

提供性能指标收集、汇总和查询功能
"""

import logging
import threading
from typing import Any, Dict, List

from interfaces import ObservabilityBackend
from interfaces.observability import NodeMetrics, ChapterMetrics, TotalMetrics
from services.interfaces import (
    PerformanceMetricsService,
    PerformanceMetricsData,
    PerformanceMetricsSummary,
    PerformanceMetricsError,
)

logger = logging.getLogger(__name__)


class PerformanceMetricsCollector(PerformanceMetricsService):
    """
    性能指标收集器实现
    
    职责：
    - 收集和汇总性能指标
    - 提供性能数据查询
    - 支持节点/章节/总体三级指标
    - 成本计算和预估
    """
    
    def __init__(
        self,
        observability: ObservabilityBackend,
    ):
        """
        初始化性能指标收集器
        
        Args:
            observability: 可观测性后端
        """
        self.observability = observability
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info("PerformanceMetricsCollector initialized")
    
    def get_performance_metrics(self) -> PerformanceMetricsData:
        """
        获取性能指标汇总
        
        Returns:
            PerformanceMetricsData: 性能指标数据
            
        Raises:
            PerformanceMetricsError: 获取失败时
        """
        try:
            with self._lock:
                # 从可观测性后端获取性能汇总
                summary = self.observability.get_performance_summary()
                
                # 转换为 API 响应格式
                per_node = self._convert_node_metrics(summary.per_node)
                per_chapter = self._convert_chapter_metrics(summary.per_chapter)
                total = self._convert_total_metrics(summary.total)
                
                logger.debug(
                    f"Performance metrics retrieved: "
                    f"nodes={len(per_node)}, chapters={len(per_chapter)}"
                )
                
                return PerformanceMetricsData(
                    per_node=per_node,
                    per_chapter=per_chapter,
                    summary=total,
                )
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
            raise PerformanceMetricsError(f"Failed to get performance metrics: {str(e)}")
    
    def get_node_metrics(self) -> List[Dict[str, Any]]:
        """
        获取节点级性能指标
        
        Returns:
            List[Dict[str, Any]]: 节点指标列表
        """
        try:
            with self._lock:
                summary = self.observability.get_performance_summary()
                return self._convert_node_metrics(summary.per_node)
        except Exception as e:
            logger.error(f"Failed to get node metrics: {e}", exc_info=True)
            return []
    
    def get_chapter_metrics(self) -> List[Dict[str, Any]]:
        """
        获取章节级性能指标
        
        Returns:
            List[Dict[str, Any]]: 章节指标列表
        """
        try:
            with self._lock:
                summary = self.observability.get_performance_summary()
                return self._convert_chapter_metrics(summary.per_chapter)
        except Exception as e:
            logger.error(f"Failed to get chapter metrics: {e}", exc_info=True)
            return []
    
    def get_summary_metrics(self) -> PerformanceMetricsSummary:
        """
        获取总体性能指标汇总
        
        Returns:
            PerformanceMetricsSummary: 总体指标
        """
        try:
            with self._lock:
                summary = self.observability.get_performance_summary()
                return self._convert_total_metrics(summary.total)
        except Exception as e:
            logger.error(f"Failed to get summary metrics: {e}", exc_info=True)
            # 返回空指标
            return PerformanceMetricsSummary(
                total_chapters=0,
                total_duration_min=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                avg_chapter_time_min=0.0,
            )
    
    def clear_metrics(self) -> bool:
        """
        清除所有性能指标
        
        Returns:
            bool: 是否成功清除
        """
        with self._lock:
            # 注意：这里不实际清除 observability 中的数据
            # 因为那是历史记录，通常不应该被清除
            # 如果需要清除功能，需要在 ObservabilityBackend 中添加相应方法
            logger.info("Performance metrics clear requested (no-op)")
            return True
    
    def _convert_node_metrics(self, nodes: List[NodeMetrics]) -> List[Dict[str, Any]]:
        """
        转换节点指标为字典列表
        
        Args:
            nodes: 节点指标列表
            
        Returns:
            List[Dict[str, Any]]: 转换后的字典列表
        """
        return [
            {
                "node_id": node.node_id,
                "chapter": node.chapter,
                "model": node.model,
                "prompt_tokens": node.prompt_tokens,
                "completion_tokens": node.completion_tokens,
                "total_tokens": node.total_tokens,
                "ttf_ms": node.ttf_ms,
                "tps": node.tps,
                "duration_ms": node.duration_ms,
                "api_latency_ms": node.api_latency_ms,
                "retry_count": node.retry_count,
                "cost_usd": node.cost_usd,
                "timestamp": node.timestamp,
            }
            for node in nodes
        ]
    
    def _convert_chapter_metrics(self, chapters: List[ChapterMetrics]) -> List[Dict[str, Any]]:
        """
        转换章节指标为字典列表
        
        Args:
            chapters: 章节指标列表
            
        Returns:
            List[Dict[str, Any]]: 转换后的字典列表
        """
        return [
            {
                "chapter_id": chapter.chapter_id,
                "total_nodes": chapter.total_nodes,
                "total_duration_ms": chapter.total_duration_ms,
                "total_tokens": chapter.total_tokens,
                "total_retries": chapter.total_retries,
                "total_cost_usd": chapter.total_cost_usd,
                "avg_tps": chapter.avg_tps,
            }
            for chapter in chapters
        ]
    
    def _convert_total_metrics(self, total: TotalMetrics) -> PerformanceMetricsSummary:
        """
        转换总体指标为汇总数据类
        
        Args:
            total: 总体指标
            
        Returns:
            PerformanceMetricsSummary: 汇总数据类
        """
        return PerformanceMetricsSummary(
            total_chapters=total.total_chapters,
            total_duration_min=total.total_duration_ms / 60000.0,  # 转换为分钟
            total_tokens=total.total_tokens,
            total_cost_usd=total.total_cost_usd,
            avg_chapter_time_min=total.avg_chapter_time_min,
        )
