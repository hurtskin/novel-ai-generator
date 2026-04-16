"""
服务层接口定义

定义所有服务的抽象接口，实现业务逻辑与实现的解耦
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GenerationStatus(str, Enum):
    """生成状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class NovelStyle(str, Enum):
    """小说文体枚举"""
    NOVEL = "novel"
    SCRIPT = "script"
    GAME_STORY = "game_story"
    DIALOGUE = "dialogue"
    ARTICLE = "article"


@dataclass
class GenerationRequest:
    """生成请求数据类"""
    theme: str
    style: NovelStyle = NovelStyle.NOVEL
    total_words: int = 10000
    character_count: int = 3
    genre: str = "modern"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class GenerationProgress:
    """生成进度数据类"""
    current_chapter: int
    total_chapters: int
    current_node: str
    percentage: float
    status: GenerationStatus
    message: Optional[str] = None


@dataclass
class ChapterResult:
    """章节结果数据类"""
    chapter_number: int
    title: str
    content: str
    word_count: int
    node_results: Dict[str, Any]


@dataclass
class GenerationResult:
    """生成结果数据类"""
    task_id: str
    status: GenerationStatus
    chapters: List[ChapterResult]
    total_word_count: int
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SnapshotInfo:
    """快照信息数据类"""
    id: str
    name: str
    description: Optional[str]
    created_at: str
    chapter: int
    node: str
    version: str = "1.0"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StateSnapshot:
    """状态快照数据类"""
    generation_state: Dict[str, Any]
    memory_state: Dict[str, Any]
    observability_state: Dict[str, Any]
    timestamp: str
    version: str = "1.0"


class NovelGeneratorService(ABC):
    """
    小说生成服务接口
    
    职责：
    - 接收并验证生成请求
    - 协调各节点完成内容生成
    - 管理生成进度和状态
    - 提供错误处理和重试机制
    """
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        执行小说生成
        
        Args:
            request: 生成请求
            
        Returns:
            GenerationResult: 生成结果
            
        Raises:
            GenerationError: 生成失败时
        """
        pass
    
    @abstractmethod
    async def generate_chapter(
        self,
        chapter_number: int,
        context: Dict[str, Any],
    ) -> ChapterResult:
        """
        生成单个章节
        
        Args:
            chapter_number: 章节号
            context: 生成上下文
            
        Returns:
            ChapterResult: 章节结果
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: GenerationRequest) -> bool:
        """
        验证生成请求
        
        Args:
            request: 生成请求
            
        Returns:
            bool: 验证是否通过
        """
        pass


class StateManagerService(ABC):
    """
    状态管理服务接口
    
    职责：
    - 维护生成过程状态
    - 提供状态查询和更新
    - 实现状态持久化
    - 支持状态变更通知
    """
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict[str, Any]: 当前状态
        """
        pass
    
    @abstractmethod
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        更新状态
        
        Args:
            updates: 状态更新
        """
        pass
    
    @abstractmethod
    def reset_state(self) -> None:
        """重置状态"""
        pass
    
    @abstractmethod
    def get_progress(self) -> GenerationProgress:
        """
        获取生成进度
        
        Returns:
            GenerationProgress: 生成进度
        """
        pass
    
    @abstractmethod
    def subscribe(self, callback: Callable[[str, Any], None]) -> str:
        """
        订阅状态变更
        
        Args:
            callback: 回调函数
            
        Returns:
            str: 订阅ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
        """
        pass
    
    @abstractmethod
    async def save_state(self) -> None:
        """保存状态到持久化存储"""
        pass
    
    @abstractmethod
    async def load_state(self) -> None:
        """从持久化存储加载状态"""
        pass


class SnapshotManagerService(ABC):
    """
    快照管理服务接口
    
    职责：
    - 创建和管理快照
    - 支持快照回滚
    - 实现版本控制
    - 管理快照元数据
    """
    
    @abstractmethod
    async def create_snapshot(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> SnapshotInfo:
        """
        创建快照
        
        Args:
            name: 快照名称
            description: 快照描述
            
        Returns:
            SnapshotInfo: 快照信息
        """
        pass
    
    @abstractmethod
    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        恢复快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 恢复是否成功
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    def list_snapshots(self) -> List[SnapshotInfo]:
        """
        获取快照列表
        
        Returns:
            List[SnapshotInfo]: 快照列表
        """
        pass
    
    @abstractmethod
    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotInfo]:
        """
        获取快照信息
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            Optional[SnapshotInfo]: 快照信息
        """
        pass
    
    @abstractmethod
    async def auto_snapshot(self, trigger: str) -> Optional[SnapshotInfo]:
        """
        自动创建快照
        
        Args:
            trigger: 触发条件
            
        Returns:
            Optional[SnapshotInfo]: 快照信息（如果不满足条件则返回None）
        """
        pass


class ServiceError(Exception):
    """服务层基础异常"""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class GenerationError(ServiceError):
    """生成服务异常"""
    
    def __init__(self, message: str, node: Optional[str] = None):
        self.node = node
        super().__init__(message, "GENERATION_ERROR")


class StateError(ServiceError):
    """状态服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "STATE_ERROR")


class SnapshotError(ServiceError):
    """快照服务异常"""
    
    def __init__(self, message: str, snapshot_id: Optional[str] = None):
        self.snapshot_id = snapshot_id
        super().__init__(message, "SNAPSHOT_ERROR")
