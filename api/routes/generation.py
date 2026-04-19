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
    get_node_retry_service,
    get_node_regenerate_service,
    get_performance_metrics_service,
    get_config_manager_service,
    get_debug_log_service,
    get_state_manager_service,
    require_generation_not_running,
    GenerationState,
)
from interfaces import LLMClient, ConfigProvider
from services.interfaces import (
    NodeRetryService, NodeRetryError,
    NodeRegenerateService, NodeRegenerateError,
    PerformanceMetricsService, PerformanceMetricsError,
    ConfigManagerService, ConfigManagerError,
    DebugLogService, DebugLogError,
    NovelGeneratorService,
    StateManagerService,
)

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


class NodeRetryResponse(BaseModel):
    """
    节点重试响应模型
    
    Attributes:
        status: 操作状态
        message: 状态消息
        chapter_id: 章节ID
        node_id: 节点ID
        retry_count: 当前重试次数
        can_retry: 是否还可以继续重试
    """
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="状态消息")
    chapter_id: int = Field(..., description="章节ID")
    node_id: int = Field(..., description="节点ID")
    retry_count: int = Field(..., description="当前重试次数")
    can_retry: bool = Field(..., description="是否还可以继续重试")


@router.post(
    "/retry_node",
    response_model=NodeRetryResponse,
    status_code=status.HTTP_200_OK,
    summary="重试当前节点",
    description="重试当前失败的节点生成，支持自动重试和人工干预两种模式",
)
async def retry_node(
    state: GenerationState = Depends(get_generation_state),
    retry_service: NodeRetryService = Depends(get_node_retry_service),
    state_manager: StateManagerService = Depends(get_state_manager_service),
) -> NodeRetryResponse:
    """
    重试当前节点
    
    统一的节点重试接口，同时支持：
    1. 自动重试：记录重试次数，供生成器查询
    2. 人工干预：触发实际的重试逻辑
    
    从 NodeRetryService 获取待重试节点信息，确保重试正确的节点。
    调用 StateManagerService.retry_current_node() 触发实际重试流程。
    
    Note:
        - 需要当前有正在运行的生成任务
        - 会自动使用触发人工干预时的节点信息
    """
    # 验证是否有正在运行的任务
    if not state.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generation task is running",
        )
    
    # 从 NodeRetryService 获取待重试节点信息
    pending_retry = retry_service.get_pending_retry()
    
    if pending_retry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending retry node found",
        )
    
    chapter_id = pending_retry.chapter_id
    node_id = pending_retry.node_id
    
    try:
        # 执行重试（记录重试次数）
        result = await retry_service.retry_node(chapter_id, node_id)
        
        # 触发实际重试逻辑（关键！这会设置 retry_current=True 并恢复生成流程）
        state_manager.retry_current_node()
        
        # 清除待重试状态
        retry_service.clear_pending_retry()
        
        # 检查是否还可以继续重试
        can_retry = retry_service.can_retry(chapter_id, node_id, max_retries=3)
        
        logger.info(
            f"Node retry: chapter={chapter_id}, node={node_id}, "
            f"retry_count={result.retry_count}"
        )
        
        return NodeRetryResponse(
            status="success" if result.success else "failed",
            message=result.message,
            chapter_id=chapter_id,
            node_id=node_id,
            retry_count=result.retry_count,
            can_retry=can_retry,
        )
        
    except NodeRetryError as e:
        logger.error(f"Node retry error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in retry_node: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry node: {str(e)}",
        )


class RegenerateRequest(BaseModel):
    """
    节点再生请求模型
    
    Attributes:
        chapter_id: 章节ID
        node_id: 节点ID
    """
    chapter_id: int = Field(..., description="章节ID", ge=1)
    node_id: str = Field(..., description="节点ID", min_length=1)


class RegenerateResponse(BaseModel):
    """
    节点再生响应模型
    
    Attributes:
        status: 操作状态
        chapter_id: 章节ID
        node_id: 节点ID
    """
    status: str = Field(..., description="操作状态")
    chapter_id: int = Field(..., description="章节ID")
    node_id: str = Field(..., description="节点ID")


