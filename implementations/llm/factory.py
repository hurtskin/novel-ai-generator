"""
LLM 客户端工厂实现

实现 LLMClientFactory 接口，根据配置创建对应的 LLM 客户端实例
支持 Moonshot、Ollama 等多种提供商
"""

import os
from typing import Optional
import yaml

from interfaces.llm_client import LLMClient, LLMClientFactory
from implementations.llm.moonshot_client import MoonshotClient
from implementations.llm.ollama_client import OllamaClient


class LLMClientFactoryImpl(LLMClientFactory):
    """
    LLM 客户端工厂实现
    
    职责：
    - 根据配置创建对应的 LLM 客户端
    - 支持多种 LLM 提供商的切换
    - 管理客户端实例的生命周期
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化工厂
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        self._clients: dict[str, LLMClient] = {}

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()
        # 清除缓存的客户端实例，下次创建时会使用新配置
        self._clients.clear()

    def create_client(self, provider: str) -> LLMClient:
        """
        创建 LLM 客户端
        
        Args:
            provider: 提供商名称（"moonshot", "ollama"等）
            
        Returns:
            LLMClient: 对应提供商的客户端实例
            
        Raises:
            ValueError: 不支持的提供商
        """
        # 检查缓存
        if provider in self._clients:
            return self._clients[provider]

        # 创建新实例
        if provider == "moonshot":
            client = MoonshotClient(self._config_path)
        elif provider == "ollama":
            client = OllamaClient(self._config_path)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # 缓存实例
        self._clients[provider] = client
        return client

    def get_default_client(self) -> LLMClient:
        """
        获取默认配置的客户端
        
        根据配置文件中的 provider 设置决定使用哪个客户端
        
        Returns:
            LLMClient: 默认客户端实例
        """
        provider = self._config.get("api", {}).get("provider", "moonshot")
        
        # 检查是否启用了 Ollama
        if provider == "ollama":
            ollama_config = self._config.get("ollama", {})
            if ollama_config.get("enabled", False):
                return self.create_client("ollama")
            # Ollama 未启用，回退到 Moonshot
            return self.create_client("moonshot")
        
        return self.create_client(provider)

    def get_client(self, provider: Optional[str] = None) -> LLMClient:
        """
        获取客户端（便捷方法）
        
        Args:
            provider: 提供商名称，None 则使用默认配置
            
        Returns:
            LLMClient: 客户端实例
        """
        if provider is None:
            return self.get_default_client()
        return self.create_client(provider)


# 全局工厂实例（单例）
_factory: Optional[LLMClientFactoryImpl] = None


def get_factory(config_path: Optional[str] = None) -> LLMClientFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        LLMClientFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = LLMClientFactoryImpl(config_path)
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    _factory = None
