# 依赖注入容器使用指南

> 本文档介绍 Novel AI Generator 依赖注入容器的使用方法
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [核心功能](#核心功能)
4. [高级特性](#高级特性)
5. [最佳实践](#最佳实践)
6. [故障排除](#故障排除)

---

## 概述

本项目实现了功能完善的依赖注入容器，支持：

- 接口到实现的绑定
- 构造函数自动注入
- 多种生命周期管理（Transient、Singleton、Scoped）
- 循环依赖检测
- 命名注册
- 工厂函数注册

### 架构位置

```
core/
├── container.py           # 容器核心实现
└── container_config.py    # 容器配置和初始化
```

---

## 快速开始

### 1. 创建容器

```python
from core.container import Container, Scope

# 创建容器实例
container = Container()
```

### 2. 定义接口

```python
from typing import Protocol
from abc import abstractmethod

class ILogger(Protocol):
    @abstractmethod
    def log(self, message: str) -> None:
        pass
```

### 3. 实现类

```python
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")
```

### 4. 注册依赖

```python
# 注册实现
container.register(ILogger, ConsoleLogger)
```

### 5. 解析依赖

```python
# 解析依赖
logger = container.resolve(ILogger)
logger.log("Hello, DI!")  # 输出: [LOG] Hello, DI!
```

---

## 核心功能

### 生命周期管理

容器支持三种生命周期：

#### Transient（瞬态）

每次解析都创建新实例（默认）：

```python
container.register(ILogger, ConsoleLogger, Scope.TRANSIENT)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 和 logger2 是不同的实例
assert logger1 is not logger2
```

#### Singleton（单例）

整个容器共享一个实例：

```python
container.register(ILogger, ConsoleLogger, Scope.SINGLETON)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 和 logger2 是相同的实例
assert logger1 is logger2
```

#### Scoped（作用域）

在同一线程内共享实例：

```python
container.register(ILogger, ConsoleLogger, Scope.SCOPED)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 和 logger2 是相同的实例（同一线程）
assert logger1 is logger2
```

### 构造函数自动注入

容器自动解析构造函数的参数类型：

```python
class IDatabase(Protocol):
    def query(self, sql: str) -> list:
        pass

class Database:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def query(self, sql: str) -> list:
        self.logger.log(f"Query: {sql}")
        return []

# 注册
container.register(ILogger, ConsoleLogger)
container.register(IDatabase, Database)

# 解析 - 自动注入 ILogger
db = container.resolve(IDatabase)
# db.logger 已经被自动注入
```

### 命名注册

支持同一接口的多个实现：

```python
class FileLogger:
    def __init__(self, filename: str = "app.log"):
        self.filename = filename
    
    def log(self, message: str) -> None:
        with open(self.filename, 'a') as f:
            f.write(f"{message}\n")

# 注册多个实现
container.register(ILogger, ConsoleLogger, name="console")
container.register(ILogger, FileLogger, name="file")

# 按名称解析
console_logger = container.resolve(ILogger, name="console")
file_logger = container.resolve(ILogger, name="file")

# 获取所有实现
all_loggers = container.resolve_all(ILogger)
```

### 工厂函数注册

使用工厂函数创建实例：

```python
def create_database(container):
    logger = container.resolve(ILogger)
    return Database(logger, connection_string="custom")

container.register_factory(IDatabase, create_database)
```

### 实例注册

直接注册已创建的实例（自动作为单例）：

```python
logger_instance = ConsoleLogger()
container.register_instance(ILogger, logger_instance)
```

---

## 高级特性

### 循环依赖检测

容器自动检测循环依赖并抛出异常：

```python
class ServiceA:
    def __init__(self, b: 'ServiceB'):
        self.b = b

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

container.register(ServiceA, ServiceA)
container.register(ServiceB, ServiceB)

# 抛出 CircularDependencyError
try:
    container.resolve(ServiceA)
except CircularDependencyError as e:
    print(f"循环依赖: {e}")
```

### 可选依赖

构造函数参数可以有默认值：

```python
class OptionalService:
    def __init__(self, logger: ILogger = None):
        self.logger = logger

container.register(OptionalService, OptionalService)

# 可以正常解析，logger 为 None
service = container.resolve(OptionalService)
```

### 链式注册

支持流畅的链式调用：

```python
container \
    .register(ILogger, ConsoleLogger) \
    .register(IDatabase, Database) \
    .register(IConfig, AppConfig, Scope.SINGLETON)
```

### 全局容器

使用全局容器简化代码：

```python
from core.container import get_global_container, reset_global_container

# 获取全局容器
container = get_global_container()

# 注册和解析
container.register(ILogger, ConsoleLogger)
logger = container.resolve(ILogger)

# 重置全局容器（测试时使用）
reset_global_container()
```

### 服务提供者

创建只读的服务提供者：

```python
# 配置容器
container.register(ILogger, ConsoleLogger)
container.register(IDatabase, Database)

# 创建只读提供者
provider = container.build_provider()

# 只能解析，不能注册
logger = provider.resolve(ILogger)
```

---

## 最佳实践

### 1. 项目中的使用模式

本项目使用容器的方式：

```python
# core/container_config.py
from core.container import Container, Scope
from interfaces.llm_client import LLMClient, LLMClientFactory
from interfaces.memory import MemoryStore
# ... 其他接口

def configure_container(container: Container) -> Container:
    """配置容器绑定"""
    
    # 注册 LLM 客户端工厂
    from implementations.llm.factory import LLMClientFactoryImpl
    container.register(LLMClientFactory, LLMClientFactoryImpl, Scope.SINGLETON)
    
    # 注册记忆存储
    from implementations.memory.simple_memory_store import SimpleMemoryStore
    container.register(MemoryStore, SimpleMemoryStore, Scope.SINGLETON)
    
    # ... 其他注册
    
    return container

def initialize_container() -> Container:
    """初始化并返回配置好的容器"""
    container = Container()
    configure_container(container)
    return container
```

### 2. 在 FastAPI 中使用

```python
# api/dependencies.py
from fastapi import Request
from core.container import Container

def get_container(request: Request) -> Container:
    """从请求状态获取容器"""
    return request.app.state.container

def get_llm_client(container: Container = Depends(get_container)) -> LLMClient:
    """获取 LLM 客户端"""
    factory = container.resolve(LLMClientFactory)
    config = container.resolve(ConfigProvider)
    return factory.create_client(config.get("api"))
```

### 3. 在 LLM 节点中使用

```python
# core/nodes/role_actor.py
from interfaces.llm_client import LLMClient
from interfaces.memory import MemoryStore

class RoleActorNode:
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore
    ):
        self.llm_client = llm_client
        self.memory_store = memory_store
    
    def execute(self, input_data: RoleActorInput) -> RoleActorOutput:
        # 使用注入的依赖
        memory = self.memory_store.get_character_memory(
            input_data.target_character
        )
        response = self.llm_client.chat(messages=[...])
        # ...
```

### 4. 测试中使用 Mock

```python
# tests/test_nodes.py
import pytest
from unittest.mock import Mock
from core.container import Container

def test_role_actor_with_mock():
    """使用 Mock 测试 RoleActor 节点"""
    container = Container()
    
    # 创建 Mock
    mock_llm = Mock(spec=LLMClient)
    mock_llm.chat.return_value = ChatResponse(
        content="生成的内容",
        usage=TokenUsage(100, 50, 150),
        performance=PerformanceMetrics(0, 0, 0, 0),
        model="mock"
    )
    
    mock_memory = Mock(spec=MemoryStore)
    mock_memory.get_character_memory.return_value = CharacterMemory(
        character_name="主角",
        memories=[],
        emotions=[],
        relationships={}
    )
    
    # 注册 Mock
    container.register_instance(LLMClient, mock_llm)
    container.register_instance(MemoryStore, mock_memory)
    
    # 测试
    node = RoleActorNode(
        llm_client=container.resolve(LLMClient),
        memory_store=container.resolve(MemoryStore)
    )
    
    result = node.execute(input_data)
    
    # 验证
    assert result.generated_content == "生成的内容"
    mock_llm.chat.assert_called_once()
```

---

## 故障排除

### 异常处理

容器定义了以下异常类型：

| 异常 | 描述 | 解决方案 |
|------|------|----------|
| `DependencyNotFoundError` | 依赖未注册 | 检查注册代码，确保先注册再解析 |
| `CircularDependencyError` | 发现循环依赖 | 重构代码，使用接口打破循环 |
| `ResolutionError` | 解析失败 | 检查构造函数参数是否都可解析 |
| `RegistrationError` | 注册失败 | 检查接口和实现类定义 |

### 常见问题

#### Q: 解析时提示依赖未找到

```python
# 错误：先解析后注册
logger = container.resolve(ILogger)  # DependencyNotFoundError
container.register(ILogger, ConsoleLogger)

# 正确：先注册后解析
container.register(ILogger, ConsoleLogger)
logger = container.resolve(ILogger)
```

#### Q: 循环依赖如何解决

```python
# 错误：直接相互依赖
class A:
    def __init__(self, b: B):  # B 依赖 A
        self.b = b

class B:
    def __init__(self, a: A):  # A 依赖 B
        self.a = a

# 解决：使用接口打破循环
class IServiceA(Protocol):
    pass

class IServiceB(Protocol):
    pass

class A:
    def __init__(self, b: IServiceB):  # 依赖接口
        self.b = b

class B:
    def __init__(self, a: IServiceA):  # 依赖接口
        self.a = a
```

#### Q: 如何调试依赖解析

```python
# 打印容器中的所有注册
interfaces = container.get_registered_interfaces()
for interface in interfaces:
    print(f"Interface: {interface.__name__}")
    registrations = container._registrations.get(interface, [])
    for reg in registrations:
        print(f"  -> {reg.implementation.__name__} ({reg.scope.name})")
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，添加 Scoped 生命周期支持 |
| 1.1.0 | 2026-04-15 | 添加全局容器和链式注册 |
| 1.0.0 | 2026-04-01 | 初始版本 |
