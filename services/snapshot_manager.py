"""
快照管理服务实现

支持小说生成过程中关键节点的快照创建、保存、加载和回滚
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from interfaces import StorageBackend, ObservabilityBackend
from services.interfaces import (
    SnapshotManagerService,
    SnapshotInfo,
    StateSnapshot,
    SnapshotError,
)
from services.state_manager import StateManager

logger = logging.getLogger(__name__)


class SnapshotManager(SnapshotManagerService):
    """
    快照管理服务实现
    
    职责：
    - 创建和管理快照
    - 支持快照回滚
    - 实现版本控制
    - 管理快照元数据
    
    Attributes:
        storage: 存储后端
        observability: 可观测性后端
        state_manager: 状态管理服务
        _snapshots_dir: 快照存储目录
        _version: 快照版本
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        observability: ObservabilityBackend,
        state_manager: StateManager,
        snapshots_dir: str = "storage/snapshots",
    ):
        """
        初始化快照管理服务
        
        Args:
            storage: 存储后端
            observability: 可观测性后端
            state_manager: 状态管理服务
            snapshots_dir: 快照存储目录
        """
        self.storage = storage
        self.observability = observability
        self.state_manager = state_manager
        self._snapshots_dir = Path(snapshots_dir)
        self._version = "1.0"
        
        # 确保目录存在
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SnapshotManager initialized with dir: {snapshots_dir}")
    
    async def create_snapshot(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> SnapshotInfo:
        """
        创建快照
        
        保存当前状态、记忆和观测数据
        
        Args:
            name: 快照名称
            description: 快照描述
            
        Returns:
            SnapshotInfo: 快照信息
            
        Raises:
            SnapshotError: 创建失败时
            
        Example:
            >>> snapshot = await manager.create_snapshot("Chapter 5 complete")
            >>> print(f"Created snapshot: {snapshot.id}")
        """
        try:
            # 生成快照ID
            snapshot_id = f"snap_{uuid.uuid4().hex[:16]}"
            created_at = datetime.now().isoformat()
            
            # 获取当前状态
            state = self.state_manager.get_state()
            
            # 创建快照数据
            snapshot_data = StateSnapshot(
                generation_state=state,
                memory_state={},  # 实际应该从 memory_store 获取
                observability_state={},  # 实际应该从 observability 获取
                timestamp=created_at,
                version=self._version,
            )
            
            # 创建元数据
            meta = {
                "id": snapshot_id,
                "name": name,
                "description": description,
                "created_at": created_at,
                "chapter": state.get("current_chapter", 0),
                "node": state.get("current_node", ""),
                "version": self._version,
            }
            
            # 保存到存储
            full_data = {
                "meta": meta,
                "data": snapshot_data.__dict__,
            }
            
            self.storage.save(f"snapshot:{snapshot_id}", full_data)
            
            # 同时保存到文件
            snapshot_file = self._snapshots_dir / f"{snapshot_id}.json"
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            
            # 记录日志
            self.observability.log_event(
                "INFO",
                state.get("current_chapter", 0),
                state.get("current_node", ""),
                f"Snapshot created: {name}",
            )
            
            logger.info(f"Snapshot created: {snapshot_id} - {name}")
            
            return SnapshotInfo(
                id=snapshot_id,
                name=name,
                description=description,
                created_at=created_at,
                chapter=meta["chapter"],
                node=meta["node"],
                version=self._version,
                metadata=meta,
            )
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            raise SnapshotError(f"Failed to create snapshot: {str(e)}")
    
    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        恢复快照
        
        从指定快照恢复状态
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 恢复是否成功
            
        Raises:
            SnapshotError: 恢复失败时
            
        Example:
            >>> success = await manager.restore_snapshot("snap_abc123")
            >>> if success:
            ...     print("State restored successfully")
        """
        try:
            # 从存储加载
            data = self.storage.load(f"snapshot:{snapshot_id}")
            
            if not data:
                # 尝试从文件加载
                snapshot_file = self._snapshots_dir / f"{snapshot_id}.json"
                if snapshot_file.exists():
                    with open(snapshot_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    raise SnapshotError(f"Snapshot not found: {snapshot_id}", snapshot_id)
            
            # 恢复状态
            snapshot_data = data.get("data", {})
            generation_state = snapshot_data.get("generation_state", {})
            
            # 更新状态管理器
            for key, value in generation_state.items():
                self.state_manager.update_state({key: value})
            
            # 记录日志
            meta = data.get("meta", {})
            self.observability.log_event(
                "INFO",
                meta.get("chapter", 0),
                meta.get("node", ""),
                f"Snapshot restored: {meta.get('name', snapshot_id)}",
            )
            
            logger.info(f"Snapshot restored: {snapshot_id}")
            return True
            
        except SnapshotError:
            raise
        except Exception as e:
            logger.error(f"Failed to restore snapshot {snapshot_id}: {e}", exc_info=True)
            raise SnapshotError(f"Failed to restore snapshot: {str(e)}", snapshot_id)
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        删除快照
        
        删除指定快照及其数据
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 删除是否成功
            
        Example:
            >>> success = await manager.delete_snapshot("snap_abc123")
        """
        try:
            # 从存储删除
            try:
                self.storage.delete(f"snapshot:{snapshot_id}")
            except:
                pass
            
            # 从文件删除
            snapshot_file = self._snapshots_dir / f"{snapshot_id}.json"
            if snapshot_file.exists():
                snapshot_file.unlink()
            
            logger.info(f"Snapshot deleted: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            raise SnapshotError(f"Failed to delete snapshot: {str(e)}", snapshot_id)
    
    def list_snapshots(self) -> List[SnapshotInfo]:
        """
        获取快照列表
        
        返回所有可用快照的信息列表
        
        Returns:
            List[SnapshotInfo]: 快照列表，按创建时间倒序排列
            
        Example:
            >>> snapshots = manager.list_snapshots()
            >>> for snap in snapshots:
            ...     print(f"{snap.name} - Chapter {snap.chapter}")
        """
        snapshots = []
        
        # 从文件系统读取
        if self._snapshots_dir.exists():
            for snapshot_file in sorted(
                self._snapshots_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                try:
                    with open(snapshot_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    meta = data.get("meta", {})
                    snapshots.append(
                        SnapshotInfo(
                            id=meta.get("id", snapshot_file.stem),
                            name=meta.get("name", "Unnamed"),
                            description=meta.get("description"),
                            created_at=meta.get("created_at", ""),
                            chapter=meta.get("chapter", 0),
                            node=meta.get("node", ""),
                            version=meta.get("version", "1.0"),
                            metadata=meta,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to read snapshot {snapshot_file}: {e}")
        
        return snapshots
    
    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotInfo]:
        """
        获取快照信息
        
        获取指定快照的详细信息
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[SnapshotInfo]: 快照信息，不存在则返回None
        """
        # 尝试从文件读取
        snapshot_file = self._snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            return None
        
        try:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            meta = data.get("meta", {})
            return SnapshotInfo(
                id=meta.get("id", snapshot_id),
                name=meta.get("name", "Unnamed"),
                description=meta.get("description"),
                created_at=meta.get("created_at", ""),
                chapter=meta.get("chapter", 0),
                node=meta.get("node", ""),
                version=meta.get("version", "1.0"),
                metadata=meta,
            )
        except Exception as e:
            logger.error(f"Failed to read snapshot {snapshot_id}: {e}")
            return None
    
    async def auto_snapshot(self, trigger: str) -> Optional[SnapshotInfo]:
        """
        自动创建快照
        
        根据触发条件自动创建快照
        
        Args:
            trigger: 触发条件，如 "chapter_complete", "node_complete", "error"
            
        Returns:
            Optional[SnapshotInfo]: 快照信息，如果不满足条件则返回None
            
        Example:
            >>> snapshot = await manager.auto_snapshot("chapter_complete")
            >>> if snapshot:
            ...     print(f"Auto-snapshot created: {snapshot.name}")
        """
        # 定义自动快照触发条件
        auto_snapshot_triggers = {
            "chapter_complete": True,
            "node_complete": False,  # 可选
            "error": True,
            "intervention": True,
        }
        
        if not auto_snapshot_triggers.get(trigger, False):
            return None
        
        # 生成快照名称
        state = self.state_manager.get_state()
        chapter = state.get("current_chapter", 0)
        node = state.get("current_node", "")
        
        name = f"Auto-{trigger}-Ch{chapter}"
        if node:
            name += f"-{node}"
        
        description = f"Automatically created on {trigger} at {datetime.now().isoformat()}"
        
        return await self.create_snapshot(name, description)
    
    def get_snapshot_path(self, snapshot_id: str) -> Path:
        """
        获取快照文件路径
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Path: 快照文件路径
        """
        return self._snapshots_dir / f"{snapshot_id}.json"
    
    def cleanup_old_snapshots(self, keep_count: int = 50) -> int:
        """
        清理旧快照
        
        只保留最近的指定数量的快照
        
        Args:
            keep_count: 保留的快照数量
            
        Returns:
            int: 删除的快照数量
        """
        snapshots = self.list_snapshots()
        
        if len(snapshots) <= keep_count:
            return 0
        
        deleted = 0
        for snapshot in snapshots[keep_count:]:
            try:
                snapshot_file = self._snapshots_dir / f"{snapshot.id}.json"
                if snapshot_file.exists():
                    snapshot_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete old snapshot {snapshot.id}: {e}")
        
        logger.info(f"Cleaned up {deleted} old snapshots")
        return deleted
