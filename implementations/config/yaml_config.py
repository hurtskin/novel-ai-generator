"""
YAML 配置提供者实现

实现 ConfigProvider 接口，提供基于 YAML 文件的配置管理功能
支持配置的加载、解析、获取和更新
"""

import logging
import os
from typing import Any, Dict, List, Optional, TypeVar, Union

import yaml

from interfaces.config import (
    ConfigProvider,
    APIConfig,
    GenerationConfig,
    MemoryConfig,
    PricingConfig,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class YamlConfigProvider(ConfigProvider):
    """
    YAML 配置文件提供者实现
    
    功能特性：
    - 基于 YAML 文件的配置管理
    - 支持点号分隔的键访问（如"api.base_url"）
    - 类型安全的配置获取方法
    - 支持配置热重载
    - 支持运行时配置修改
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 YAML 配置提供者
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config.yaml"
            )
        
        self._config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded config from {self._config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self._config_path}")
            self._config = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}

    def _get_nested_value(self, key: str) -> Any:
        """
        获取嵌套配置值
        
        Args:
            key: 点号分隔的配置键
            
        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Key not found: {key}")
        
        return value

    def _set_nested_value(self, key: str, value: Any) -> None:
        """
        设置嵌套配置值
        
        Args:
            key: 点号分隔的配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value

    def get(self, key: str, default: Optional[T] = None) -> T:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔（如"api.base_url"）
            default: 默认值
            
        Returns:
            T: 配置值
        """
        try:
            return self._get_nested_value(key)
        except KeyError:
            if default is not None:
                return default
            raise

    def get_string(self, key: str, default: str = "") -> str:
        """获取字符串配置"""
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        value = self.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        value = self.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_list(self, key: str, default: Optional[List[Any]] = None) -> List[Any]:
        """获取列表配置"""
        if default is None:
            default = []
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        return default

    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取字典配置"""
        if default is None:
            default = {}
        value = self.get(key, default)
        if isinstance(value, dict):
            return value
        return default

    def get_api_config(self) -> APIConfig:
        """获取 API 配置"""
        api_config = self._config.get("api", {})
        return APIConfig(
            provider=api_config.get("provider", "moonshot"),
            base_url=api_config.get("base_url", "https://api.moonshot.cn/v1"),
            api_key=api_config.get("api_key", ""),
            model=api_config.get("model", "kimi-k2.5"),
            timeout=api_config.get("timeout", 120),
            max_retries=api_config.get("max_retries", 3),
        )

    def get_generation_config(self) -> GenerationConfig:
        """获取生成配置"""
        gen_config = self._config.get("generation", {})
        return GenerationConfig(
            temperature=gen_config.get("temperature", 0.7),
            top_p=gen_config.get("top_p", 0.9),
            max_tokens=gen_config.get("max_tokens", 4096),
            mock_mode=gen_config.get("mock_mode", False),
            debug=gen_config.get("debug", True),
        )

    def get_memory_config(self) -> MemoryConfig:
        """获取记忆配置"""
        mem_config = self._config.get("memory", {})
        return MemoryConfig(
            recent_chapters=mem_config.get("recent_chapters", 3),
            truncation=mem_config.get("truncation", 4000),
            max_total=mem_config.get("max_total", 10000),
            per_chapter=mem_config.get("per_chapter", 2000),
            truncation_strategy=mem_config.get("truncation_strategy", "tail"),
        )

    def get_pricing_config(self, model: str) -> PricingConfig:
        """
        获取模型定价配置
        
        Args:
            model: 模型名称
            
        Returns:
            PricingConfig: 定价配置
        """
        pricing_config = self._config.get("pricing", {}).get(model, {})
        return PricingConfig(
            input_per_million=pricing_config.get("input_per_million", 12.0),
            output_per_million=pricing_config.get("output_per_million", 60.0),
        )

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("Config reloaded")

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值（运行时修改）
        
        Args:
            key: 配置键
            value: 配置值
        """
        self._set_nested_value(key, value)
        logger.debug(f"Set config {key} = {value}")

    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Config saved to {self._config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path
