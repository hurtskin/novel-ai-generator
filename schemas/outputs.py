"""
输出数据模型

包含所有输出数据模型，包括 API 响应模型、数据返回格式定义等
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from schemas.common import (
    ChapterOutlineRef,
    NodeConfig,
    GenreSpecific,
    CharacterCard,
)


class DirectorGeneralOutput(BaseModel):
    """总导演节点输出"""
    world_building: str
    writing_style: str
    outline: List[str]
    chapter_count: int
    characters: List[str]
    character_names: List[str]
    character_cards: List[CharacterCard] = Field(default_factory=list)
    conflict_design: str
    foreshadowing: List[str]
    character_arcs: List[str]
    tone: str
    genre_specific: GenreSpecific


class DirectorChapterOutput(BaseModel):
    """章节导演节点输出"""
    chapter_outline: ChapterOutlineRef
    node_sequence: List[NodeConfig]
    node_count: int
    character_presence_plan: Dict[str, List[int]]
    genre_specific: GenreSpecific


class PromptComponents(BaseModel):
    """提示词组件"""
    identity: str
    current_event: str = ""
    expected_reaction: str = ""
    long_term_memory: List[str]
    short_term_memory: List[str]
    recent_events: str
    current_situation: str
    relationships: Dict[str, str]
    items: List[str]
    goals: str
    constraints: List[str]
    genre_hints: str
    summary: List[str] = Field(default_factory=list, description="已生成内容的精简描述")
    rag_context: List[Dict[str, Any]] = Field(default_factory=list, description="RAG 检索结果列表")
    cache_config: Optional[dict] = Field(default=None, description="Context Caching 配置")
    cached_static_context: Optional[dict] = Field(default=None, description="已缓存的静态上下文")


class RoleAssignerOutput(BaseModel):
    """角色分配器节点输出"""
    target_character: str
    generation_prompt: PromptComponents
    feedback: str = Field(default="", description="审查反馈，传递给 RoleActor")
    rag_queries: List[str] = Field(default_factory=list, description="RAG 检索语句列表，由角色分配节点生成")


class StateChangeReport(BaseModel):
    """状态变更报告"""
    summary: str


class RoleActorOutput(BaseModel):
    """角色演绎节点输出"""
    generated_content: str
    state_change_report: StateChangeReport


class SelfCheckOutput(BaseModel):
    """自检节点输出"""
    needs_revision: bool
    issue_types: List[str]
    specific_issues: List[str]
    improvement_suggestions: str


class TextPolisherOutput(BaseModel):
    """文本润色节点输出"""
    polished_text: str = Field(description="润色后的文本内容")