@router.post(
    "/regenerate",
    response_model=RegenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="重新生成节点",
    description="指定章节和节点重新生成",
)
async def regenerate_node(
    request: RegenerateRequest,
    regenerate_service: NodeRegenerateService = Depends(get_node_regenerate_service),
) -> RegenerateResponse:
    """
    重新生成节点
    
    用于指定章节和节点进行内容重新生成。
    
    Args:
        request: 再生请求，包含 chapter_id 和 node_id
        regenerate_service: 节点再生服务
        
    Returns:
        RegenerateResponse: 再生响应
        
    Raises:
        HTTPException: 400 - 参数无效或无法再生
        HTTPException: 500 - 服务器内部错误
    """
    chapter_id = request.chapter_id
    node_id = request.node_id
    
    try:
        # 检查是否可以再生
        if not regenerate_service.can_regenerate(chapter_id, node_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot regenerate node {node_id} in chapter {chapter_id}",
            )
        
        # 执行再生
        result = await regenerate_service.regenerate_node(chapter_id, node_id)
        
        logger.info(
            f"Node regeneration: chapter={chapter_id}, node={node_id}, "
            f"status={result.status}"
        )
        
        return RegenerateResponse(
            status=result.status,
            chapter_id=chapter_id,
            node_id=node_id,
        )
        
    except NodeRegenerateError as e:
        logger.error(f"Node regenerate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in regenerate_node: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate node: {str(e)}",
        )


class PerformanceResponse(BaseModel):
    """
    性能指标响应模型
    
    Attributes:
        per_node: 节点级性能指标列表
        per_chapter: 章节级性能指标列表
        summary: 总体性能指标汇总
    """
    per_node: List[Dict[str, Any]] = Field(default_factory=list, description="节点级性能指标")
    per_chapter: List[Dict[str, Any]] = Field(default_factory=list, description="章节级性能指标")
    summary: Dict[str, Any] = Field(default_factory=dict, description="总体性能指标汇总")


@router.get(
    "/performance",
    response_model=PerformanceResponse,
    status_code=status.HTTP_200_OK,
    summary="获取性能指标",
    description="获取性能指标汇总，包括节点级、章节级和总体指标",
)
async def get_performance(
    metrics_service: PerformanceMetricsService = Depends(get_performance_metrics_service),
) -> PerformanceResponse:
    """
    获取性能指标汇总
    
    返回三级性能指标：
    - per_node: 每个 LLM 节点的详细指标
    - per_chapter: 每个章节的汇总指标
    - summary: 总体汇总指标
    
    Args:
        metrics_service: 性能指标服务
        
    Returns:
        PerformanceResponse: 性能指标响应
        
    Raises:
        HTTPException: 500 - 服务器内部错误
    """
    try:
        # 获取性能指标
        metrics = metrics_service.get_performance_metrics()
        
        # 转换汇总数据为字典
        summary_dict = {
            "total_chapters": metrics.summary.total_chapters,
            "total_duration_min": metrics.summary.total_duration_min,
            "total_tokens": metrics.summary.total_tokens,
            "total_cost_usd": metrics.summary.total_cost_usd,
            "avg_chapter_time_min": metrics.summary.avg_chapter_time_min,
        }
        
        logger.info(
            f"Performance metrics retrieved: "
            f"nodes={len(metrics.per_node)}, chapters={len(metrics.per_chapter)}"
        )
        
        return PerformanceResponse(
            per_node=metrics.per_node,
            per_chapter=metrics.per_chapter,
            summary=summary_dict,
        )
        
    except PerformanceMetricsError as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}",
        )


