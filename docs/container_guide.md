# 依赖注入容器使用指南

## 概述

本项目实现了功能完善的依赖注入容器，支持：
- 接口到实现的绑定
- 构造函数自动注入
- 多种生命周期管理（Transient、Singleton、Scoped）
- 循环依赖检测
- 命名注册
- 工厂函数注册

## 快速开始

### 1. 创建容器

```python
from core.container import Container, Scope

# 创建容器实例
container = Container()
```

### 2. 注册依赖

```python
from typing import Protocol
from abc import abstractmethod

# 定义接口
class ILogger(Protocol):
    @abstractmethod
    def log(self, message: str) -> None:
        pass

# 实现类
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

# 注册实现
container.register(ILogger, ConsoleLogger)
```

### 3. 解析依赖

```python
# 解析依赖
logger = container.resolve(ILogger)
logger.log("Hello, DI!")
```

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
```

#### Singleton（单例）
整个容器共享一个实例：

```python
container.register(ILogger, ConsoleLogger, Scope.SINGLETON)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 和 logger2 是相同的实例
```

#### Scoped（作用域）
在同一线程内共享实例：

```python
container.register(ILogger, ConsoleLogger, Scope.SCOPED)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 和 logger2 是相同的实例（同一线程）
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

## 异常处理

容器定义了以下异常类型：

- `ContainerError`: 所有容器异常的基类
- `DependencyNotFoundError`: 依赖未注册
- `CircularDependencyError`: 发现循环依赖
- `ResolutionError`: 解析失败
- `RegistrationError`: 注册失败

```python
from core.container import (
    DependencyNotFoundError,
    CircularDependencyError,
    ResolutionError
)

try:
    service = container.resolve(IService)
except DependencyNotFoundError:
    print("依赖未找到")
except CircularDependencyError as e:
    print(f"循环依赖: {e}")
except ResolutionError as e:
    print(f"解析失败: {e}")
```

## 最佳实践

### 1. 面向接口编程

始终定义接口（Protocol），然后注册实现：

```python
# 好的做法
class IEmailService(Protocol):
    def send(self, to: str, subject: str, body: str) -> None:
        pass

class SmtpEmailService:
    def send(self, to: str, subject: str, body: str) -> None:
        # SMTP 实现
        pass

container.register(IEmailService, SmtpEmailService)
```

### 2. 生命周期选择

- **Transient**: 无状态服务，每次需要新实例
- **Singleton**: 有状态共享服务，如配置、连接池
- **Scoped**: 请求级别的服务，如数据库会话

### 3. 避免循环依赖

如果检测到循环依赖，考虑重构：

```python
# 不好的做法 - 循环依赖
class ServiceA:
    def __init__(self, b: 'ServiceB'):
        self.b = b

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

# 好的做法 - 使用事件或中介者
class ServiceA:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

class ServiceB:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus
```

### 4. 模块组织

将相关服务的注册组织到模块中：

```python
class ServicesModule:
    def __init__(self, container: Container):
        self.container = container
    
    def configure(self):
        self.container \
            .register(ILogger, ConsoleLogger, Scope.SINGLETON) \
            .register(IDatabase, Database, Scope.SCOPED) \
            .register(IEmailService, SmtpEmailService)

# 使用
module = ServicesModule(container)
module.configure()
```

## 完整示例

```python
from typing import Protocol
from abc import abstractmethod
from core.container import Container, Scope, get_global_container

# 定义接口
class ILogger(Protocol):
    @abstractmethod
    def log(self, message: str) -> None:
        pass

class IDatabase(Protocol):
    @abstractmethod
    def query(self, sql: str) -> list:
        pass

class IEmailService(Protocol):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        pass

# 实现类
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

class Database:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def query(self, sql: str) -> list:
        self.logger.log(f"Query: {sql}")
        return []

class EmailService:
    def __init__(self, logger: ILogger, db: IDatabase):
        self.logger = logger
        self.db = db
    
    def send(self, to: str, subject: str, body: str) -> None:
        self.logger.log(f"Sending email to {to}")
        self.db.query("INSERT INTO emails ...")

# 配置容器
def configure_services(container: Container):
    container \
        .register(ILogger, ConsoleLogger, Scope.SINGLETON) \
        .register(IDatabase, Database, Scope.SCOPED) \
        .register(IEmailService, EmailService, Scope.TRANSIENT)

# 使用
def main():
    container = get_global_container()
    configure_services(container)
    
    # 解析服务
    email_service = container.resolve(IEmailService)
    email_service.send("user@example.com", "Hello", "World")

if __name__ == "__main__":
    main()
```

## 测试支持

在测试中使用容器：

```python
import unittest
from core.container import Container, Scope, reset_global_container

class TestService(unittest.TestCase):
    def setUp(self):
        self.container = Container()
        # 或者使用新的全局容器
        reset_global_container()
        self.container = get_global_container()
    
    def test_service(self):
        # 注册 mock 实现
        self.container.register(ILogger, MockLogger)
        
        # 测试
        service = self.container.resolve(IService)
        result = service.do_work()
        
        self.assertEqual(result, "expected")
```
