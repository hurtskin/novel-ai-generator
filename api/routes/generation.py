"""
生成路由模块

提供文本/内容生成相关的 RESTful API 端点
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field

from api.dependencies import (
    get_llm_client,
    get_config_provider,
    get_generation_state,
    require_generation_not_running,
    GenerationState,
)
from interfaces import LLMClient, ConfigProvider

logger = logging.getLogger(__name__)

router = APIRouter()


class StyleEnum(str, Enum):
    """文体枚举"""
    NOVEL = "novel"
    SCRIPT = "script"
    GAME_STORY = "game_story"
    DIALOGUE = "dialogue"
    ARTICLE = "article"


class GenreEnum(str, Enum):
    """类型枚举"""
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    HORROR = "horror"
    HISTORICAL = "historical"
    MODERN = "modern"


class GenerationRequest(BaseModel):
    """
    生成请求模型
    
    Attributes:
        theme: 主题/故事大纲
        style: 文体类型
        total_words: 总字数目标
        character_count: 角色数量
        genre: 故事类型
        temperature: 生成温度
        max_tokens: 最大 token 数
    """
    theme: str = Field(..., min_length=1, max_length=5000, description="主题/故事大纲")
    style: StyleEnum = Field(default=StyleEnum.NOVEL, description="文体类型")
    total_words: int = Field(default=10000, ge=1000, le=100000, description="总字数目标")
    character_count: int = Field(default=3, ge=1, le=20, description="角色数量")
    genre: GenreEnum = Field(default=GenreEnum.MODERN, description="故事类型")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=4096, ge=100, le=8192, description="最大 token 数")


class GenerationResponse(BaseModel):
    """
    生成响应模型
    
    Attributes:
        task_id: 任务 ID
        status: 任务状态
        message: 状态消息
        created_at: 创建时间
    """
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    created_at: str = Field(..., description="创建时间")


class GenerationStatus(BaseModel):
    """
    生成状态模型
    
    Attributes:
        is_running: 是否运行中
        is_paused: 是否暂停
        is_stopped: 是否已停止
        current_chapter: 当前章节
        current_node: 当前节点
        total_chapters: 总章节数
        progress: 进度百分比
        error: 错误信息
    """
    is_running: bool = Field(..., description="是否运行中")
    is_paused: bool = Field(..., description="是否暂停")
    is_stopped: bool = Field(..., description="是否已停止")
    current_chapter: int = Field(..., description="当前章节")
    current_node: str = Field(..., description="当前节点")
    total_chapters: int = Field(..., description="总章节数")
    progress: float = Field(..., description="进度百分比")
    error: Optional[str] = Field(None, description="错误信息")


class ChapterResult(BaseModel):
    """章节结果模型"""
    chapter_number: int = Field(..., description="章节编号")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    word_count: int = Field(..., description="字数")


class GenerationResult(BaseModel):
    """
    生成结果模型
    
    Attributes:
        task_id: 任务 ID
        status: 任务状态
        chapters: 章节列表
        total_word_count: 总字数
        completed_at: 完成时间
    """
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态")
    chapters: List[ChapterResult] = Field(default=[], description="章节列表")
    total_word_count: int = Field(default=0, description="总字数")
    completed_at: Optional[str] = Field(None, description="完成时间")


# 任务存储（简化实现，生产环境使用 Redis）
_tasks: Dict[str, Dict[str, Any]] = {}


def _generate_task_id() -> str:
    """生成任务 ID"""
    import uuid
    return f"gen_{uuid.uuid4().hex[:12]}"


@router.post(
    "/start",
    response_model=GenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="启动生成任务",
    description="启动一个新的内容生成任务",
)
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    state: GenerationState = Depends(get_generation_state),
    _: None = Depends(require_generation_not_running),
    llm_client: LLMClient = Depends(get_llm_client),
    config_provider: ConfigProvider = Depends(get_config_provider),
) -> GenerationResponse:
    """
    启动内容生成任务
    
    - 验证请求参数
    - 创建异步生成任务
    - 返回任务 ID 用于后续查询
    """
    task_id = _generate_task_id()
    
    # 初始化任务状态
    _tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "request": request.model_dump(),
        "created_at": datetime.now().isoformat(),
        "result": None,
    }
    
    # 更新全局状态
    state.is_running = True
    state.is_paused = False
    state.is_stopped = False
    state.current_chapter = 0
    state.current_node = "INIT"
    state.total_chapters = 0
    state.progress = 0.0
    state.error = None
    
    # 启动后台任务
    background_tasks.add_task(
        _run_generation_task,
        task_id,
        request,
        state,
        llm_client,
        config_provider,
    )
    
    logger.info(f"Generation task {task_id} started")
    
    return GenerationResponse(
        task_id=task_id,
        status="pending",
        message="Generation task started",
        created_at=_tasks[task_id]["created_at"],
    )


@router.get(
    "/status",
    response_model=GenerationStatus,
    summary="获取生成状态",
    description="获取当前生成任务的运行状态",
)
async def get_status(
    state: GenerationState = Depends(get_generation_state),
) -> GenerationStatus:
    """获取当前生成任务的状态"""
    return GenerationStatus(**state.to_dict())


@router.post(
    "/pause",
    response_model=Dict[str, str],
    summary="暂停生成",
    description="暂停当前运行的生成任务",
)
async def pause_generation(
    state: GenerationState = Depends(get_generation_state),
) -> Dict[str, str]:
    """暂停生成任务"""
    if not state.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generation task is running",
        )
    
    state.is_paused = True
    logger.info("Generation task paused")
    return {"status": "paused", "message": "Generation task paused"}


@router.post(
    "/resume",
    response_model=Dict[str, str],
    summary="恢复生成",
    description="恢复暂停的生成任务",
)
async def resume_generation(
    state: GenerationState = Depends(get_generation_state),
) -> Dict[str, str]:
    """恢复生成任务"""
    if not state.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generation task is running",
        )
    
    if not state.is_paused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generation task is not paused",
        )
    
    state.is_paused = False
    logger.info("Generation task resumed")
    return {"status": "resumed", "message": "Generation task resumed"}


@router.post(
    "/stop",
    response_model=Dict[str, str],
    summary="停止生成",
    description="停止当前运行的生成任务",
)
async def stop_generation(
    state: GenerationState = Depends(get_generation_state),
) -> Dict[str, str]:
    """停止生成任务"""
    if not state.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generation task is running",
        )
    
    state.is_stopped = True
    state.is_running = False
    logger.info("Generation task stopped")
    return {"status": "stopped", "message": "Generation task stopped"}


@router.get(
    "/tasks/{task_id}",
    response_model=GenerationResult,
    summary="获取任务结果",
    description="获取指定生成任务的结果",
)
async def get_task_result(task_id: str) -> GenerationResult:
    """获取任务结果"""
    if task_id not in _tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    task = _tasks[task_id]
    
    return GenerationResult(
        task_id=task_id,
        status=task["status"],
        chapters=task.get("result", {}).get("chapters", []),
        total_word_count=task.get("result", {}).get("total_word_count", 0),
        completed_at=task.get("completed_at"),
    )


@router.get(
    "/tasks",
    response_model=List[GenerationResponse],
    summary="获取任务列表",
    description="获取所有生成任务的列表",
)
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
) -> List[GenerationResponse]:
    """获取任务列表"""
    tasks = list(_tasks.values())
    return [
        GenerationResponse(
            task_id=t["id"],
            status=t["status"],
            message=f"Task is {t['status']}",
            created_at=t["created_at"],
        )
        for t in tasks[skip:skip + limit]
    ]


async def _run_generation_task(
    task_id: str,
    request: GenerationRequest,
    state: GenerationState,
    llm_client: LLMClient,
    config_provider: ConfigProvider,
) -> None:
    """
    运行生成任务（后台任务）
    
    Args:
        task_id: 任务 ID
        request: 生成请求
        state: 生成状态
        llm_client: LLM 客户端
        config_provider: 配置提供者
    """
    try:
        _tasks[task_id]["status"] = "running"
        
        # 模拟生成过程（实际实现应该调用核心生成逻辑）
        # TODO: 集成实际的生成流程
        
        logger.info(f"Task {task_id} running with theme: {request.theme[:50]}...")
        
        # 模拟章节生成
        total_chapters = 3  # 实际应该从 director_general 获取
        state.total_chapters = total_chapters
        
        chapters = []
        for i in range(1, total_chapters + 1):
            if state.is_stopped:
                break
            
            while state.is_paused:
                await asyncio.sleep(0.5)
            
            state.current_chapter = i
            state.current_node = f"CHAPTER_{i}"
            state.progress = (i / total_chapters) * 100
            
            # 模拟生成延迟
            await asyncio.sleep(1)
            
            chapters.append(ChapterResult(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}...",
                word_count=1000,
            ))
        
        # 完成任务
        _tasks[task_id]["status"] = "completed" if not state.is_stopped else "stopped"
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()
        _tasks[task_id]["result"] = {
            "chapters": [c.model_dump() for c in chapters],
            "total_word_count": sum(c.word_count for c in chapters),
        }
        
        state.is_running = False
        logger.info(f"Task {task_id} completed")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)
        state.error = str(e)
        state.is_running = False
