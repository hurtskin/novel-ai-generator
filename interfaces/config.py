"""
配置管理接口定义

定义配置获取和管理的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from pathlib import Path


T = TypeVar('T')


@dataclass
class APIConfig:
    """API配置"""
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout: int
    max_retries: int


@dataclass
class GenerationConfig:
    """生成配置"""
    temperature: float
    top_p: float
    max_tokens: int
    mock_mode: bool
    debug: bool


@dataclass
class MemoryConfig:
    """记忆配置"""
    recent_chapters: int
    truncation: int
    max_total: int
    per_chapter: int
    truncation_strategy: str


@dataclass
class PricingConfig:
    """定价配置"""
    input_per_million: float
    output_per_million: float


class ConfigProvider(ABC):
    """
    配置提供者抽象基类
    
    职责：
    - 加载和解析配置文件
    - 提供类型安全的配置获取
    - 支持配置热重载
    
    实现类：
    - YamlConfigProvider: YAML配置文件实现
    """
    
    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> T:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔（如"api.base_url"）
            default: 默认值
            
        Returns:
            T: 配置值
        """
        pass
    
    @abstractmethod
    def get_string(self, key: str, default: str = "") -> str:
        """获取字符串配置"""
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        pass
    
    @abstractmethod
    def get_list(self, key: str, default: Optional[List[Any]] = None) -> List[Any]:
        """获取列表配置"""
        pass
    
    @abstractmethod
    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取字典配置"""
        pass
    
    @abstractmethod
    def get_api_config(self) -> APIConfig:
        """获取API配置"""
        pass
    
    @abstractmethod
    def get_generation_config(self) -> GenerationConfig:
        """获取生成配置"""
        pass
    
    @abstractmethod
    def get_memory_config(self) -> MemoryConfig:
        """获取记忆配置"""
        pass
    
    @abstractmethod
    def get_pricing_config(self, model: str) -> PricingConfig:
        """
        获取模型定价配置
        
        Args:
            model: 模型名称
            
        Returns:
            PricingConfig: 定价配置
        """
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值（运行时修改）
        
        Args:
            key: 配置键
            value: 配置值
        """
        pass
    
    @abstractmethod
    def save(self) -> None:
        """保存配置到文件"""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        pass


class ConfigProviderFactory(ABC):
    """配置提供者工厂"""
    
    @abstractmethod
    def create_provider(self, config_path: str) -> ConfigProvider:
        """
        创建配置提供者
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ConfigProvider: 配置提供者实例
        """
        pass
