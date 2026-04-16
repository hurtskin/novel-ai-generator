"""
可观测性后端工厂实现

实现 ObservabilityFactory 接口，根据配置创建对应的观测性后端实例
支持 FileObservabilityBackend 和 NullObservabilityBackend 两种实现
"""

import os
from typing import Optional
import yaml

from interfaces.observability import ObservabilityBackend, ObservabilityFactory
from implementations.observability.file_backend import FileObservabilityBackend
from implementations.observability.null_backend import NullObservabilityBackend


class ObservabilityFactoryImpl(ObservabilityFactory):
    """
    可观测性后端工厂实现
    
    职责：
    - 根据配置创建观测性后端实例
    - 支持多种后端类型切换
    - 管理后端实例的生命周期
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
        self._backends: dict[str, ObservabilityBackend] = {}

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()
        # 清除缓存的后端实例，下次创建时会使用新配置
        self._backends.clear()

    def create_backend(self, backend_type: str) -> ObservabilityBackend:
        """
        创建观测性后端
        
        Args:
            backend_type: 后端类型（"file", "null"）
            
        Returns:
            ObservabilityBackend: 观测性后端实例
            
        Raises:
            ValueError: 不支持的后端类型
        """
        # 检查缓存
        if backend_type in self._backends:
            return self._backends[backend_type]

        # 创建新实例
        if backend_type == "file":
            backend = FileObservabilityBackend(self._config_path)
        elif backend_type == "null":
            backend = NullObservabilityBackend()
        else:
            raise ValueError(f"Unsupported observability backend type: {backend_type}")

        # 缓存实例
        self._backends[backend_type] = backend
        return backend

    def get_default_backend(self) -> ObservabilityBackend:
        """
        获取默认观测性后端
        
        根据配置文件中的设置决定使用哪种后端
        
        Returns:
            ObservabilityBackend: 默认观测性后端实例
        """
        # 从配置中读取观测后端类型
        generation_config = self._config.get("generation", {})
        debug_mode = generation_config.get("debug", True)
        
        # 如果 debug 模式关闭，使用空后端
        if not debug_mode:
            return self.create_backend("null")
        
        # 默认使用文件后端
        return self.create_backend("file")

    def get_backend(self, backend_type: Optional[str] = None) -> ObservabilityBackend:
        """
        获取观测性后端（便捷方法）
        
        Args:
            backend_type: 后端类型，None 则使用默认配置
            
        Returns:
            ObservabilityBackend: 观测性后端实例
        """
        if backend_type is None:
            return self.get_default_backend()
        return self.create_backend(backend_type)


# 全局工厂实例（单例）
_factory: Optional[ObservabilityFactoryImpl] = None


def get_factory(config_path: Optional[str] = None) -> ObservabilityFactoryImpl:
    """
    获取全局工厂实例（单例）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ObservabilityFactoryImpl: 工厂实例
    """
    global _factory
    if _factory is None:
        _factory = ObservabilityFactoryImpl(config_path)
    return _factory


def reset_factory() -> None:
    """重置全局工厂实例（用于测试）"""
    global _factory
    _factory = None