async def _run_generation_task(
    task_id: str,
    request: GenerationRequest,
    state: GenerationState,
) -> None:
    """
    运行生成任务（后台任务）
    
    调用 NovelGenerator 服务执行实际的小说生成流程，包括：
    - Director General: 生成总体大纲
    - Director Chapter: 生成章节计划
    - Role Assigner/Actor: 角色分配和演绎
    - Self Check: 内容自检
    - Text Polisher: 文本润色
    - Memory Summarizer: 记忆总结
    
    Args:
        task_id: 任务 ID
        request: 生成请求
        state: 生成状态
    """
    from services.interfaces import GenerationRequest as NovelGenerationRequest, NovelStyle
    
    try:
        _tasks[task_id]["status"] = "running"
        
        logger.info(f"Task {task_id} running with theme: {request.theme[:50]}...")
        
        # 延迟启动，给前端时间建立 WebSocket 连接
        # 在 mock_mode 下生成速度很快，需要确保 WebSocket 连接建立后再开始
        import asyncio
        await asyncio.sleep(0.5)
        logger.info(f"Task {task_id} starting after WebSocket delay")
        
        # 使用模块级别的容器实例，确保与 WebSocket 连接管理器使用同一个 EventBus
        from api.dependencies import _container_instance
        if _container_instance is None:
            logger.error("Container instance not set")
            raise RuntimeError("Container instance not set")
        container = _container_instance
        logger.info(f"Using shared container instance")
        
        # 获取小说生成服务
        novel_generator = container.resolve(NovelGeneratorService)
        
        # 构建生成请求
        # 注意：request.style 和 request.genre 可能是字符串或枚举值
        style_value = request.style.value if hasattr(request.style, 'value') else request.style
        genre_value = request.genre.value if hasattr(request.genre, 'value') else request.genre
        
        gen_request = NovelGenerationRequest(
            theme=request.theme,
            style=NovelStyle(style_value),
            total_words=request.total_words,
            character_count=request.character_count,
            genre=genre_value,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # 更新状态
        state.is_running = True
        state.is_stopped = False
        state.is_paused = False
        
        # 执行生成
        result = await novel_generator.generate(gen_request)
        
        # 转换结果为 API 格式
        chapters = [
            ChapterResult(
                chapter_number=c.chapter_number,
                title=c.title,
                content=c.content,
                word_count=c.word_count,
            )
            for c in result.chapters
        ]
        
        # 完成任务
        _tasks[task_id]["status"] = "completed" if not state.is_stopped else "stopped"
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()
        _tasks[task_id]["result"] = {
            "chapters": [c.model_dump() for c in chapters],
            "total_word_count": result.total_word_count,
        }
        
        state.is_running = False
        state.progress = 100.0
        logger.info(f"Task {task_id} completed with {result.total_word_count} words")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)
        state.error = str(e)
        state.is_running = False


class ConfigSaveRequest(BaseModel):
    """
    配置保存请求模型
    
    Attributes:
        api: API 配置（可选）
        generation: 生成配置（可选）
        memory: 记忆配置（可选）
        ui: UI 配置（可选）
        performance: 性能配置（可选）
    """
    api: Optional[Dict[str, Any]] = Field(None, description="API 配置")
    generation: Optional[Dict[str, Any]] = Field(None, description="生成配置")
    memory: Optional[Dict[str, Any]] = Field(None, description="记忆配置")
    ui: Optional[Dict[str, Any]] = Field(None, description="UI 配置")
    performance: Optional[Dict[str, Any]] = Field(None, description="性能配置")


class ConfigSaveResponse(BaseModel):
    """
    配置保存响应模型
    
    Attributes:
        status: 操作状态
        message: 状态消息
        updated_keys: 更新的键列表
    """
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="状态消息")
    updated_keys: List[str] = Field(default_factory=list, description="更新的键列表")

class ConfigGetResponse(BaseModel):
    """
    配置获取响应模型
    
    Attributes:
        api: API 配置
        generation: 生成配置
        memory: 记忆配置
        ui: UI 配置
        performance: 性能配置
    """
    api: Dict[str, Any] = Field(default_factory=dict, description="API 配置")
    generation: Dict[str, Any] = Field(default_factory=dict, description="生成配置")
    memory: Dict[str, Any] = Field(default_factory=dict, description="记忆配置")
    ui: Dict[str, Any] = Field(default_factory=dict, description="UI 配置")
    performance: Dict[str, Any] = Field(default_factory=dict, description="性能配置")

