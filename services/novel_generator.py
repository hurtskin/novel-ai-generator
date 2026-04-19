"""
小说生成服务实现

实现小说生成主服务，协调各节点完成内容生成
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from interfaces import LLMClient, MemoryStore, ObservabilityBackend, ConfigProvider
from interfaces.memory import MemoryUpdate
from core.iterators.chapter_iterator import ChapterIterator
from core.nodes.director_general import director_general
from core.nodes.director_chapter import director_chapter
from core.nodes.role_assigner import role_assigner
from core.nodes.role_actor import role_actor
from core.nodes.self_check import self_check
from core.nodes.memory_summarizer import memory_summarizer
from core.nodes.text_polisher import text_polisher

from schemas import (
    DirectorGeneralInput,
    DirectorGeneralOutput,
    DirectorChapterInput,
    DirectorChapterOutput,
    RoleAssignerInput,
    RoleAssignerOutput,
    RoleActorOutput,
    CurrentNodeInfo,
    CharacterProfileData,
    RawMemory,
)

from services.interfaces import (
    NovelGeneratorService,
    GenerationRequest,
    GenerationResult,
    GenerationProgress,
    GenerationStatus,
    ChapterResult,
    GenerationError,
    EventBus,
    Event,
    FileOutputService,
    RAGRetrievalService,
    StateManagerService,
    NodeRetryService,
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
        event_bus: EventBus,
        file_output_service: FileOutputService,
        rag_service: RAGRetrievalService,
        state_manager: StateManagerService,
        node_retry_service: Optional[NodeRetryService] = None,
    ):
        """
        初始化小说生成服务
        
        Args:
            llm_client: LLM 客户端
            memory_store: 记忆存储
            observability: 可观测性后端
            config_provider: 配置提供者
            event_bus: 事件总线
            file_output_service: 文件输出服务
            rag_service: RAG 检索服务
            state_manager: 状态管理服务
            node_retry_service: 节点重试服务（可选）
        """
        self.llm_client = llm_client
        self.memory_store = memory_store
        self.observability = observability
        self.config_provider = config_provider
        self.file_output = file_output_service
        self.rag = rag_service
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.node_retry_service = node_retry_service
        
        self._current_task_id: Optional[str] = None
        self._is_running: bool = False
        self._is_paused: bool = False
        self._is_stopped: bool = False
        self._current_chapter: int = 0
        self._total_chapters: int = 0
        self._current_node: str = ""
        
        logger.info("NovelGenerator initialized")
        
        generation_config = self.config_provider.get_generation_config()
        self._mock_mode = generation_config.mock_mode 
        self.max_retries = getattr(generation_config, 'max_retries', 3)
        self.window_size = getattr(generation_config, 'window_size', 5)
    
    def _publish_event(self, event_type: str, data: dict) -> int:
        """
        发布事件到事件总线
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            int: 通知的订阅者数量
        """
        return self.event_bus.publish(Event(type=event_type, data=data))
    
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

        # 清空 RAG 存储（确保新任务开始时数据干净）
        if self.rag:
            try:
                await self.rag.clear()
                logger.info("RAG store cleared for new generation")
            except Exception as e:
                logger.warning(f"Failed to clear RAG store: {e}")
        
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
        result = await asyncio.to_thread(director_general, input_data, llm_client=self.llm_client, mock_mode=self._mock_mode)
        
        # 如果结果是字典，转换为 DirectorGeneralOutput 对象
        if isinstance(result, dict):
            result = DirectorGeneralOutput(**result)
        
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
        from core.iterators.node_sequence import NodeSequence
        from core.context.chapter_context import ChapterContext
        plan = context.get("plan")
        request = context.get("request")
        
        try:
            # 使用 ChapterContext 管理章节上下文
            with ChapterContext(
                chapter_id=chapter_number,
                config_path="config.yaml",
                memory_path="global_memory.json",
                base_dir=f"./temp/{self._current_task_id}"
            ) as ctx:
                # 步骤 1: Director Chapter
                self._current_node = "DIRECTOR_CHAPTER"
                chapter_plan = await self._run_director_chapter(chapter_number, plan)
                
                # 步骤 2-4: 使用 NodeSequence 迭代执行节点序列
                self._current_node = "NODE_SEQUENCE"
                chapter_content = await self._execute_node_sequence(
                    chapter_number=chapter_number,
                    chapter_plan=chapter_plan,
                    context=context,
                    ctx=ctx,
                )
                # 步骤 5: Text Polisher
                self._current_node = "TEXT_POLISHER"
                polished_content = await self._run_text_polisher(chapter_content)
                            # 保存润色后的章节
                if self.file_output:
                    await self.file_output.save_polished_chapter(
                        chapter_number=chapter_number,
                        content=polished_content,
                        original_file_path=f"./output/{self._current_task_id}.txt",
                    )

                # 步骤 6: Memory Summarizer
                self._current_node = "MEMORY_SUMMARIZER"
                await self._run_memory_summarizer(chapter_number, polished_content, context)
                
                # 计算字数
                word_count = len(chapter_content.replace(" ", "").replace("\n", ""))
                
                return ChapterResult(
                    chapter_number=chapter_number,
                    title=chapter_plan.title if hasattr(chapter_plan, "title") else f"Chapter {chapter_number}",
                    content=polished_content,
                    word_count=word_count,
                    node_results={
                        "director_chapter": chapter_plan,
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
            chapter_id=chapter_number,
            director_general_output=plan,
            genre=plan.genre_specific.genre if hasattr(plan, "genre_specific") else "novel",
        )
        
        result = await asyncio.to_thread(director_chapter, input_data, llm_client=self.llm_client, mock_mode=self._mock_mode)
        logger.debug(f"DIRECTOR_CHAPTER completed for chapter {chapter_number}")
        return result
    
    async def _run_role_assigner(
        self,
        chapter_number: int,
        node: Dict[str, Any],
        context: Dict[str, Any],
    ) -> RoleAssignerOutput:
        """
        运行 Role Assigner 节点

        根据节点定义和上下文，调用 role_assigner 节点生成分配的角色任务。
        遵循面向接口原则，通过依赖注入使用 llm_client。

        Args:
            chapter_number: 章节号
            node: 节点定义字典，包含 node_id, type, description, target_character 等
            context: 生成上下文，包含 plan, request 等信息

        Returns:
            RoleAssignerOutput: 角色分配器输出
        """
        plan = context.get("plan")
        request = context.get("request")

        # 从 plan 中获取角色卡片
        character_cards = plan.character_cards if hasattr(plan, "character_cards") else []
        character_names = plan.character_names if hasattr(plan, "character_names") else []

        # 获取目标角色
        target_character = node.get("target_character", "")
        if not target_character and character_cards:
            target_character = character_cards[0].name if character_cards else"主角"

        # 查找目标角色的详细档案
        character_profile = None
        for card in character_cards:
            if isinstance(card, dict) and card.get("name") == target_character:
                character_profile = CharacterProfileData(
                    name=card.get("name", target_character),
                    role=card.get("role", ""),
                    background=card.get("background", ""),
                    personality=card.get("personality", ""),
                    goals=card.get("goals", ""),
                    relationships=card.get("relationships", {}),
                )
                break

        # 如果找不到角色档案，使用默认值
        if not character_profile:
            character_profile = CharacterProfileData(
                name=target_character,
                role="主角",
                background="",
                personality="",
                goals="",
                relationships={},
            )

        # 构建当前节点信息
        current_node = CurrentNodeInfo(
            node_id=node.get("node_id", 0),
            type=node.get("type", "dialogue"),
            description=node.get("description", ""),
            target_character=target_character,
        )

        # 构建输入数据
        input_data = RoleAssignerInput(
            current_node=current_node,
            character_profile=character_profile,
            genre=request.genre if request else "novel",
            current_situation=node.get("description", ""),
            goals=node.get("goals", "完成当前场景内容"),
            constraints=node.get("constraints", []),
            user_theme=request.theme if request else "",
            user_style=request.style.value if request else "",
            user_total_words=request.total_words if request else 0,
            user_character_count=request.character_count if request else 0,
            character_names=character_names,
            character_cards=[card.model_dump() if hasattr(card, "model_dump") else card for card in character_cards],
            feedback=node.get("feedback", ""),
            generated_summaries=[],  # 可以从 memory_store 获取
        )

        # 调用 role_assigner 节点（在后台线程运行同步函数）
        result = await asyncio.to_thread(
            role_assigner,
            input_data=input_data,
            llm_client=self.llm_client,
            mock_mode=self._mock_mode,
        )

        logger.debug(f"ROLE_ASSIGNER completed for chapter {chapter_number}, node {current_node.node_id}")
        return result
    
    async def _run_role_actor(
        self,
        chapter_number: int,
        node_id: str,
        node_type: str,
        role_output: RoleAssignerOutput,
        rag_context: List[str],
        context: Dict[str, Any],
    ) -> str:
        """
        运行 Role Actor 节点

        根据角色分配器的输出，调用 role_actor 节点生成具体的角色扮演内容。
        遵循面向接口原则，通过依赖注入使用 llm_client。

        Args:
            chapter_number: 章节号
            node_id: 节点ID
            node_type: 节点类型 (dialogue/narrator/action/environment/psychology/conflict)
            role_output: 角色分配器输出 (RoleAssignerOutput)
            rag_context: RAG检索上下文列表
            context: 生成上下文

        Returns:
            str: 生成的内容文本
        """
        request = context.get("request")

        # 构建流式回调函数（通过 EventBus 发布 token 事件）
        stream_callback = None
        if self.event_bus:
            def _stream_callback(token: str) -> None:
                self._publish_event("token", {
                    "chapter": chapter_number,
                    "node_id": node_id,
                    "token": token,
                })
            stream_callback = _stream_callback

        # 构建记忆更新回调
        def _update_memory_callback(memory_update: Dict[str, Any]) -> None:
            if self.memory_store:
                try:
                    self.memory_store.update_memory(memory_update)
                except Exception as e:
                    logger.warning(f"Memory update failed: {e}")

        # 准备 role_output 的 generation_prompt，添加 RAG 上下文
        if rag_context and role_output.generation_prompt:
            # 将 RAG 上下文合并到 generation_prompt 的 rag_context 字段
            rag_entries = [
                {"source": f"rag_{i}", "score": 0.9, "content": ctx}
                for i, ctx in enumerate(rag_context)
            ]
            # 使用 model_copy 创建副本并更新
            updated_prompt = role_output.generation_prompt.model_copy(update={"rag_context": rag_entries})
            role_output = role_output.model_copy(update={"generation_prompt": updated_prompt})

        # 调用 role_actor 节点（在后台线程运行同步函数）
        result = await asyncio.to_thread(
            role_actor,
            role_assigner_output=role_output,
            chapter_id=chapter_number,
            node_id=node_id,
            node_type=node_type,
            feedback=role_output.feedback if hasattr(role_output, "feedback") else "",
            stream_callback=stream_callback,
            update_memory_callback=_update_memory_callback,
            user_theme=request.theme if request else "",
            user_style=request.style.value if request else "",
            user_total_words=request.total_words if request else 0,
            user_character_count=request.character_count if request else 0,
            llm_client=self.llm_client,
            mock_mode=self._mock_mode,
        )

        # 提取生成的内容
        generated_content = result.get("generated_content", "") if isinstance(result, dict) else ""
        if not generated_content and hasattr(result, "generated_content"):
            generated_content = result.generated_content

        logger.debug(f"ROLE_ACTOR completed for chapter {chapter_number}, node {node_id}")
        return generated_content
    
    async def _run_self_check(
        self,
        content: str,
        window_content: str,
        chapter_number: int,
        node_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """运行 Self Check 节点 - 支持滑动窗口"""
        plan = context.get("plan")
        request = context.get("request")
        
        # 构建标准
        character_cards = []
        if hasattr(plan, 'character_cards') and plan.character_cards:
            for card in plan.character_cards:
                if hasattr(card, 'model_dump'):
                    character_cards.append(card.model_dump())
                elif isinstance(card, dict):
                    character_cards.append(card)

        standards = {
            'outline': plan.outline if hasattr(plan, 'outline') else '',
            'world_building': plan.world_building if hasattr(plan, 'world_building') else {},
            'characters': character_cards,
        }
        
        # 构建用户输入参数
        user_input = {}
        if request:
            user_input = {
                'theme': getattr(request, 'theme', ''),
                'style': getattr(request, 'style', ''),
                'total_words': getattr(request, 'total_words', 0),
                'character_count': getattr(request, 'character_count', 0),
            }
        
        # 使用滑动窗口内容作为当前章节内容
        current_content = window_content + "\n\n" + content if window_content else content
        
        result = await asyncio.to_thread(
            self_check,
            director_general_standards=standards,
            current_chapter_content=current_content,
            summary=[],  # 可以从 memory_store 获取
            previous_feedback="",
            chapter_id=chapter_number,
            node_id=node_id,
            llm_client=self.llm_client,
            mock_mode=self._mock_mode,
            user_input=user_input,
        )
        
        logger.debug(f"SELF_CHECK completed for chapter {chapter_number}, node {node_id}")
        
        if isinstance(result, dict):
            return result
        elif hasattr(result, 'model_dump'):
            return result.model_dump()
        return {'needs_revision': False}
    
    async def _run_memory_summarizer(
        self,
        chapter_number: int,
        content: str,
        context: Dict[str, Any],
    ) -> None:
        """
        运行 Memory Summarizer 节点

        将章节内容压缩为结构化的记忆卡片，并存储到记忆存储中。
        遵循面向接口原则，通过依赖注入使用 llm_client 和 memory_store。

        Args:
            chapter_number: 章节号
            content: 章节内容文本
            context: 生成上下文，包含 plan 等信息

        Returns:
            None: 记忆卡片直接存储到 memory_store
        """
        plan = context.get("plan")

        # 获取角色名称列表
        character_names = plan.character_names if hasattr(plan, "character_names") else []
        if not character_names and hasattr(plan, "characters"):
            character_names = plan.characters

        # 如果没有角色信息，使用默认角色
        if not character_names:
            character_names = ["旁白"]

        # 构建原始记忆片段
        # 策略：将章节内容按段落分割，为每个主要角色创建记忆
        raw_memories = []
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, paragraph in enumerate(paragraphs[:10]):  # 限制最多10个记忆片段
            # 检测段落中涉及的角色
            mentioned_chars = [name for name in character_names if name in paragraph]
            if not mentioned_chars:
                mentioned_chars = ["旁白"]

            for char in mentioned_chars[:2]:  # 每个段落最多关联2个角色
                raw_memories.append(
                    RawMemory(
                        character=char,
                        content=paragraph[:500],  # 限制内容长度
                        emotion="neutral",  # 简化处理，实际可通过情感分析获取
                    )
                )

        # 如果没有生成记忆，添加一个默认记忆
        if not raw_memories:
            raw_memories.append(
                RawMemory(
                    character=character_names[0] if character_names else "旁白",
                    content=content[:500] if len(content) > 500 else content,
                    emotion="neutral",
                )
            )

        try:
            # 调用 memory_summarizer 节点（在后台线程运行同步函数）
            memory_cards = await asyncio.to_thread(
                memory_summarizer,
                raw_memories=raw_memories,
                llm_client=self.llm_client,
            )

            # 将记忆卡片存储到 memory_store
            if self.memory_store and memory_cards:
                for card in memory_cards:
                    if isinstance(card, dict):
                        # 添加章节信息
                        card["chapter_id"] = chapter_number
                        card["source_chapter"] = chapter_number
                        try:
                            self.memory_store.update_memory(MemoryUpdate(
                            chapter_id=chapter_number,
                            node_id="memory_summarizer",
                            target_character=card.get("character", "global"),
                            new_memories=[json.dumps(card, ensure_ascii=False)],
                            ))
                        except Exception as e:
                            logger.warning(f"Failed to store memory card: {e}")

            logger.debug(f"MEMORY_SUMMARIZER completed for chapter {chapter_number}, generated {len(memory_cards)} cards")
        except Exception as e:
            logger.warning(f"Memory summarization failed for chapter {chapter_number}: {e}")
            # 记忆总结失败不应中断整个生成流程
    

    async def _execute_node_sequence(
        self,
        chapter_number: int,
        chapter_plan: Any,
        context: Dict[str, Any],
        ctx: Any,  # ChapterContextData
    ) -> str:
        """
        执行节点序列，使用 NodeSequence 进行迭代
        
        Args:
            chapter_number: 章节号
            chapter_plan: 章节规划（包含 node_sequence）
            context: 生成上下文
            ctx: 章节上下文数据
            
        Returns:
            str: 拼接后的章节内容
        """
        from core.iterators.node_sequence import NodeSequence
        
        # 获取节点序列
        node_sequence = chapter_plan.node_sequence if hasattr(chapter_plan, 'node_sequence') else []
        if not node_sequence:
            # 兼容旧版本：如果没有 node_sequence，使用默认单节点
            node_sequence = [{'node_id': 0, 'type': 'dialogue', 'description': '默认节点'}]
        
        # 使用 NodeSequence 进行节点迭代
        sequence = NodeSequence(node_sequence)
        chapter_content = ""
        window_contents = {}  # 滑动窗口内容存储
        
        for node in sequence:
            if self._is_stopped:
                break
            
            while self._is_paused:
                await asyncio.sleep(0.5)
            
            node_id = node.get('node_id', f'node_{sequence.get_current_index()}')
            self._current_node = node_id
            
            # 广播进度事件
            self._publish_event("progress", {
                "current": chapter_number,
                "total": self._total_chapters,
                "percentage": round((sequence.get_current_index() / len(node_sequence)) * 100, 1),
                "current_node": node_id,
            })
            
            # 执行节点（带重试逻辑）
            node_result = await self._execute_node_with_retry(
                node=node,
                sequence=sequence,
                chapter_number=chapter_number,
                context=context,
                ctx=ctx,
                window_contents=window_contents,
            )
            
            if node_result['passed']:
                # 保存到滑动窗口
                window_contents[sequence.get_current_index() - 1] = node_result['content']
                chapter_content += node_result['content'] + "\n\n"

                # RAG 保存
                if self.rag:
                    try:
                        await self.rag.add_document(
                            content=node_result['content'],
                            metadata={
                                "chapter_id": chapter_number,
                                "node_id": node_id,
                                "type": node.get('type', 'dialogue'),
                            }
                        )
                        logger.debug(f"Added node {node_id} content to RAG")
                    except Exception as e:
                        logger.warning(f"Failed to add content to RAG: {e}")
                # 重置重试计数
                sequence.retry_count = 0
        
        return chapter_content


    async def _execute_node_with_retry(
        self,
        node: Dict[str, Any],
        sequence: Any,  # NodeSequence
        chapter_number: int,
        context: Dict[str, Any],
        ctx: Any,  # ChapterContextData
        window_contents: Dict[int, str],
    ) -> Dict[str, Any]:
        """
        执行单个节点，支持重试和滑动窗口审查
        
        Args:
            node: 节点定义
            sequence: NodeSequence 迭代器
            chapter_number: 章节号
            context: 生成上下文
            ctx: 章节上下文数据
            window_contents: 滑动窗口内容存储
            
        Returns:
            Dict[str, Any]: {'passed': bool, 'content': str}
        """
        max_retries = self.max_retries
        node_id = node.get('node_id', 'unknown')
        
        while True:
            # 1. 角色分配
            self._current_node = f"ROLE_ASSIGNER_{node_id}"
            role_output = await self._run_role_assigner(chapter_number, node, context)
            
            # 2. RAG 检索（如果配置了 RAG 服务）
            rag_context = []
            if self.rag and hasattr(role_output, 'rag_queries') and role_output.rag_queries:
                try:
                    rag_results = await self.rag.search_multiple(role_output.rag_queries, top_k=3)
                    rag_context = [r.content for results in rag_results for r in results]
                except Exception as e:
                    logger.warning(f"RAG search failed: {e}")
            
            # 3. 角色扮演生成
            self._current_node = f"ROLE_ACTOR_{node_id}"
            content = await self._run_role_actor(
                chapter_number=chapter_number,
                node_id=node_id,
                node_type=node.get('type', 'dialogue'),
                role_output=role_output,
                rag_context=rag_context,
                context=context,
            )

            # 保存版本到滑动窗口
            self.state_manager.add_node_version(sequence.get_current_index() - 1, content)

            # 4. 滑动窗口自检
            self._current_node = f"SELF_CHECK_{node_id}"
            window_content = self._build_window_content(
                current_idx=sequence.get_current_index() - 1,
                window_contents=window_contents
            )
            check_result = await self._run_self_check(
                content=content,
                window_content=window_content,
                chapter_number=chapter_number,
                node_id=node_id,
                context=context,
            )
            
            # 检查是否通过
            if not check_result.get('needs_revision', False):
                return {'passed': True, 'content': content}
            
            # 需要修订，检查重试次数
            if sequence.get_retry_count() >= max_retries:
                logger.warning(f"Node {node_id} exceeded max retries ({max_retries}), triggering human intervention")
                
                # 获取当前节点索引
                current_index = sequence.get_current_index() - 1
                
                # 获取滑动窗口中的版本
                sw = self.state_manager.get_sliding_window()
                node_versions = sw.get("node_contents", {}).get(current_index, {}).get("versions", [])
                
                # 触发人工干预
                intervention_data = {
                    'chapter': chapter_number,
                    'node_index': current_index,
                    'node_id': node_id,
                    'versions': node_versions,
                }
                
                # 设置待重试节点信息（供重试端点查询）
                if self.node_retry_service:
                    self.node_retry_service.set_pending_retry(
                        chapter_id=chapter_number,
                        node_id=node_id,
                        node_index=current_index,
                        versions=node_versions,
                    )
                    logger.info(f"[Intervention] Pending retry set for node {node_id}")
                
                # 广播需要人工审查事件
                logger.info(f"[Intervention] Publishing need_manual_review event for node {node_id}")
                result1 = self._publish_event("need_manual_review", intervention_data)
                logger.info(f"[Intervention] need_manual_review published to {result1} subscribers")
                
                # 同时广播 status 事件，确保前端状态同步
                logger.info(f"[Intervention] Publishing status event with need_human_intervention=True")
                result2 = self._publish_event("status", {
                    'current_chapter': chapter_number,
                    'current_node': node_id,
                    'total_chapters': self._total_chapters,
                    'is_running': True,
                    'is_paused': True,
                    'is_stopped': False,
                    'need_human_intervention': True,
                    'intervention_data': intervention_data,
                })
                logger.info(f"[Intervention] status published to {result2} subscribers")
                
                # 短暂延迟，确保事件有时间被 WebSocket 发送
                logger.info(f"[Intervention] Waiting 0.1s for events to be sent...")
                await asyncio.sleep(0.1)
                logger.info(f"[Intervention] Delay completed")
                
                # 设置干预状态并等待前端响应
                self.state_manager.start_intervention(intervention_data)
                
                # 等待前端响应（通过 is_paused 循环等待）
                while self.state_manager.get_state().get('is_paused', False):
                    await asyncio.sleep(0.5)
                
                # 获取滑动窗口更新
                sw = self.state_manager.get_sliding_window()
                retry_current = sw.get('retry_current', False)
                
                if retry_current:
                    # 重试当前节点
                    self.state_manager.clear_node_versions(current_index)
                    self.state_manager.reset_retry_state()
                    sequence.reset_retry_count()
                    logger.info(f"Manual retry triggered for node {node_id}")
                    continue
                else:
                    # 选择历史版本
                    selected_version_idx = sw.get('selected_version_idx', 0)
                    selected_content = node_versions[selected_version_idx] if node_versions else content

                    # 清空版本历史
                    self.state_manager.clear_node_versions(current_index)

                    # 重置反馈和重试计数
                    self.state_manager.update_state({'chapter_feedback': ''})
                    self.state_manager.reset_retry_state()
                    sequence.reset_retry_count()

                    # 关键修复：清除 retry_index，确保进入下一个节点
                    sequence.retry_index = None

                    logger.info(f"Manual version {selected_version_idx} selected for node {node_id}")
                    return {'passed': True, 'content': selected_content}
            
            # 自动重试
            logger.info(f"Node {node_id} needs revision, retrying ({sequence.get_retry_count() + 1}/{max_retries})")
            sequence.send(check_result.get('improvement_suggestions', ''))
    
    async def _run_text_polisher(self, content: str) -> str:
        """运行 Text Polisher 节点"""
        from schemas import TextPolisherInput
        
        input_data = TextPolisherInput(chapter_text=content)
        result = await asyncio.to_thread(text_polisher, input_data,llm_client=self.llm_client,mock_mode=self._mock_mode)
        
        logger.debug("TEXT_POLISHER completed")
        
        if isinstance(result, dict):
            return result.get('polished_text', content)
        elif hasattr(result, 'polished_text'):
            return result.polished_text
        return content

    def _build_window_content(self, current_idx: int, window_contents: Dict[int, str]) -> str:
        """构建滑动窗口内容"""
        window_start = max(0, current_idx - self.window_size + 1)
        contents = []
        for idx in range(window_start, current_idx + 1):
            if idx in window_contents:
                contents.append(window_contents[idx])
        return "\n\n".join(contents)

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
