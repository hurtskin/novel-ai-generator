"""
状态管理服务实现

维护小说生成过程中的状态信息，提供状态查询、更新、持久化功能
"""

import asyncio
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from interfaces import StorageBackend, ObservabilityBackend
from services.interfaces import (
    StateManagerService,
    GenerationProgress,
    GenerationStatus,
    StateSnapshot,
    StateError,
)

logger = logging.getLogger(__name__)


class StateManager(StateManagerService):
    """
    状态管理服务实现
    
    职责：
    - 维护生成过程状态
    - 提供状态查询和更新
    - 实现状态持久化
    - 支持状态变更通知
    
    Attributes:
        storage: 存储后端
        observability: 可观测性后端
        _state: 当前状态字典
        _lock: 线程锁
        _subscribers: 订阅者字典
        _subscriber_counter: 订阅者计数器
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        observability: ObservabilityBackend,
    ):
        """
        初始化状态管理服务
        
        Args:
            storage: 存储后端
            observability: 可观测性后端
        """
        self.storage = storage
        self.observability = observability
        
        # 初始化状态
        self._state: Dict[str, Any] = {
            "is_running": False,
            "is_paused": False,
            "is_stopped": False,
            "current_chapter": 0,
            "total_chapters": 0,
            "current_node": "",
            "progress": 0.0,
            "error": None,
            "novel_content": "",
            "chapter_feedback": "",
            "need_human_intervention": False,
            "intervention_data": None,
        }
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 订阅管理
        self._subscribers: Dict[str, Callable[[str, Any], None]] = {}
        self._subscriber_counter = 0
        
        logger.info("StateManager initialized")
    
    def get_state(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict[str, Any]: 当前状态的副本
            
        Example:
            >>> state = manager.get_state()
            >>> print(f"Current chapter: {state['current_chapter']}")
        """
        with self._lock:
            return self._state.copy()
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        更新状态
        
        线程安全的批量更新操作
        
        Args:
            updates: 状态更新字典
            
        Example:
            >>> manager.update_state({"current_chapter": 5, "progress": 50.0})
        """
        with self._lock:
            old_state = self._state.copy()
            self._state.update(updates)
            
            # 记录变更
            changed_keys = [k for k in updates.keys() if old_state.get(k) != updates[k]]
            if changed_keys:
                logger.debug(f"State updated: {changed_keys}")
                
                # 通知订阅者
                for key in changed_keys:
                    self._notify_subscribers(key, self._state[key])
    
    def reset_state(self) -> None:
        """
        重置状态
        
        将所有状态重置为初始值
        
        Example:
            >>> manager.reset_state()
            >>> assert manager.get_state()['current_chapter'] == 0
        """
        with self._lock:
            self._state = {
                "is_running": False,
                "is_paused": False,
                "is_stopped": False,
                "current_chapter": 0,
                "total_chapters": 0,
                "current_node": "",
                "progress": 0.0,
                "error": None,
                "novel_content": "",
                "chapter_feedback": "",
                "need_human_intervention": False,
                "intervention_data": None,
            }
            
            logger.info("State reset to initial values")
            self._notify_subscribers("reset", None)
    
    def get_progress(self) -> GenerationProgress:
        """
        获取生成进度
        
        Returns:
            GenerationProgress: 生成进度对象
            
        Example:
            >>> progress = manager.get_progress()
            >>> print(f"Progress: {progress.percentage:.1f}%")
        """
        with self._lock:
            state = self._state
            
            # 计算百分比
            percentage = 0.0
            if state.get("total_chapters", 0) > 0:
                percentage = (state.get("current_chapter", 0) / state["total_chapters"]) * 100
            
            # 确定状态
            status = GenerationStatus.PENDING
            if state.get("is_running"):
                status = GenerationStatus.RUNNING
                if state.get("is_paused"):
                    status = GenerationStatus.PAUSED
            elif state.get("is_stopped"):
                status = GenerationStatus.STOPPED
            elif state.get("error"):
                status = GenerationStatus.FAILED
            elif state.get("current_chapter", 0) >= state.get("total_chapters", 0) and state.get("total_chapters", 0) > 0:
                status = GenerationStatus.COMPLETED
            
            return GenerationProgress(
                current_chapter=state.get("current_chapter", 0),
                total_chapters=state.get("total_chapters", 0),
                current_node=state.get("current_node", ""),
                percentage=percentage,
                status=status,
                message=state.get("error") if status == GenerationStatus.FAILED else None,
            )
    
    def subscribe(self, callback: Callable[[str, Any], None]) -> str:
        """
        订阅状态变更
        
        Args:
            callback: 回调函数，接收 (key, value) 参数
            
        Returns:
            str: 订阅ID，用于取消订阅
            
        Example:
            >>> def on_state_change(key, value):
            ...     print(f"State {key} changed to {value}")
            >>> sub_id = manager.subscribe(on_state_change)
        """
        with self._lock:
            self._subscriber_counter += 1
            subscription_id = f"sub_{self._subscriber_counter}"
            self._subscribers[subscription_id] = callback
            logger.debug(f"New subscriber: {subscription_id}")
            return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> None:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Example:
            >>> manager.unsubscribe(sub_id)
        """
        with self._lock:
            if subscription_id in self._subscribers:
                del self._subscribers[subscription_id]
                logger.debug(f"Unsubscribed: {subscription_id}")
    
    def _notify_subscribers(self, key: str, value: Any) -> None:
        """
        通知所有订阅者
        
        Args:
            key: 变更的状态键
            value: 新值
        """
        for callback in list(self._subscribers.values()):
            try:
                callback(key, value)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def save_state(self) -> None:
        """
        保存状态到持久化存储
        
        将当前状态保存到存储后端
        
        Example:
            >>> await manager.save_state()
        """
        with self._lock:
            snapshot = StateSnapshot(
                generation_state=self._state.copy(),
                memory_state={},  # 实际应该从 memory_store 获取
                observability_state={},  # 实际应该从 observability 获取
                timestamp=datetime.now().isoformat(),
            )
            
            try:
                self.storage.save("state:current", snapshot.__dict__)
                logger.info("State saved to storage")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
                raise StateError(f"Failed to save state: {str(e)}")
    
    async def load_state(self) -> None:
        """
        从持久化存储加载状态
        
        从存储后端恢复状态
        
        Example:
            >>> await manager.load_state()
        """
        try:
            data = self.storage.load("state:current")
            
            if data:
                with self._lock:
                    if isinstance(data, dict):
                        if "generation_state" in data:
                            self._state.update(data["generation_state"])
                        else:
                            self._state.update(data)
                    
                    logger.info("State loaded from storage")
            else:
                logger.info("No saved state found, using initial state")
                
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            raise StateError(f"Failed to load state: {str(e)}")
    
    def set_running(self, running: bool) -> None:
        """设置运行状态"""
        self.update_state({"is_running": running})
    
    def set_paused(self, paused: bool) -> None:
        """设置暂停状态"""
        self.update_state({"is_paused": paused})
    
    def set_stopped(self, stopped: bool) -> None:
        """设置停止状态"""
        self.update_state({"is_stopped": stopped})
    
    def set_chapter(self, chapter: int) -> None:
        """设置当前章节"""
        self.update_state({"current_chapter": chapter})
    
    def set_total_chapters(self, total: int) -> None:
        """设置总章节数"""
        self.update_state({"total_chapters": total})
    
    def set_current_node(self, node: str) -> None:
        """设置当前节点"""
        self.update_state({"current_node": node})
    
    def set_progress(self, progress: float) -> None:
        """设置进度"""
        self.update_state({"progress": progress})
    
    def set_error(self, error: Optional[str]) -> None:
        """设置错误信息"""
        self.update_state({"error": error})
    
    def append_novel_content(self, content: str) -> None:
        """追加小说内容"""
        with self._lock:
            current = self._state.get("novel_content", "")
            self._state["novel_content"] = current + content
            self._notify_subscribers("novel_content", self._state["novel_content"])
