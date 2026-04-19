"""
节点重试服务实现

管理节点重试逻辑，记录重试次数和历史
"""

import logging
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime

from interfaces import ObservabilityBackend, StorageBackend
from interfaces.observability import LogLevel
from services.interfaces import (
    NodeRetryService,
    NodeRetryResult,
    NodeRetryError,
    PendingRetryInfo,
)

logger = logging.getLogger(__name__)


class NodeRetryManager(NodeRetryService):
    """
    节点重试服务实现
    
    职责：
    - 管理节点重试逻辑
    - 记录重试次数和历史
    - 支持最大重试次数限制
    - 提供重试策略配置
    
    Attributes:
        storage: 存储后端
        observability: 可观测性后端
        _retry_counts: 重试次数存储 {(chapter_id, node_id): count}
        _retry_history: 重试历史 {(chapter_id, node_id): [RetryRecord, ...]}
        _lock: 线程锁
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        observability: ObservabilityBackend,
    ):
        """
        初始化节点重试服务
        
        Args:
            storage: 存储后端
            observability: 可观测性后端
        """
        self.storage = storage
        self.observability = observability
        
        # 重试次数存储: {(chapter_id, node_id): count}
        self._retry_counts: Dict[tuple, int] = {}
        
        # 重试历史: {(chapter_id, node_id): [RetryRecord, ...]}
        self._retry_history: Dict[tuple, List[Dict[str, Any]]] = {}
        
        # 节点错误记录: {(chapter_id, node_id): error_message}
        self._node_errors: Dict[tuple, str] = {}
        
        # 待重试节点信息（人工干预时使用）
        self._pending_retry: Optional[Dict[str, Any]] = None
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info("NodeRetryManager initialized")
    
    def _get_key(self, chapter_id: int, node_id: int) -> tuple:
        """
        生成存储键
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            tuple: 存储键
        """
        return (chapter_id, node_id)
    
    async def retry_node(
        self,
        chapter_id: int,
        node_id: int,
    ) -> NodeRetryResult:
        """
        重试指定节点
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            NodeRetryResult: 重试结果
            
        Raises:
            NodeRetryError: 重试失败时
            
        Example:
            >>> result = await retry_manager.retry_node(1, "role_actor_1")
            >>> if result.success:
            ...     print(f"Retry {result.retry_count} initiated")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            # 获取当前重试次数
            current_count = self._retry_counts.get(key, 0)
            
            # 获取之前的错误信息
            previous_error = self._node_errors.get(key)
            
            # 增加重试次数
            new_count = current_count + 1
            self._retry_counts[key] = new_count
            
            # 记录重试历史
            if key not in self._retry_history:
                self._retry_history[key] = []
            
            retry_record = {
                "retry_count": new_count,
                "timestamp": datetime.now().isoformat(),
                "previous_error": previous_error,
            }
            self._retry_history[key].append(retry_record)
            
            # 清除错误记录（准备新的尝试）
            if key in self._node_errors:
                del self._node_errors[key]
            
            # 记录日志
            self.observability.log_event(
                LogLevel.INFO,
                chapter_id,
                node_id,
                f"Node retry initiated (attempt {new_count})",
            )
            
            logger.info(
                f"Node retry: chapter={chapter_id}, node={node_id}, "
                f"retry_count={new_count}"
            )
            
            return NodeRetryResult(
                success=True,
                chapter_id=chapter_id,
                node_id=node_id,
                retry_count=new_count,
                message=f"Retry attempt {new_count} initiated for node {node_id}",
                previous_error=previous_error,
            )
    
    def get_retry_count(
        self,
        chapter_id: int,
        node_id: int,
    ) -> int:
        """
        获取节点重试次数
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            int: 重试次数
            
        Example:
            >>> count = retry_manager.get_retry_count(1, "role_actor_1")
            >>> print(f"Node has been retried {count} times")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            return self._retry_counts.get(key, 0)
    
    def can_retry(
        self,
        chapter_id: int,
        node_id: int,
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
            
        Example:
            >>> if retry_manager.can_retry(1, "role_actor_1", max_retries=5):
            ...     await retry_manager.retry_node(1, "role_actor_1")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            current_count = self._retry_counts.get(key, 0)
            return current_count < max_retries
    
    def clear_retry_history(
        self,
        chapter_id: int,
        node_id: int,
    ) -> bool:
        """
        清除重试历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            bool: 是否成功清除
            
        Example:
            >>> success = retry_manager.clear_retry_history(1, "role_actor_1")
            >>> if success:
            ...     print("Retry history cleared")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._retry_counts and key not in self._retry_history:
                return False
            
            # 删除重试记录
            if key in self._retry_counts:
                del self._retry_counts[key]
            
            if key in self._retry_history:
                del self._retry_history[key]
            
            if key in self._node_errors:
                del self._node_errors[key]
            
            # 记录日志
            self.observability.log_event(
                LogLevel.INFO,
                chapter_id,
                node_id,
                "Retry history cleared",
            )
            
            logger.info(
                f"Retry history cleared: chapter={chapter_id}, node={node_id}"
            )
            
            return True
    
    def record_failure(
        self,
        chapter_id: int,
        node_id: int,
        error_message: str,
    ) -> None:
        """
        记录节点失败
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            error_message: 错误信息
            
        Example:
            >>> retry_manager.record_failure(1, "role_actor_1", "API timeout")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            # 记录错误信息
            self._node_errors[key] = error_message
            
            # 记录到重试历史
            if key not in self._retry_history:
                self._retry_history[key] = []
            
            # 更新最后一条重试记录的错误信息
            if self._retry_history[key]:
                self._retry_history[key][-1]["error"] = error_message
            
            # 记录日志
            self.observability.log_event(
                LogLevel.ERROR,
                chapter_id,
                node_id,
                f"Node failed: {error_message}",
            )
            
            logger.error(
                f"Node failure recorded: chapter={chapter_id}, node={node_id}, "
                f"error={error_message}"
            )
    
    def get_retry_history(
        self,
        chapter_id: int,
        node_id: int,
    ) -> List[Dict[str, Any]]:
        """
        获取重试历史
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            List[Dict[str, Any]]: 重试历史记录
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._retry_history:
                return []
            
            # 返回副本
            return [
                {
                    "retry_count": record["retry_count"],
                    "timestamp": record["timestamp"],
                    "previous_error": record.get("previous_error"),
                    "error": record.get("error"),
                }
                for record in self._retry_history[key]
            ]
    
    def get_last_error(
        self,
        chapter_id: int,
        node_id: int,
    ) -> Optional[str]:
        """
        获取节点最后一次错误信息
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            Optional[str]: 错误信息，不存在则返回None
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            return self._node_errors.get(key)
    
    def clear_all_retry_history(self) -> int:
        """
        清除所有重试历史
        
        Returns:
            int: 清除的节点数量
            
        Example:
            >>> count = retry_manager.clear_all_retry_history()
            >>> print(f"Cleared {count} nodes")
        """
        with self._lock:
            count = len(self._retry_counts)
            self._retry_counts.clear()
            self._retry_history.clear()
            self._node_errors.clear()
            self._pending_retry = None
            
            logger.info(f"All retry history cleared: {count} nodes")
            
            return count

    def set_pending_retry(
        self,
        chapter_id: int,
        node_id: int,
        node_index: int,
        versions: List[Dict[str, Any]],
    ) -> None:
        """
        设置待重试节点（人工干预时调用）
        
        当节点超过最大重试次数触发人工干预时，将失败节点信息存储，
        供后续重试端点查询使用。
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            node_index: 节点索引
            versions: 节点版本历史
        """
        with self._lock:
            self._pending_retry = {
                "chapter_id": chapter_id,
                "node_id": node_id,
                "node_index": node_index,
                "versions": versions,
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(
                f"Pending retry set: chapter={chapter_id}, node={node_id}, "
                f"index={node_index}"
            )

    def get_pending_retry(self) -> Optional[PendingRetryInfo]:
        """
        获取待重试节点信息（重试端点调用）
        
        Returns:
            Optional[PendingRetryInfo]: 待重试节点信息，如果没有则返回 None
        """
        with self._lock:
            if self._pending_retry is None:
                return None
            
            return PendingRetryInfo(
                chapter_id=self._pending_retry["chapter_id"],
                node_id=self._pending_retry["node_id"],
                node_index=self._pending_retry["node_index"],
                versions=self._pending_retry["versions"],
                timestamp=self._pending_retry["timestamp"],
            )

    def clear_pending_retry(self) -> None:
        """
        清除待重试状态（重试成功后调用）
        """
        with self._lock:
            if self._pending_retry is not None:
                logger.info(
                    f"Pending retry cleared: chapter={self._pending_retry['chapter_id']}, "
                    f"node={self._pending_retry['node_id']}"
                )
                self._pending_retry = None