@router.get(
    "/config",
    response_model=ConfigGetResponse,
    status_code=status.HTTP_200_OK,
    summary="获取配置",
    description="获取当前配置信息（动态从 config.yaml 读取）",
)
async def get_config(
    config_provider: ConfigProvider = Depends(get_config_provider),
) -> ConfigGetResponse:
    """
    获取配置信息
    
    动态从 config.yaml 读取最新配置，确保返回的是当前生效的配置。
    
    Args:
        config_provider: 配置提供者
        
    Returns:
        ConfigGetResponse: 配置信息响应
        
    Raises:
        HTTPException: 500 - 服务器内部错误
    """
    try:
        # 获取所有配置
        config = config_provider.get_all()
        
        logger.debug("Config retrieved successfully")
        
        return ConfigGetResponse(
            api=config.get("api", {}),
            generation=config.get("generation", {}),
            memory=config.get("memory", {}),
            ui=config.get("ui", {}),
            performance=config.get("performance", {}),
        )
        
    except Exception as e:
        logger.error(f"Failed to get config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}",
        )
        
@router.post(
    "/config",
    response_model=ConfigSaveResponse,
    status_code=status.HTTP_200_OK,
    summary="保存配置",
    description="保存配置到 config.yaml 并重新加载（动态生效，无需重启）",
)
async def save_config(
    request: ConfigSaveRequest,
    config_manager: ConfigManagerService = Depends(get_config_manager_service),
) -> ConfigSaveResponse:
    """
    保存配置
    
    支持部分配置更新，只更新提供的字段。
    配置保存后会自动重新加载，无需重启服务。
    
    Args:
        request: 配置保存请求
        config_manager: 配置管理服务
        
    Returns:
        ConfigSaveResponse: 配置保存响应
        
    Raises:
        HTTPException: 400 - 配置无效
        HTTPException: 500 - 服务器内部错误
    """
    try:
        # 构建配置更新字典
        config_updates = {}
        
        if request.api is not None:
            config_updates["api"] = request.api
        if request.generation is not None:
            config_updates["generation"] = request.generation
        if request.memory is not None:
            config_updates["memory"] = request.memory
        if request.ui is not None:
            config_updates["ui"] = request.ui
        if request.performance is not None:
            config_updates["performance"] = request.performance
        
        # 检查是否有配置更新
        if not config_updates:
            return ConfigSaveResponse(
                status="saved",
                message="No configuration changes provided",
                updated_keys=[],
            )
        
        # 保存配置
        result = await config_manager.save_config(config_updates)
        
        logger.info(
            f"Config saved successfully: updated {len(result.updated_keys)} keys"
        )
        
        return ConfigSaveResponse(
            status=result.status,
            message=result.message,
            updated_keys=result.updated_keys,
        )
        
    except ConfigManagerError as e:
        logger.error(f"Config save error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in save_config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}",
        )


class DebugLogAction(str, Enum):
    """调试日志操作类型枚举"""
    GET = "get"
    CLEAR = "clear"
    WRITE = "write"
    SET_MODE = "set_mode"


class DebugLogRequest(BaseModel):
    """
    调试日志请求模型
    
    Attributes:
        action: 操作类型（get/clear/write/set_mode）
        message: 日志消息（write 操作时必需）
        level: 日志级别（write 操作时可选，默认为 INFO）
        enabled: 是否启用调试模式（set_mode 操作时必需）
    """
    action: DebugLogAction = Field(..., description="操作类型")
    message: Optional[str] = Field(None, description="日志消息（write 操作时必需）")
    level: Optional[str] = Field("INFO", description="日志级别（write 操作时可选）")
    enabled: Optional[bool] = Field(None, description="是否启用调试模式（set_mode 操作时必需）")


class DebugLogResponse(BaseModel):
    """
    调试日志响应模型
    
    Attributes:
        status: 操作状态
        message: 状态消息
        content: 日志内容（get 操作时返回）
        exists: 日志文件是否存在
        debug_mode: 当前调试模式状态（set_mode 操作时返回）
    """
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="状态消息")
    content: Optional[str] = Field(None, description="日志内容")
    exists: bool = Field(False, description="日志文件是否存在")
    debug_mode: Optional[bool] = Field(None, description="调试模式状态")


