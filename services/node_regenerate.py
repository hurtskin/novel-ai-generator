"""
节点再生服务实现

提供节点内容再生功能，支持指定章节和节点的重新生成
"""

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from interfaces import ObservabilityBackend, StorageBackend
from interfaces.observability import LogLevel
from services.interfaces import (
    NodeRegenerateService,
    NodeRegenerateResult,
    NodeRegenerateError,
)

logger = logging.getLogger(__name__)


class NodeRegenerateManager(NodeRegenerateService):
    """
    节点再生服务实现
    
    职责：
    - 管理节点内容再生
    - 触发指定章节和节点的重新生成
    - 记录再生历史
    - 支持版本管理集成
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        observability: ObservabilityBackend,
    ):
        """
        初始化节点再生服务
        
        Args:
            storage: 存储后端
            observability: 可观测性后端
        """
        self.storage = storage
        self.observability = observability
        
        # 再生历史: {(chapter_id, node_id): [RegenerateRecord, ...]}
        self._regenerate_history: Dict[tuple, List[Dict[str, Any]]] = {}
        
        # 再生计数: {(chapter_id, node_id): count}
        self._regenerate_counts: Dict[tuple, int] = {}
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info("NodeRegenerateManager initialized")
    
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
            
        Raises:
            NodeRegenerateError: 再生失败时
        """
        with self._lock:
            key = (chapter_id, node_id)
            
            # 检查是否可以再生
            if not self.can_regenerate(chapter_id, node_id):
                raise NodeRegenerateError(
                    f"Cannot regenerate node {node_id} in chapter {chapter_id}",
                    chapter_id,
                    node_id,
                )
            
            # 获取之前的版本数量
            previous_versions = self._regenerate_counts.get(key, 0)
            
            # 增加再生计数
            self._regenerate_counts[key] = previous_versions + 1
            
            # 记录再生历史
            record = {
                "timestamp": datetime.now().isoformat(),
                "chapter_id": chapter_id,
                "node_id": node_id,
                "version_number": previous_versions + 1,
            }
            
            if key not in self._regenerate_history:
                self._regenerate_history[key] = []
            self._regenerate_history[key].append(record)
            
            # 记录可观测性事件
            self.observability.log_event(
                level=LogLevel.INFO,
                chapter=chapter_id,
                node=node_id,
                message=f"Node regeneration initiated: chapter={chapter_id}, node={node_id}",
            )
            
            logger.info(
                f"Node regeneration: chapter={chapter_id}, node={node_id}, "
                f"count={self._regenerate_counts[key]}"
            )
            
            return NodeRegenerateResult(
                success=True,
                chapter_id=chapter_id,
                node_id=node_id,
                status="regenerating",
                message=f"Node {node_id} regeneration initiated",
                previous_versions=previous_versions,
            )
    
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
        with self._lock:
            # 基本验证：章节ID和节点ID必须有效
            if chapter_id < 1:
                return False
            if not node_id or not isinstance(node_id, str):
                return False
            
            # TODO: 可以添加更多业务逻辑验证
            # 例如：检查节点是否存在、是否正在生成中等
            
            return True
    
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
        with self._lock:
            key = (chapter_id, node_id)
            return list(self._regenerate_history.get(key, []))
    
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
        with self._lock:
            key = (chapter_id, node_id)
            
            if key in self._regenerate_history:
                del self._regenerate_history[key]
            
            if key in self._regenerate_counts:
                del self._regenerate_counts[key]
            
            logger.info(
                f"Regenerate history cleared: chapter={chapter_id}, node={node_id}"
            )
            
            return True
    
    def get_regenerate_count(
        self,
        chapter_id: int,
        node_id: str,
    ) -> int:
        """
        获取节点再生次数
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            int: 再生次数
        """
        with self._lock:
            key = (chapter_id, node_id)
            return self._regenerate_counts.get(key, 0)
