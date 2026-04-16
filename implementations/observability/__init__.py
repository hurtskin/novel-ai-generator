"""
可观测性实现模块

提供多种可观测性后端实现：
- FileObservabilityBackend: 文件日志实现
- NullObservabilityBackend: 空实现（禁用观测）
- ObservabilityFactoryImpl: 工厂类

使用示例：
    from implementations.observability import FileObservabilityBackend, NullObservabilityBackend
    from implementations.observability import get_factory
    
    # 直接创建后端
    backend = FileObservabilityBackend()
    
    # 或使用工厂
    factory = get_factory()
    backend = factory.get_default_backend()
    
    # 记录日志
    from interfaces.observability import LogLevel
    backend.log_event(LogLevel.INFO, 1, "node_1", "节点开始执行")
    
    # 开始追踪
    span = backend.start_span(1, "node_1")
    
    # 结束追踪
    backend.end_span(
        span,
        usage={"prompt_tokens": 100, "completion_tokens": 50},
        performance={"duration_ms": 1000, "ttf_ms": 200, "tps": 50}
    )
    
    # 获取性能汇总
    summary = backend.get_performance_summary()
"""

from implementations.observability.file_backend import FileObservabilityBackend
from implementations.observability.null_backend import NullObservabilityBackend
from implementations.observability.factory import (
    ObservabilityFactoryImpl,
    get_factory,
    reset_factory,
)

__all__ = [
    "FileObservabilityBackend",
    "NullObservabilityBackend",
    "ObservabilityFactoryImpl",
    "get_factory",
    "reset_factory",
]
