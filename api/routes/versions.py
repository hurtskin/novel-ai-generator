"""
版本管理路由模块

提供版本选择、查询、管理等 RESTful API 端点
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import (
    get_version_selector_service,
    get_generation_state,
    get_observability,
    GenerationState,
)
from services.interfaces import (
    VersionSelectorService,
    VersionSelectionError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class VersionSelectRequest(BaseModel):
    """
    版本选择请求模型
    
    Attributes:
        version_index: 版本索引
        chapter_id: 章节ID（可选，默认使用当前章节）
        node_id: 节点ID（可选，默认使用当前节点）
    """
    version_index: int = Field(..., ge=0, description="版本索引")
    chapter_id: Optional[int] = Field(None, ge=0, description="章节ID，默认当前章节")
    node_id: Optional[str] = Field(None, description="节点ID，默认当前节点")


class VersionSelectResponse(BaseModel):
    """
    版本选择响应模型
    
    Attributes:
        status: 操作状态
        message: 状态消息
        selected_version: 选中的版本索引
        previous_version: 之前的版本索引
        chapter_id: 章节ID
        node_id: 节点ID
    """
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="状态消息")
    selected_version: int = Field(..., description="选中的版本索引")
    previous_version: Optional[int] = Field(None, description="之前的版本索引")
    chapter_id: int = Field(..., description="章节ID")
    node_id: str = Field(..., description="节点ID")


class VersionInfoResponse(BaseModel):
    """版本信息响应模型"""
    index: int = Field(..., description="版本索引")
    created_at: str = Field(..., description="创建时间")
    metrics: Dict[str, Any] = Field(default={}, description="性能指标")
    is_selected: bool = Field(default=False, description="是否被选中")
    content_preview: Optional[str] = Field(None, description="内容预览")


class VersionListResponse(BaseModel):
    """版本列表响应模型"""
    chapter_id: int = Field(..., description="章节ID")
    node_id: str = Field(..., description="节点ID")
    versions: List[VersionInfoResponse] = Field(default=[], description="版本列表")
    total_count: int = Field(..., description="版本总数")
    selected_index: Optional[int] = Field(None, description="当前选中索引")


class VersionContentResponse(BaseModel):
    """版本内容响应模型"""
    chapter_id: int = Field(..., description="章节ID")
    node_id: str = Field(..., description="节点ID")
    version_index: int = Field(..., description="版本索引")
    content: str = Field(..., description="版本内容")
    is_selected: bool = Field(default=False, description="是否被选中")


@router.post(
    "/select_version",
    response_model=VersionSelectResponse,
    status_code=status.HTTP_200_OK,
    summary="选择版本",
    description="选择指定章节和节点的特定版本",
)
async def select_version(
    request: VersionSelectRequest,
    version_service: VersionSelectorService = Depends(get_version_selector_service),
    state: GenerationState = Depends(get_generation_state),
) -> VersionSelectResponse:
    """
    选择版本
    
    用于在多个生成版本中选择特定版本（例如在自检后选择接受或拒绝某个版本）。
    如果未提供 chapter_id 和 node_id，则使用当前生成状态中的值。
    
    - **version_index**: 要选择的版本索引（从0开始）
    - **chapter_id**: 可选，章节ID
    - **node_id**: 可选，节点ID
    """
    # 确定章节和节点
    chapter_id = request.chapter_id if request.chapter_id is not None else state.current_chapter
    node_id = request.node_id if request.node_id is not None else state.current_node
    
    # 验证章节和节点
    if chapter_id is None or chapter_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing chapter_id",
        )
    
    if not node_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing node_id",
        )
    
    try:
        # 执行版本选择
        result = version_service.select_version(
            chapter_id=chapter_id,
            node_id=node_id,
            version_index=request.version_index,
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )
        
        logger.info(
            f"Version selected: chapter={chapter_id}, node={node_id}, "
            f"version={result.selected_version}"
        )
        
        return VersionSelectResponse(
            status="success",
            message=result.message,
            selected_version=result.selected_version,
            previous_version=result.previous_version,
            chapter_id=chapter_id,
            node_id=node_id,
        )
        
    except VersionSelectionError as e:
        logger.error(f"Version selection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in select_version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select version: {str(e)}",
        )


@router.get(
    "/versions/{chapter_id}/{node_id}",
    response_model=VersionListResponse,
    summary="获取版本列表",
    description="获取指定章节和节点的所有版本",
)
async def list_versions(
    chapter_id: int,
    node_id: str,
    include_content: bool = False,
    version_service: VersionSelectorService = Depends(get_version_selector_service),
) -> VersionListResponse:
    """
    获取版本列表
    
    返回指定章节和节点的所有可用版本信息。
    
    - **chapter_id**: 章节ID
    - **node_id**: 节点ID
    - **include_content**: 是否包含内容预览（默认否）
    """
    try:
        versions = version_service.get_versions(chapter_id, node_id)
        selected = version_service.get_selected_version(chapter_id, node_id)
        
        version_responses = []
        for v in versions:
            preview = None
            if include_content and v.content:
                # 限制预览长度
                preview = v.content[:200] + "..." if len(v.content) > 200 else v.content
            
            version_responses.append(VersionInfoResponse(
                index=v.index,
                created_at=v.created_at,
                metrics=v.metrics,
                is_selected=v.is_selected,
                content_preview=preview,
            ))
        
        return VersionListResponse(
            chapter_id=chapter_id,
            node_id=node_id,
            versions=version_responses,
            total_count=len(versions),
            selected_index=selected.index if selected else None,
        )
        
    except Exception as e:
        logger.error(f"Error listing versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}",
        )


@router.get(
    "/versions/{chapter_id}/{node_id}/{version_index}",
    response_model=VersionContentResponse,
    summary="获取版本内容",
    description="获取指定版本的内容",
)
async def get_version_content(
    chapter_id: int,
    node_id: str,
    version_index: int,
    version_service: VersionSelectorService = Depends(get_version_selector_service),
) -> VersionContentResponse:
    """
    获取版本内容
    
    返回指定版本的具体内容。
    
    - **chapter_id**: 章节ID
    - **node_id**: 节点ID
    - **version_index**: 版本索引
    """
    try:
        # 获取版本列表以检查索引是否有效
        versions = version_service.get_versions(chapter_id, node_id)
        
        if not versions or version_index >= len(versions):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_index} not found for chapter {chapter_id}, node {node_id}",
            )
        
        version_info = versions[version_index]
        
        return VersionContentResponse(
            chapter_id=chapter_id,
            node_id=node_id,
            version_index=version_index,
            content=version_info.content,
            is_selected=version_info.is_selected,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version content: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version content: {str(e)}",
        )


@router.get(
    "/versions/current",
    response_model=VersionListResponse,
    summary="获取当前版本列表",
    description="获取当前章节和节点的版本列表",
)
async def list_current_versions(
    include_content: bool = False,
    version_service: VersionSelectorService = Depends(get_version_selector_service),
    state: GenerationState = Depends(get_generation_state),
) -> VersionListResponse:
    """
    获取当前版本列表
    
    返回当前章节和节点的所有可用版本信息。
    """
    if state.current_chapter < 0 or not state.current_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active generation context",
        )
    
    return await list_versions(
        chapter_id=state.current_chapter,
        node_id=state.current_node,
        include_content=include_content,
        version_service=version_service,
    )


@router.delete(
    "/versions/{chapter_id}/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清除版本",
    description="清除指定章节和节点的所有版本",
)
async def clear_versions(
    chapter_id: int,
    node_id: str,
    version_service: VersionSelectorService = Depends(get_version_selector_service),
) -> None:
    """
    清除版本
    
    删除指定章节和节点的所有版本历史。
    
    - **chapter_id**: 章节ID
    - **node_id**: 节点ID
    """
    try:
        success = version_service.clear_versions(chapter_id, node_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for chapter {chapter_id}, node {node_id}",
            )
        
        logger.info(f"Versions cleared: chapter={chapter_id}, node={node_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear versions: {str(e)}",
        )
