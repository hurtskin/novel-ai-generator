"""
配置实现模块

提供配置管理实现：
- YamlConfigProvider: YAML 配置文件提供者
- ConfigProviderFactoryImpl: 工厂类

使用示例：
    from implementations.config import YamlConfigProvider, get_factory
    
    # 直接创建提供者
    config = YamlConfigProvider("./config.yaml")
    
    # 或使用工厂
    factory = get_factory()
    config = factory.get_default_provider()
    
    # 获取配置值
    base_url = config.get("api.base_url")
    timeout = config.get_int("api.timeout", 120)
    
    # 获取类型化配置
    api_config = config.get_api_config()
    gen_config = config.get_generation_config()
    
    # 重新加载配置
    config.reload()
"""

from implementations.config.yaml_config import YamlConfigProvider
from implementations.config.factory import (
    ConfigProviderFactoryImpl,
    get_factory,
    reset_factory,
)

__all__ = [
    "YamlConfigProvider",
    "ConfigProviderFactoryImpl",
    "get_factory",
    "reset_factory",
]
