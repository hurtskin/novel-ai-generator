"""
版本选择服务实现

管理节点生成的多个版本，支持版本选择、切换和历史记录
"""

import logging
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime

from interfaces import ObservabilityBackend, StorageBackend
from interfaces.observability import LogLevel
from services.interfaces import (
    VersionSelectorService,
    VersionInfo,
    VersionSelectionResult,
    VersionSelectionError,
)

logger = logging.getLogger(__name__)


class VersionSelector(VersionSelectorService):
    """
    版本选择服务实现
    
    职责：
    - 管理节点生成的多个版本
    - 支持版本选择和切换
    - 记录版本历史
    - 提供版本比较功能
    
    Attributes:
        storage: 存储后端
        observability: 可观测性后端
        _versions: 版本存储字典 {(chapter_id, node_id): [VersionInfo]}
        _selected: 当前选中版本字典 {(chapter_id, node_id): int}
        _lock: 线程锁
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        observability: ObservabilityBackend,
    ):
        """
        初始化版本选择服务
        
        Args:
            storage: 存储后端
            observability: 可观测性后端
        """
        self.storage = storage
        self.observability = observability
        
        # 版本存储: {(chapter_id, node_id): [VersionInfo, ...]}
        self._versions: Dict[tuple, List[VersionInfo]] = {}
        
        # 当前选中版本: {(chapter_id, node_id): version_index}
        self._selected: Dict[tuple, int] = {}
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info("VersionSelector initialized")
    
    def _get_key(self, chapter_id: int, node_id: str) -> tuple:
        """
        生成存储键
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            
        Returns:
            tuple: 存储键
        """
        return (chapter_id, node_id)
    
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
            
        Raises:
            VersionSelectionError: 注册失败时
            
        Example:
            >>> version_idx = selector.register_version(
            ...     chapter_id=1,
            ...     node_id="role_actor_1",
            ...     content="生成的文本内容...",
            ...     metrics={"tokens": 100, "cost": 0.01}
            ... )
            >>> print(f"Registered version: {version_idx}")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            # 初始化版本列表
            if key not in self._versions:
                self._versions[key] = []
            
            # 生成新版本索引
            version_index = len(self._versions[key])
            
            # 创建版本信息
            version_info = VersionInfo(
                index=version_index,
                content=content,
                created_at=datetime.now().isoformat(),
                metrics=metrics,
                is_selected=False,
            )
            
            # 添加到版本列表
            self._versions[key].append(version_info)
            
            # 如果是第一个版本，自动选中
            if version_index == 0:
                self._selected[key] = 0
                version_info.is_selected = True
            
            # 记录日志
            self.observability.log_event(
                LogLevel.INFO,
                chapter_id,
                node_id,
                f"Version {version_index} registered",
            )
            
            logger.info(
                f"Version registered: chapter={chapter_id}, node={node_id}, "
                f"index={version_index}"
            )
            
            return version_index
    
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
            
        Raises:
            VersionSelectionError: 选择失败时
            
        Example:
            >>> result = selector.select_version(1, "role_actor_1", 0)
            >>> if result.success:
            ...     print(f"Selected version: {result.selected_version}")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            # 检查版本是否存在
            if key not in self._versions:
                raise VersionSelectionError(
                    f"No versions found for chapter {chapter_id}, node {node_id}",
                    chapter_id,
                    node_id,
                )
            
            versions = self._versions[key]
            
            # 检查版本索引是否有效
            if version_index < 0 or version_index >= len(versions):
                raise VersionSelectionError(
                    f"Invalid version index: {version_index}. "
                    f"Available: 0-{len(versions)-1}",
                    chapter_id,
                    node_id,
                )
            
            # 获取之前的选中版本
            previous_version = self._selected.get(key)
            
            # 更新选中状态
            if previous_version is not None and previous_version < len(versions):
                versions[previous_version].is_selected = False
            
            # 设置新版本
            self._selected[key] = version_index
            versions[version_index].is_selected = True
            
            # 记录日志
            self.observability.log_event(
                LogLevel.INFO,
                chapter_id,
                node_id,
                f"Version {version_index} selected (previous: {previous_version})",
            )
            
            logger.info(
                f"Version selected: chapter={chapter_id}, node={node_id}, "
                f"index={version_index}, previous={previous_version}"
            )
            
            return VersionSelectionResult(
                success=True,
                selected_version=version_index,
                previous_version=previous_version,
                message=f"Version {version_index} selected successfully",
            )
    
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
            
        Example:
            >>> versions = selector.get_versions(1, "role_actor_1")
            >>> for v in versions:
            ...     print(f"Version {v.index}: {v.created_at}")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._versions:
                return []
            
            # 返回副本
            return [
                VersionInfo(
                    index=v.index,
                    content=v.content,
                    created_at=v.created_at,
                    metrics=v.metrics.copy(),
                    is_selected=v.is_selected,
                )
                for v in self._versions[key]
            ]
    
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
            Optional[VersionInfo]: 选中的版本信息，不存在则返回None
            
        Example:
            >>> selected = selector.get_selected_version(1, "role_actor_1")
            >>> if selected:
            ...     print(f"Selected: Version {selected.index}")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._versions or key not in self._selected:
                return None
            
            selected_index = self._selected[key]
            versions = self._versions[key]
            
            if selected_index >= len(versions):
                return None
            
            v = versions[selected_index]
            return VersionInfo(
                index=v.index,
                content=v.content,
                created_at=v.created_at,
                metrics=v.metrics.copy(),
                is_selected=v.is_selected,
            )
    
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
            
        Example:
            >>> success = selector.clear_versions(1, "role_actor_1")
            >>> if success:
            ...     print("Versions cleared")
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._versions:
                return False
            
            # 删除版本和选中记录
            del self._versions[key]
            if key in self._selected:
                del self._selected[key]
            
            # 记录日志
            self.observability.log_event(
                LogLevel.INFO,
                chapter_id,
                node_id,
                "Versions cleared",
            )
            
            logger.info(f"Versions cleared: chapter={chapter_id}, node={node_id}")
            
            return True
    
    def get_version_content(
        self,
        chapter_id: int,
        node_id: str,
        version_index: int,
    ) -> Optional[str]:
        """
        获取指定版本的内容
        
        Args:
            chapter_id: 章节ID
            node_id: 节点ID
            version_index: 版本索引
            
        Returns:
            Optional[str]: 版本内容，不存在则返回None
        """
        with self._lock:
            key = self._get_key(chapter_id, node_id)
            
            if key not in self._versions:
                return None
            
            versions = self._versions[key]
            if version_index < 0 or version_index >= len(versions):
                return None
            
            return versions[version_index].content
    
    def clear_all_versions(self) -> int:
        """
        清除所有版本历史
        
        Returns:
            int: 清除的节点数量
            
        Example:
            >>> count = selector.clear_all_versions()
            >>> print(f"Cleared {count} nodes")
        """
        with self._lock:
            count = len(self._versions)
            self._versions.clear()
            self._selected.clear()
            
            logger.info(f"All versions cleared: {count} nodes")
            
            return count
