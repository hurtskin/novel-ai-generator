"""
记忆存储接口定义

定义记忆存储和检索的抽象接口，支持多种存储后端（内存、RAG向量存储等）
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryCard:
    """记忆卡片数据类"""
    event_id: str
    timestamp: str
    location: str
    core_action: str
    emotion_marks: Dict[str, str]
    relationship_changes: Dict[str, str]
    key_quote: str
    future_impacts: List[str]
    source_index: str


@dataclass
class MemoryUpdate:
    """记忆更新数据"""
    chapter_id: int
    node_id: str
    target_character: str
    new_memories: List[str]
    emotion_shift: str = ""
    new_discoveries: List[str] = None
    relationship_updates: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.new_discoveries is None:
            self.new_discoveries = []
        if self.relationship_updates is None:
            self.relationship_updates = {}


@dataclass
class RetrievalMetrics:
    """检索性能指标"""
    retrieval_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    cards_retrieved: int = 0
    chars_returned: int = 0


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    character: str
    current_scene: Dict[str, Any]
    retrieved_memories: List[Dict[str, Any]]
    memory_count: int
    total_chars: int
    retrieval_time_ms: float
    config_used: Dict[str, Any]


@dataclass
class CharacterMemory:
    """角色记忆数据"""
    character_name: str
    memories: List[Dict[str, Any]]
    emotions: List[Dict[str, Any]]
    relationships: Dict[str, Any]


class MemoryRetriever(ABC):
    """
    记忆检索器抽象基类
    
    职责：
    - 根据角色和场景检索相关记忆
    - 支持关键词匹配
    - 支持记忆截断
    
    实现类：
    - SimpleMemoryRetriever: 基于关键词的简单检索
    - RAGMemoryRetriever: 基于向量相似度的检索
    """
    
    @abstractmethod
    def retrieve(
        self,
        character: str,
        current_scene: Dict[str, Any],
        global_memory: Dict[str, Any],
        config: Dict[str, Any],
        metrics: Optional[RetrievalMetrics] = None
    ) -> RetrievalResult:
        """
        检索角色相关记忆
        
        Args:
            character: 角色名称
            current_scene: 当前场景信息
            global_memory: 全局记忆存储
            config: 配置参数
            metrics: 性能指标收集器（可选）
            
        Returns:
            RetrievalResult: 检索结果包含相关记忆卡片
        """
        pass
    
    @abstractmethod
    def extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        pass
    
    @abstractmethod
    def validate_token_overflow(self, context: Dict[str, Any], max_tokens: int = 8000) -> bool:
        """
        验证是否超出token限制
        
        Args:
            context: 上下文数据
            max_tokens: 最大token数
            
        Returns:
            bool: 是否超出限制
        """
        pass


class MemoryStore(ABC):
    """
    记忆存储抽象基类
    
    职责：
    - 存储和检索角色记忆
    - 管理章节记忆和全局记忆
    - 支持记忆更新和合并
    
    实现类：
    - SimpleMemoryStore: 基于内存的简单存储
    - RAGMemoryStore: 基于向量检索的存储
    """
    
    @abstractmethod
    def get_character_memory(self, character_name: str) -> Optional[CharacterMemory]:
        """
        获取角色记忆
        
        Args:
            character_name: 角色名称
            
        Returns:
            CharacterMemory: 角色记忆数据，不存在则返回None
        """
        pass
    
    @abstractmethod
    def update_memory(self, memory_update: MemoryUpdate) -> None:
        """
        更新记忆
        
        Args:
            memory_update: 记忆更新数据
        """
        pass
    
    @abstractmethod
    def get_global_memory(self) -> Dict[str, Any]:
        """获取全局记忆"""
        pass
    
    @abstractmethod
    def save_global_memory(self, memory: Dict[str, Any]) -> None:
        """保存全局记忆"""
        pass
    
    @abstractmethod
    def get_chapter_memory(self, chapter_id: int) -> Dict[str, Any]:
        """获取章节记忆"""
        pass
    
    @abstractmethod
    def save_chapter_memory(self, chapter_id: int, memory: Dict[str, Any]) -> None:
        """保存章节记忆"""
        pass
    
    @abstractmethod
    def clear_character_memory(self, character_name: str) -> None:
        """清空角色记忆"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有记忆数据"""
        pass

    @abstractmethod
    def get_all_characters(self) -> List[str]:
        """获取所有角色名称列表"""
        pass
    
    @abstractmethod
    def truncate_memories(
        self,
        memories: List[Dict[str, Any]],
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """
        截断记忆列表到指定字符数
        
        Args:
            memories: 记忆列表
            max_chars: 最大字符数
            
        Returns:
            List[Dict[str, Any]]: 截断后的记忆列表
        """
        pass
    
    @abstractmethod
    def deduplicate_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        去重记忆列表
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的记忆列表
        """
        pass


class MemoryStoreFactory(ABC):
    """记忆存储工厂"""
    
    @abstractmethod
    def create_store(self, backend: str) -> MemoryStore:
        """
        创建记忆存储实例
        
        Args:
            backend: 后端类型（"simple", "rag"）
            
        Returns:
            MemoryStore: 存储实例
        """
        pass
    
    @abstractmethod
    def get_default_store(self) -> MemoryStore:
        """获取默认存储实例"""
        pass
