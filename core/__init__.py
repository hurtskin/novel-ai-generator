"""
核心层 - 业务逻辑和依赖注入

该模块包含：
- 依赖注入容器
- LLM节点业务逻辑
- 迭代器
- 上下文管理
"""

from .container import Container, container

__all__ = ["Container", "container"]