@router.post(
    "/debuglog",
    response_model=DebugLogResponse,
    status_code=status.HTTP_200_OK,
    summary="调试日志操作",
    description="执行调试日志相关操作：获取内容、清除、写入、设置调试模式",
)
async def debug_log(
    request: DebugLogRequest,
    debug_log_service: DebugLogService = Depends(get_debug_log_service),
) -> DebugLogResponse:
    """
    调试日志操作
    
    支持以下操作：
    - get: 获取调试日志内容
    - clear: 清空调试日志
    - write: 写入调试日志（需要提供 message 和可选的 level）
    - set_mode: 设置调试模式（需要提供 enabled）
    
    Args:
        request: 调试日志请求
        debug_log_service: 调试日志服务
        
    Returns:
        DebugLogResponse: 调试日志响应
        
    Raises:
        HTTPException: 400 - 请求参数无效
        HTTPException: 500 - 服务器内部错误
    """
    try:
        if request.action == DebugLogAction.GET:
            # 获取调试日志内容
            result = debug_log_service.get_debug_log()
            return DebugLogResponse(
                status=result.status,
                message=result.message,
                content=result.content,
                exists=result.exists,
            )
            
        elif request.action == DebugLogAction.CLEAR:
            # 清空调试日志
            result = debug_log_service.clear_debug_log()
            return DebugLogResponse(
                status=result.status,
                message=result.message,
                exists=result.exists,
            )
            
        elif request.action == DebugLogAction.WRITE:
            # 写入调试日志
            if not request.message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message is required for write action",
                )
            result = debug_log_service.write_debug_log(
                message=request.message,
                level=request.level or "INFO",
            )
            return DebugLogResponse(
                status=result.status,
                message=result.message,
                exists=result.exists,
            )
            
        elif request.action == DebugLogAction.SET_MODE:
            # 设置调试模式
            if request.enabled is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Enabled is required for set_mode action",
                )
            result = debug_log_service.set_debug_mode(enabled=request.enabled)
            debug_mode = debug_log_service.get_debug_mode()
            return DebugLogResponse(
                status=result.status,
                message=result.message,
                exists=result.exists,
                debug_mode=debug_mode,
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {request.action}",
            )
            
    except HTTPException:
        # 重新抛出 HTTPException（如 400 错误）
        raise
    except DebugLogError as e:
        logger.error(f"Debug log error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error in debug_log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform debug log operation: {str(e)}",
        )


class SelectVersionRequest(BaseModel):
    """
    选择版本请求模型
    
    Attributes:
        version_index: 选择的版本索引
    """
    version_index: int = Field(..., description="选择的版本索引")


class SelectVersionResponse(BaseModel):
    """
    选择版本响应模型
    
    Attributes:
        status: 操作状态
        message: 状态消息
        version_index: 选择的版本索引
    """
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="状态消息")
    version_index: int = Field(..., description="选择的版本索引")


@router.post(
    "/select_version",
    response_model=SelectVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="选择历史版本",
    description="人工干预时选择某个历史版本继续生成",
)
async def select_version(
    request: SelectVersionRequest,
    state_manager: StateManagerService = Depends(get_state_manager_service),
) -> SelectVersionResponse:
    """
    选择历史版本
    
    当生成流程触发人工干预时，前端调用此接口选择某个历史版本。
    选择后，生成流程会继续执行。
    
    Args:
        request: 选择版本请求
        state_manager: 状态管理服务
        
    Returns:
        SelectVersionResponse: 选择响应
        
    Raises:
        HTTPException: 500 - 服务器内部错误
    """
    try:
        # 选择版本
        state_manager.select_version(request.version_index)
        
        logger.info(f"Version {request.version_index} selected")
        
        return SelectVersionResponse(
            status="success",
            message="Version selected successfully",
            version_index=request.version_index,
        )
        
    except Exception as e:
        logger.error(f"Failed to select version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select version: {str(e)}",
        )
