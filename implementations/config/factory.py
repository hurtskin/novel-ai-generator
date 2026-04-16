"""
配置提供者工厂实现

实现 ConfigProviderFactory 接口，创建对应的配置提供者实例
"""

import logging
from typing import Optional

from interfaces.config import ConfigProvider, ConfigProviderFactory
from implementations.config.yaml_config import YamlConfigProvider

logger = logging.getLogger(__name__)


class ConfigProviderFactoryImpl(ConfigProviderFactory):
    """
    配置提供者工厂实现
    
    职责：
    - 根据配置创建配置提供者实例
    - 支持多种配置格式（YAML、JSON等）
    - 管理提供者实例的生命周期
    """

    def __init__(self):
        """初始化工厂"""
        self._providers: dict[str, ConfigProvider] = {}

    def create_provider(self, config_path: str, provider_type: str = "yaml") -> ConfigProvider:
        """
        创建配置提供者
        
        Args:
            config_path: 配置文件路径
            provider_type: 提供者类型（"yaml", "json"）
            
        Returns:
            ConfigProvider: 配置提供者实例
            
        Raises:
            ValueError: 不支持的提供者类型
        """
        # 检查缓存
        cache_key = f"{provider_type}_{config_path}"
        if cache_key in self._providers:
            return self._providers[cache_key]

        # 创建新实例
        if provider_type == "yaml":
            provider = YamlConfigProvider(config_path)
        elif provider_type == "json":
            # 预留 JSON 提供者支持
            raise NotImplementedError("JSON config provider not implemented yet")
        else:
            raise ValueError(f"Unsupported config provider type: {provider_type}")

        # 缓存实例
        self._providers[cache_key] = provider
        logger.info(f"Created {provider_type} config provider for {config_path}")
        return provider

    def get_default_provider(self, config_path: Optional[str] = None) -> ConfigProvider:
        """
        获取默认配置提供者
        
        Args:
            config_path: 配置文件路径，None 则使用默认路径
            
        Returns:
            ConfigProvider: 默认配置提供者实例（YAML）
        """
        if config_path is None:
            return YamlConfigProvider()
        return self.create_provider(config_path, "yaml")


# 全局工厂实例（单例）
_factory: Optional[ConfigProviderFactoryImpl] = None


def get_factory() -> ConfigProviderFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Returns:
        ConfigProviderFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = ConfigProviderFactoryImpl()
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    _factory = None
