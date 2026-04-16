"""
LLM 客户端接口定义

定义与大型语言模型交互的抽象接口，支持多种LLM提供商（Moonshot、Ollama等）
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int = 0


@dataclass
class PerformanceMetrics:
    """性能指标"""
    ttf_ms: float  # Time To First Token
    tps: float  # Tokens Per Second
    duration_ms: float  # 总耗时
    api_latency_ms: float  # API延迟
    retry_count: int = 0  # 重试次数


@dataclass
class ChatResponse:
    """LLM聊天响应"""
    content: str
    usage: TokenUsage
    performance: PerformanceMetrics
    model: str
    finish_reason: Optional[str] = None


# 流式回调类型定义
StreamCallback = Callable[[str], None]


class LLMClient(ABC):
    """
    LLM客户端抽象基类
    
    职责：
    - 与LLM API进行通信
    - 处理流式输出
    - 自动重试机制
    - 性能指标收集
    
    实现类：
    - MoonshotClient: Moonshot API实现
    - OllamaClient: Ollama本地模型实现
    """
    
    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[StreamCallback] = None,
        cache_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        发送聊天请求到LLM
        
        Args:
            messages: 聊天消息列表
            model: 模型名称，None则使用默认模型
            temperature: 温度参数
            top_p: Top-p采样参数
            max_tokens: 最大生成token数
            stream_callback: 流式输出回调函数
            cache_id: 缓存ID（用于Context Caching）
            
        Returns:
            ChatResponse: 包含生成内容、使用统计和性能指标
            
        Raises:
            LLMRequestError: 请求失败时抛出
            LLMRateLimitError: 触发速率限制时抛出
            LLMTimeoutError: 请求超时时抛出
        """
        pass
    
    @abstractmethod
    def chat_with_completion_check(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[StreamCallback] = None,
        check_interval: int = 100,
    ) -> ChatResponse:
        """
        流式调用并检查JSON完整性，如果完整则提前返回
        
        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: Top-p采样参数
            max_tokens: 最大生成token数
            stream_callback: 流式输出回调函数
            check_interval: 检查间隔（字符数）
            
        Returns:
            ChatResponse: 包含生成内容和性能指标
        """
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        """获取当前使用的模型名称"""
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: 估算的token数量
        """
        pass
    
    @abstractmethod
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0
    ) -> float:
        """
        计算API调用成本
        
        Args:
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            cached_tokens: 缓存token数
            
        Returns:
            float: 成本（USD）
        """
        pass


class LLMClientFactory(ABC):
    """
    LLM客户端工厂
    
    职责：
    - 根据配置创建对应的LLM客户端
    - 支持多种LLM提供商的切换
    """
    
    @abstractmethod
    def create_client(self, provider: str) -> LLMClient:
        """
        创建LLM客户端
        
        Args:
            provider: 提供商名称（"moonshot", "ollama"等）
            
        Returns:
            LLMClient: 对应提供商的客户端实例
        """
        pass
    
    @abstractmethod
    def get_default_client(self) -> LLMClient:
        """获取默认配置的客户端"""
        pass


# 异常定义
class LLMError(Exception):
    """LLM相关错误的基类"""
    pass


class LLMRequestError(LLMError):
    """请求错误"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class LLMRateLimitError(LLMError):
    """速率限制错误"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """超时错误"""
    pass


class LLMAuthenticationError(LLMError):
    """认证错误"""
    pass
