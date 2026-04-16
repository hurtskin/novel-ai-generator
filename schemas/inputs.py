"""
输入数据模型

包含所有输入数据模型，包括 API 请求参数、用户输入验证模型等
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field

from schemas.common import (
    CacheConfig,
    CachedContent,
    CurrentNodeInfo,
    CharacterProfileData,
)

if TYPE_CHECKING:
    from schemas.outputs import DirectorGeneralOutput


class DirectorGeneralInput(BaseModel):
    """总导演节点输入"""
    theme: str
    style: str
    total_words: int
    character_count: int
    genre: str
    cache_config: Optional[CacheConfig] = Field(default=None, description="Context Caching 配置")
    cached_static_context: Optional[CachedContent] = Field(default=None, description="已缓存的静态上下文")


class DirectorChapterInput(BaseModel):
    """章节导演节点输入"""
    chapter_id: int
    director_general_output: DirectorGeneralOutput
    genre: str
    feedback: Optional[str] = None
    user_theme: str = ""
    user_style: str = ""
    user_total_words: int = 0
    user_character_count: int = 0


class ChapterOutlineInput(BaseModel):
    """章节大纲输入"""
    chapter_id: int
    title: str
    summary: str
    key_events: List[str]
    characters_involved: List[str]


class RoleAssignerInput(BaseModel):
    """角色分配器节点输入"""
    current_node: CurrentNodeInfo
    character_profile: CharacterProfileData
    genre: str
    current_situation: str
    goals: str
    constraints: List[str] = Field(default_factory=list)
    user_theme: str = ""
    user_style: str = ""
    user_total_words: int = 0
    user_character_count: int = 0
    character_names: List[str] = Field(default_factory=list, description="固定的角色姓名列表")
    character_cards: List[Dict[str, Any]] = Field(default_factory=list, description="所有角色的详细卡片信息（字典列表）")
    cache_config: Optional[CacheConfig] = Field(default=None, description="Context Caching 配置")
    cached_static_context: Optional[CachedContent] = Field(default=None, description="已缓存的静态上下文")
    feedback: str = Field(default="", description="审查反馈，用于改进生成内容")
    generated_summaries: List[str] = Field(default_factory=list, description="之前已经生成完的所有单元的精简描述")


class TextPolisherInput(BaseModel):
    """文本润色节点输入"""
    chapter_text: str = Field(description="当前章节的文本内容，需要润色的原始文本")
