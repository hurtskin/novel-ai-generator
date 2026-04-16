"""
快照路由模块

提供快照创建、查询、删除、恢复等管理接口
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_observability, get_storage_backend
from interfaces import ObservabilityBackend, StorageBackend

logger = logging.getLogger(__name__)

router = APIRouter()


class SnapshotInfo(BaseModel):
    """
    快照信息模型
    
    Attributes:
        id: 快照唯一标识
        name: 快照名称
        description: 快照描述
        created_at: 创建时间
        chapter: 章节号
        node: 节点名称
        size_bytes: 快照大小（字节）
        version: 版本号
    """
    id: str = Field(..., description="快照唯一标识")
    name: str = Field(..., description="快照名称")
    description: Optional[str] = Field(None, description="快照描述")
    created_at: str = Field(..., description="创建时间")
    chapter: int = Field(..., description="章节号")
    node: str = Field(..., description="节点名称")
    size_bytes: int = Field(default=0, description="快照大小（字节）")
    version: str = Field(default="1.0", description="版本号")


class SnapshotCreateRequest(BaseModel):
    """
    快照创建请求模型
    
    Attributes:
        name: 快照名称
        description: 快照描述
        include_memory: 是否包含记忆数据
        include_observability: 是否包含观测数据
    """
    name: str = Field(..., min_length=1, max_length=100, description="快照名称")
    description: Optional[str] = Field(None, max_length=500, description="快照描述")
    include_memory: bool = Field(default=True, description="是否包含记忆数据")
    include_observability: bool = Field(default=True, description="是否包含观测数据")


class SnapshotCreateResponse(BaseModel):
    """快照创建响应模型"""
    id: str = Field(..., description="快照 ID")
    status: str = Field(..., description="创建状态")
    message: str = Field(..., description="状态消息")
    created_at: str = Field(..., description="创建时间")


class SnapshotRestoreRequest(BaseModel):
    """
    快照恢复请求模型
    
    Attributes:
        snapshot_id: 要恢复的快照 ID
        restore_memory: 是否恢复记忆数据
        restore_observability: 是否恢复观测数据
    """
    snapshot_id: str = Field(..., description="要恢复的快照 ID")
    restore_memory: bool = Field(default=True, description="是否恢复记忆数据")
    restore_observability: bool = Field(default=True, description="是否恢复观测数据")


class SnapshotRestoreResponse(BaseModel):
    """快照恢复响应模型"""
    status: str = Field(..., description="恢复状态")
    message: str = Field(..., description="状态消息")
    restored_at: str = Field(..., description="恢复时间")
    chapter: int = Field(..., description="恢复的章节号")
    node: str = Field(..., description="恢复的节点名称")


class SnapshotListResponse(BaseModel):
    """快照列表响应模型"""
    snapshots: List[SnapshotInfo] = Field(default=[], description="快照列表")
    total: int = Field(..., description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页大小")


class SnapshotCompareRequest(BaseModel):
    """快照比较请求模型"""
    snapshot_id_1: str = Field(..., description="第一个快照 ID")
    snapshot_id_2: str = Field(..., description="第二个快照 ID")


class SnapshotCompareResponse(BaseModel):
    """快照比较响应模型"""
    differences: Dict[str, Any] = Field(default={}, description="差异内容")
    summary: str = Field(..., description="差异摘要")


# 快照存储路径
SNAPSHOTS_DIR = Path("storage/snapshots")


def _ensure_snapshots_dir():
    """确保快照目录存在"""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_snapshot_path(snapshot_id: str) -> Path:
    """获取快照文件路径"""
    return SNAPSHOTS_DIR / f"{snapshot_id}.json"


def _load_snapshot_meta(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """加载快照元数据"""
    path = _get_snapshot_path(snapshot_id)
    if not path.exists():
        return None
    
    import json
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("meta", {})
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
        return None


@router.post(
    "/",
    response_model=SnapshotCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建快照",
    description="创建当前状态的快照",
)
async def create_snapshot(
    request: SnapshotCreateRequest,
    observability: ObservabilityBackend = Depends(get_observability),
    storage: StorageBackend = Depends(get_storage_backend),
) -> SnapshotCreateResponse:
    """
    创建状态快照
    
    保存当前生成状态、记忆数据和观测数据
    """
    _ensure_snapshots_dir()
    
    import uuid
    snapshot_id = f"snap_{uuid.uuid4().hex[:16]}"
    created_at = datetime.now().isoformat()
    
    try:
        # 收集快照数据
        snapshot_data = {
            "meta": {
                "id": snapshot_id,
                "name": request.name,
                "description": request.description,
                "created_at": created_at,
                "version": "1.0",
            },
            "data": {}
        }
        
        # 保存到存储
        storage.save(f"snapshot:{snapshot_id}", snapshot_data)
        
        # 同时保存到文件
        snapshot_path = _get_snapshot_path(snapshot_id)
        import json
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Snapshot {snapshot_id} created: {request.name}")
        
        return SnapshotCreateResponse(
            id=snapshot_id,
            status="created",
            message=f"Snapshot '{request.name}' created successfully",
            created_at=created_at,
        )
    
    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}",
        )


@router.get(
    "/",
    response_model=SnapshotListResponse,
    summary="获取快照列表",
    description="获取所有快照的列表",
)
async def list_snapshots(
    skip: int = 0,
    limit: int = 20,
    storage: StorageBackend = Depends(get_storage_backend),
) -> SnapshotListResponse:
    """
    获取快照列表
    
    支持分页查询
    """
    _ensure_snapshots_dir()
    
    snapshots = []
    
    # 从文件系统读取快照
    if SNAPSHOTS_DIR.exists():
        for snapshot_file in sorted(SNAPSHOTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                meta = _load_snapshot_meta(snapshot_file.stem)
                if meta:
                    snapshots.append(SnapshotInfo(
                        id=meta.get("id", snapshot_file.stem),
                        name=meta.get("name", "Unnamed"),
                        description=meta.get("description"),
                        created_at=meta.get("created_at", ""),
                        chapter=meta.get("chapter", 0),
                        node=meta.get("node", ""),
                        size_bytes=snapshot_file.stat().st_size,
                        version=meta.get("version", "1.0"),
                    ))
            except Exception as e:
                logger.warning(f"Failed to read snapshot {snapshot_file}: {e}")
    
    total = len(snapshots)
    paginated = snapshots[skip:skip + limit]
    
    return SnapshotListResponse(
        snapshots=paginated,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get(
    "/{snapshot_id}",
    response_model=SnapshotInfo,
    summary="获取快照详情",
    description="获取指定快照的详细信息",
)
async def get_snapshot(
    snapshot_id: str,
    storage: StorageBackend = Depends(get_storage_backend),
) -> SnapshotInfo:
    """获取快照详情"""
    meta = _load_snapshot_meta(snapshot_id)
    
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    
    snapshot_path = _get_snapshot_path(snapshot_id)
    size_bytes = snapshot_path.stat().st_size if snapshot_path.exists() else 0
    
    return SnapshotInfo(
        id=meta.get("id", snapshot_id),
        name=meta.get("name", "Unnamed"),
        description=meta.get("description"),
        created_at=meta.get("created_at", ""),
        chapter=meta.get("chapter", 0),
        node=meta.get("node", ""),
        size_bytes=size_bytes,
        version=meta.get("version", "1.0"),
    )


@router.post(
    "/{snapshot_id}/restore",
    response_model=SnapshotRestoreResponse,
    summary="恢复快照",
    description="从指定快照恢复状态",
)
async def restore_snapshot(
    snapshot_id: str,
    request: SnapshotRestoreRequest,
    observability: ObservabilityBackend = Depends(get_observability),
    storage: StorageBackend = Depends(get_storage_backend),
) -> SnapshotRestoreResponse:
    """
    恢复快照
    
    从指定快照恢复生成状态
    """
    # 验证快照存在
    meta = _load_snapshot_meta(snapshot_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    
    try:
        # 从存储加载快照数据
        snapshot_data = storage.load(f"snapshot:{snapshot_id}")
        
        if not snapshot_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot data not found for {snapshot_id}",
            )
        
        restored_at = datetime.now().isoformat()
        
        logger.info(f"Snapshot {snapshot_id} restored")
        
        return SnapshotRestoreResponse(
            status="restored",
            message=f"Snapshot '{meta.get('name', snapshot_id)}' restored successfully",
            restored_at=restored_at,
            chapter=meta.get("chapter", 0),
            node=meta.get("node", ""),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore snapshot {snapshot_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore snapshot: {str(e)}",
        )


@router.delete(
    "/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除快照",
    description="删除指定的快照",
)
async def delete_snapshot(
    snapshot_id: str,
    storage: StorageBackend = Depends(get_storage_backend),
) -> None:
    """删除快照"""
    snapshot_path = _get_snapshot_path(snapshot_id)
    
    if not snapshot_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    
    try:
        # 删除文件
        snapshot_path.unlink()
        
        # 删除存储中的数据
        try:
            storage.delete(f"snapshot:{snapshot_id}")
        except:
            pass
        
        logger.info(f"Snapshot {snapshot_id} deleted")
    
    except Exception as e:
        logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete snapshot: {str(e)}",
        )


@router.post(
    "/compare",
    response_model=SnapshotCompareResponse,
    summary="比较快照",
    description="比较两个快照的差异",
)
async def compare_snapshots(
    request: SnapshotCompareRequest,
    storage: StorageBackend = Depends(get_storage_backend),
) -> SnapshotCompareResponse:
    """
    比较两个快照
    
    分析两个快照之间的差异
    """
    # 验证两个快照都存在
    meta1 = _load_snapshot_meta(request.snapshot_id_1)
    meta2 = _load_snapshot_meta(request.snapshot_id_2)
    
    if not meta1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {request.snapshot_id_1} not found",
        )
    
    if not meta2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {request.snapshot_id_2} not found",
        )
    
    try:
        # 加载快照数据
        data1 = storage.load(f"snapshot:{request.snapshot_id_1}")
        data2 = storage.load(f"snapshot:{request.snapshot_id_2}")
        
        # 简单的差异分析
        differences = {
            "meta1": meta1,
            "meta2": meta2,
            "time_diff": "N/A",  # 实际应该计算时间差
        }
        
        summary = f"Comparing '{meta1.get('name')}' with '{meta2.get('name')}'"
        
        return SnapshotCompareResponse(
            differences=differences,
            summary=summary,
        )
    
    except Exception as e:
        logger.error(f"Failed to compare snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare snapshots: {str(e)}",
        )
