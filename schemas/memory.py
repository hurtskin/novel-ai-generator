"""
记忆相关数据模型

包含会话历史、上下文存储等记忆管理相关的数据结构
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MemoryCard(BaseModel):
    """记忆卡片"""
    event_id: str
    timestamp: str
    location: str
    core_action: str
    emotion_marks: Dict[str, str]
    relationship_changes: Dict[str, str]
    key_quote: str
    future_impacts: List[str]
    source_index: str


class RawMemory(BaseModel):
    """原始记忆"""
    character: str
    content: str
    emotion: str
