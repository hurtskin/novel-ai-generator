"""
核心节点模块

提供 LLM 工作流中的各个节点实现：
- director_general: 总导演节点，生成作品大纲
- director_chapter: 章节导演节点，生成章节执行计划
- role_assigner: 角色分配节点，生成角色扮演提示
- role_actor: 角色演绎节点，生成角色扮演内容
- self_check: 自检节点，审阅内容质量
- memory_summarizer: 记忆总结节点，压缩记忆片段
- text_polisher: 文本润色节点，提升文本质量

使用示例：
    from core.nodes import director_general, director_chapter
    from core.nodes import role_assigner, role_actor
    from core.nodes import self_check, memory_summarizer, text_polisher
    
    # 总导演节点
    result = director_general(input_data, llm_client)
    
    # 章节导演节点
    chapter_plan = director_chapter(chapter_input, llm_client)
    
    # 角色分配节点
    role_output = role_assigner(role_input, llm_client)
    
    # 角色演绎节点
    actor_output = role_actor(role_output, chapter_id, node_id, llm_client=llm_client)
    
    # 自检节点
    check_result = self_check(standards, content, summary, llm_client=llm_client)
    
    # 记忆总结节点
    memory_cards = memory_summarizer(raw_memories, llm_client)
    
    # 文本润色节点
    polished = text_polisher(polisher_input, llm_client)
"""

from core.nodes.director_general import director_general
from core.nodes.director_chapter import director_chapter
from core.nodes.role_assigner import role_assigner
from core.nodes.role_actor import role_actor
from core.nodes.self_check import self_check, validate_loop_guard, handle_revision_needed
from core.nodes.memory_summarizer import memory_summarizer
from core.nodes.text_polisher import text_polisher

__all__ = [
    "director_general",
    "director_chapter",
    "role_assigner",
    "role_actor",
    "self_check",
    "validate_loop_guard",
    "handle_revision_needed",
    "memory_summarizer",
    "text_polisher",
]
