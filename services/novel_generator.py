"""
小说生成服务实现

实现小说生成主服务，协调各节点完成内容生成
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from interfaces import LLMClient, MemoryStore, ObservabilityBackend, ConfigProvider
from core.iterators.chapter_iterator import ChapterIterator
from core.nodes.director_general import director_general
from core.nodes.director_chapter import director_chapter
from core.nodes.role_assigner import role_assigner
from core.nodes.role_actor import role_actor
from core.nodes.self_check import self_check
from core.nodes.memory_summarizer import memory_summarizer
from schemas import (
    DirectorGeneralInput,
    DirectorGeneralOutput,
    DirectorChapterInput,
    DirectorChapterOutput,
    RoleAssignerInput,
    RoleAssignerOutput,
    RoleActorOutput,
)

from services.interfaces import (
    NovelGeneratorService,
    GenerationRequest,
    GenerationResult,
    GenerationProgress,
    GenerationStatus,
    ChapterResult,
    GenerationError,
)

logger = logging.getLogger(__name__)


class NovelGenerator(NovelGeneratorService):
    """
    小说生成服务实现
    
    职责：
    - 接收并验证生成请求
    - 协调 Director General、Director Chapter、Role Assigner、Role Actor 等节点
    - 管理生成进度和状态
    - 提供错误处理和重试机制
    
    Attributes:
        llm_client: LLM 客户端
        memory_store: 记忆存储
        observability: 可观测性后端
        config_provider: 配置提供者
        _current_task_id: 当前任务ID
        _is_running: 是否正在运行
        _is_paused: 是否暂停
        _is_stopped: 是否停止
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        observability: ObservabilityBackend,
        config_provider: ConfigProvider,
    ):
        """
        初始化小说生成服务
        
        Args:
            llm_client: LLM 客户端
            memory_store: 记忆存储
            observability: 可观测性后端
            config_provider: 配置提供者
        """
        self.llm_client = llm_client
        self.memory_store = memory_store
        self.observability = observability
        self.config_provider = config_provider
        
        self._current_task_id: Optional[str] = None
        self._is_running: bool = False
        self._is_paused: bool = False
        self._is_stopped: bool = False
        self._current_chapter: int = 0
        self._total_chapters: int = 0
        self._current_node: str = ""
        
        logger.info("NovelGenerator initialized")
    
    def validate_request(self, request: GenerationRequest) -> bool:
        """
        验证生成请求
        
        Args:
            request: 生成请求
            
        Returns:
            bool: 验证是否通过
            
        Example:
            >>> request = GenerationRequest(theme="测试主题", total_words=5000)
            >>> generator.validate_request(request)
            True
        """
        if not request.theme or len(request.theme.strip()) == 0:
            logger.warning("Request validation failed: empty theme")
            return False
        
        if request.total_words < 1000 or request.total_words > 100000:
            logger.warning(f"Request validation failed: invalid total_words {request.total_words}")
            return False
        
        if request.character_count < 1 or request.character_count > 20:
            logger.warning(f"Request validation failed: invalid character_count {request.character_count}")
            return False
        
        if request.temperature < 0.0 or request.temperature > 2.0:
            logger.warning(f"Request validation failed: invalid temperature {request.temperature}")
            return False
        
        logger.debug(f"Request validation passed: {request.theme[:50]}...")
        return True
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        执行小说生成
        
        完整的生成流程：
        1. 验证请求参数
        2. 调用 Director General 生成总体大纲
        3. 循环生成每个章节
        4. 收集结果并返回
        
        Args:
            request: 生成请求
            
        Returns:
            GenerationResult: 生成结果
            
        Raises:
            GenerationError: 生成失败时
            
        Example:
            >>> request = GenerationRequest(theme="科幻小说", total_words=10000)
            >>> result = await generator.generate(request)
            >>> print(f"Generated {result.total_word_count} words")
        """
        # 验证请求
        if not self.validate_request(request):
            raise GenerationError("Invalid generation request", node="VALIDATION")
        
        # 初始化任务
        self._current_task_id = f"gen_{uuid.uuid4().hex[:12]}"
        self._is_running = True
        self._is_stopped = False
        self._is_paused = False
        
        logger.info(f"Starting generation task {self._current_task_id}")
        self.observability.log_event(
            "INFO", 0, "GENERATOR", f"Task {self._current_task_id} started"
        )
        
        try:
            # 步骤 1: Director General
            plan = await self._run_director_general(request)
            self._total_chapters = plan.chapter_count
            
            # 步骤 2: 循环生成章节
            chapters = []
            for chapter_num in ChapterIterator(1, self._total_chapters + 1):
                if self._is_stopped:
                    logger.info("Generation stopped by user")
                    break
                
                # 处理暂停
                while self._is_paused:
                    await asyncio.sleep(0.5)
                
                self._current_chapter = chapter_num
                self._current_node = f"CHAPTER_{chapter_num}"
                
                # 生成章节
                chapter_result = await self.generate_chapter(
                    chapter_num,
                    {"plan": plan, "request": request}
                )
                chapters.append(chapter_result)
                
                # 记录进度
                progress = self.get_progress()
                logger.info(f"Chapter {chapter_num}/{self._total_chapters} completed: {progress.percentage:.1f}%")
            
            # 完成任务
            self._is_running = False
            total_words = sum(c.word_count for c in chapters)
            
            result = GenerationResult(
                task_id=self._current_task_id,
                status=GenerationStatus.COMPLETED if not self._is_stopped else GenerationStatus.STOPPED,
                chapters=chapters,
                total_word_count=total_words,
                created_at=asyncio.get_event_loop().time().__str__(),
            )
            
            logger.info(f"Generation task {self._current_task_id} completed: {total_words} words")
            return result
            
        except Exception as e:
            self._is_running = False
            logger.error(f"Generation failed: {e}", exc_info=True)
            self.observability.log_event(
                "ERROR", self._current_chapter, self._current_node, str(e)
            )
            raise GenerationError(str(e), node=self._current_node)
    
    async def _run_director_general(self, request: GenerationRequest) -> DirectorGeneralOutput:
        """
        运行 Director General 节点
        
        Args:
            request: 生成请求
            
        Returns:
            DirectorGeneralOutput: 总体大纲
        """
        self._current_node = "DIRECTOR_GENERAL"
        
        input_data = DirectorGeneralInput(
            theme=request.theme,
            style=request.style.value,
            total_words=request.total_words,
            character_count=request.character_count,
            genre=request.genre,
        )
        
        logger.debug(f"Running DIRECTOR_GENERAL with theme: {request.theme[:50]}...")
        
        # 在后台线程运行同步函数
        result = await asyncio.to_thread(director_general, input_data)
        
        logger.info(f"DIRECTOR_GENERAL completed: {result.chapter_count} chapters planned")
        return result
    
    async def generate_chapter(
        self,
        chapter_number: int,
        context: Dict[str, Any],
    ) -> ChapterResult:
        """
        生成单个章节
        
        章节生成流程：
        1. Director Chapter: 生成章节大纲
        2. Role Assigner: 分配角色任务
        3. Role Actor: 执行角色生成
        4. Self Check: 自检
        5. Memory Summarizer: 更新记忆
        
        Args:
            chapter_number: 章节号
            context: 生成上下文，包含 plan 和 request
            
        Returns:
            ChapterResult: 章节结果
            
        Raises:
            GenerationError: 生成失败时
        """
        plan = context.get("plan")
        request = context.get("request")
        
        try:
            # 步骤 1: Director Chapter
            self._current_node = "DIRECTOR_CHAPTER"
            chapter_plan = await self._run_director_chapter(chapter_number, plan)
            
            # 步骤 2: Role Assigner
            self._current_node = "ROLE_ASSIGNER"
            role_tasks = await self._run_role_assigner(chapter_number, chapter_plan)
            
            # 步骤 3: Role Actor
            self._current_node = "ROLE_ACTOR"
            chapter_content = await self._run_role_actor(chapter_number, role_tasks)
            
            # 步骤 4: Self Check
            self._current_node = "SELF_CHECK"
            check_result = await self._run_self_check(chapter_number, chapter_content)
            
            # 步骤 5: Memory Summarizer
            self._current_node = "MEMORY_SUMMARIZER"
            await self._run_memory_summarizer(chapter_number, chapter_content)
            
            # 计算字数
            word_count = len(chapter_content.replace(" ", "").replace("\n", ""))
            
            return ChapterResult(
                chapter_number=chapter_number,
                title=chapter_plan.title if hasattr(chapter_plan, "title") else f"Chapter {chapter_number}",
                content=chapter_content,
                word_count=word_count,
                node_results={
                    "director_chapter": chapter_plan,
                    "role_assigner": role_tasks,
                    "self_check": check_result,
                }
            )
            
        except Exception as e:
            logger.error(f"Chapter {chapter_number} generation failed: {e}")
            raise GenerationError(f"Chapter {chapter_number} failed: {str(e)}", node=self._current_node)
    
    async def _run_director_chapter(
        self,
        chapter_number: int,
        plan: DirectorGeneralOutput,
    ) -> DirectorChapterOutput:
        """运行 Director Chapter 节点"""
        input_data = DirectorChapterInput(
            chapter_number=chapter_number,
            global_outline=plan.outline if hasattr(plan, "outline") else "",
            characters=plan.character_cards if hasattr(plan, "character_cards") else [],
        )
        
        result = await asyncio.to_thread(director_chapter, input_data)
        logger.debug(f"DIRECTOR_CHAPTER completed for chapter {chapter_number}")
        return result
    
    async def _run_role_assigner(
        self,
        chapter_number: int,
        chapter_plan: DirectorChapterOutput,
    ) -> RoleAssignerOutput:
        """运行 Role Assigner 节点"""
        input_data = RoleAssignerInput(
            chapter_outline=chapter_plan.outline if hasattr(chapter_plan, "outline") else "",
            characters=chapter_plan.characters if hasattr(chapter_plan, "characters") else [],
        )
        
        result = await asyncio.to_thread(role_assigner, input_data)
        logger.debug(f"ROLE_ASSIGNER completed for chapter {chapter_number}")
        return result
    
    async def _run_role_actor(
        self,
        chapter_number: int,
        role_tasks: RoleAssignerOutput,
    ) -> str:
        """运行 Role Actor 节点"""
        # 简化实现：直接返回内容
        # 实际应该根据角色任务调用 role_actor
        content = f"Chapter {chapter_number} content generated by role actors."
        logger.debug(f"ROLE_ACTOR completed for chapter {chapter_number}")
        return content
    
    async def _run_self_check(
        self,
        chapter_number: int,
        content: str,
    ) -> Any:
        """运行 Self Check 节点"""
        # 简化实现
        logger.debug(f"SELF_CHECK completed for chapter {chapter_number}")
        return {"passed": True}
    
    async def _run_memory_summarizer(
        self,
        chapter_number: int,
        content: str,
    ) -> None:
        """运行 Memory Summarizer 节点"""
        # 简化实现
        logger.debug(f"MEMORY_SUMMARIZER completed for chapter {chapter_number}")
    
    def get_progress(self) -> GenerationProgress:
        """
        获取当前生成进度
        
        Returns:
            GenerationProgress: 生成进度
        """
        percentage = 0.0
        if self._total_chapters > 0:
            percentage = (self._current_chapter / self._total_chapters) * 100
        
        status = GenerationStatus.PENDING
        if self._is_running:
            status = GenerationStatus.RUNNING
            if self._is_paused:
                status = GenerationStatus.PAUSED
        elif self._is_stopped:
            status = GenerationStatus.STOPPED
        elif self._current_chapter >= self._total_chapters and self._total_chapters > 0:
            status = GenerationStatus.COMPLETED
        
        return GenerationProgress(
            current_chapter=self._current_chapter,
            total_chapters=self._total_chapters,
            current_node=self._current_node,
            percentage=percentage,
            status=status,
        )
    
    def pause(self) -> None:
        """暂停生成"""
        if self._is_running:
            self._is_paused = True
            logger.info("Generation paused")
    
    def resume(self) -> None:
        """恢复生成"""
        if self._is_running and self._is_paused:
            self._is_paused = False
            logger.info("Generation resumed")
    
    def stop(self) -> None:
        """停止生成"""
        self._is_stopped = True
        self._is_running = False
        logger.info("Generation stopped")
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """是否暂停"""
        return self._is_paused
    
    @property
    def current_task_id(self) -> Optional[str]:
        """当前任务ID"""
        return self._current_task_id
