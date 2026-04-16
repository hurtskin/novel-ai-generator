# 接口定义规范文档

> 本文档定义了 Novel AI Generator 的抽象接口层规范
> 版本: 1.0.0
> 日期: 2026-04-15

---

## 目录

1. [概述](#概述)
2. [接口设计原则](#接口设计原则)
3. [接口清单](#接口清单)
4. [详细接口定义](#详细接口定义)
5. [依赖注入容器](#依赖注入容器)
6. [错误处理规范](#错误处理规范)
7. [扩展指南](#扩展指南)

---

## 概述

### 设计目标

- **解耦**: 业务逻辑与具体实现解耦
- **可测试性**: 支持 Mock 实现进行单元测试
- **可扩展性**: 轻松添加新的实现类
- **可维护性**: 清晰的接口契约和文档

### 架构层次

```
┌─────────────────────────────────────────┐
│              API Layer                  │
│         (FastAPI Routes)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Service Layer                 │
│    (NovelGenerator, StateManager)       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Core Layer                   │
│      (LLM Nodes, Iterators)             │
│         ↓ 依赖接口，不依赖实现           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Interface Layer                 │
│   (LLMClient, MemoryStore, etc.)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Implementation Layer               │
│  (MoonshotClient, SimpleMemoryStore)    │
└─────────────────────────────────────────┘
```

---

## 接口设计原则

### 1. 单一职责原则 (SRP)

每个接口只负责一个明确的功能领域：
- `LLMClient`: 只负责LLM通信
- `MemoryStore`: 只负责记忆存储
- `ObservabilityBackend`: 只负责观测性

### 2. 接口隔离原则 (ISP)

接口应该小而精，避免"胖接口"：
- `MemoryRetriever`: 只负责检索
- `MemoryStore`: 负责存储和检索

### 3. 依赖倒置原则 (DIP)

高层模块依赖抽象接口，不依赖具体实现：
```python
# 正确：依赖接口
def role_actor(client: LLMClient, ...):
    client.chat(...)

# 错误：依赖具体实现
def role_actor(...):
    client = get_llm_client()  # 硬编码依赖
```

### 4. 开闭原则 (OCP)

对扩展开放，对修改关闭：
- 新增LLM提供商：实现 `LLMClient` 接口
- 新增存储后端：实现 `MemoryStore` 接口

---

## 接口清单

| 接口名 | 文件 | 职责 | 实现类 |
|--------|------|------|--------|
| `LLMClient` | `llm_client.py` | LLM通信 | `MoonshotClient`, `OllamaClient` |
| `LLMClientFactory` | `llm_client.py` | 创建LLM客户端 | `LLMClientFactoryImpl` |
| `MemoryStore` | `memory.py` | 记忆存储 | `SimpleMemoryStore`, `RAGMemoryStore` |
| `MemoryRetriever` | `memory.py` | 记忆检索 | `SimpleMemoryRetriever` |
| `ObservabilityBackend` | `observability.py` | 观测性 | `FileObservabilityBackend`, `NullObservabilityBackend` |
| `ConfigProvider` | `config.py` | 配置管理 | `YamlConfigProvider` |
| `StorageBackend` | `storage.py` | 持久化存储 | `JsonStorageBackend` |
| `EmbeddingClient` | `embedding.py` | 文本嵌入 | `InfiniEmbeddingClient` |
| `VectorStore` | `embedding.py` | 向量存储 | `SimpleVectorStore` |

---

## 详细接口定义

### 1. LLMClient 接口

**文件**: `interfaces/llm_client.py`

**职责**: 与大型语言模型进行通信

**核心方法**:

```python
class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[StreamCallback] = None,
        cache_id: Optional[str] = None,
    ) -> ChatResponse:
        pass
```

**数据类**:

```python
@dataclass
class ChatMessage:
    role: str      # "system", "user", "assistant"
    content: str

@dataclass
class ChatResponse:
    content: str
    usage: TokenUsage
    performance: PerformanceMetrics
    model: str
```

**异常体系**:

```
LLMError (基类)
├── LLMRequestError      # 请求错误
├── LLMRateLimitError    # 速率限制
├── LLMTimeoutError      # 超时错误
└── LLMAuthenticationError  # 认证错误
```

---

### 2. MemoryStore 接口

**文件**: `interfaces/memory.py`

**职责**: 管理角色记忆和全局记忆

**核心方法**:

```python
class MemoryStore(ABC):
    @abstractmethod
    def get_character_memory(self, character_name: str) -> Optional[CharacterMemory]:
        pass
    
    @abstractmethod
    def update_memory(self, memory_update: MemoryUpdate) -> None:
        pass
    
    @abstractmethod
    def get_global_memory(self) -> Dict[str, Any]:
        pass
```

**数据类**:

```python
@dataclass
class MemoryUpdate:
    chapter_id: int
    node_id: str
    target_character: str
    new_memories: List[str]
    emotion_shift: str = ""
    new_discoveries: List[str] = None
    relationship_updates: Dict[str, Any] = None

@dataclass
class CharacterMemory:
    character_name: str
    memories: List[Dict[str, Any]]
    emotions: List[Dict[str, Any]]
    relationships: Dict[str, Any]
```

---

### 3. ObservabilityBackend 接口

**文件**: `interfaces/observability.py`

**职责**: 日志、追踪、性能指标收集

**核心方法**:

```python
class ObservabilityBackend(ABC):
    @abstractmethod
    def log_event(self, level: LogLevel, chapter: int, node: str, message: str) -> None:
        pass
    
    @abstractmethod
    def start_span(self, chapter: int, node: str) -> Span:
        pass
    
    @abstractmethod
    def end_span(self, span: Span, usage: Dict[str, int], performance: Dict[str, float]) -> None:
        pass
    
    @abstractmethod
    def broadcast(self, msg_type: str, data: Any) -> None:
        pass
```

---

### 4. ConfigProvider 接口

**文件**: `interfaces/config.py`

**职责**: 配置管理和访问

**核心方法**:

```python
class ConfigProvider(ABC):
    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> T:
        pass
    
    @abstractmethod
    def get_string(self, key: str, default: str = "") -> str:
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        pass
    
    @abstractmethod
    def reload(self) -> None:
        pass
```

**配置数据结构**:

```python
@dataclass
class APIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout: int
    max_retries: int

@dataclass
class GenerationConfig:
    temperature: float
    top_p: float
    max_tokens: int
    mock_mode: bool
    debug: bool
```

---

### 5. StorageBackend 接口

**文件**: `interfaces/storage.py`

**职责**: 数据持久化存储

**核心方法**:

```python
class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        pass
    
    @abstractmethod
    def load(self, key: str, default: Optional[T] = None) -> T:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
```

---

### 6. EmbeddingClient 接口

**文件**: `interfaces/embedding.py`

**职责**: 文本嵌入向量生成

**核心方法**:

```python
class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        pass
```

---

## 依赖注入容器

### Container 类

**文件**: `core/container.py`

**职责**: 管理接口与实现的绑定，解析依赖关系

**核心方法**:

```python
class Container:
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """注册实例（单例）"""
        pass
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], singleton: bool = False) -> None:
        """注册工厂函数"""
        pass
    
    def register_class(self, interface: Type[T], implementation: Type[T], singleton: bool = False) -> None:
        """注册实现类"""
        pass
    
    def resolve(self, interface: Type[T]) -> T:
        """解析接口获取实现"""
        pass
```

**使用示例**:

```python
from core.container import container
from interfaces.llm_client import LLMClient
from implementations.llm.moonshot_client import MoonshotClient

# 注册实现
container.register_class(LLMClient, MoonshotClient, singleton=True)

# 解析依赖
client = container.resolve(LLMClient)
```

---

## 错误处理规范

### 1. 异常层次结构

每个接口模块定义自己的异常层次：

```python
# interfaces/llm_client.py
class LLMError(Exception):
    """LLM相关错误的基类"""
    pass

class LLMRequestError(LLMError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
```

### 2. 错误处理原则

- **不要吞没异常**: 除非有特殊处理需求，否则应该抛出异常
- **提供上下文**: 异常消息应该包含足够的上下文信息
- **使用特定异常**: 不要泛化使用 `Exception`，应该使用具体的异常类型

### 3. 重试机制

对于可重试的错误（如速率限制、超时），在实现层处理：

```python
def chat(self, ...):
    retry_count = 0
    while retry_count <= self.max_retries:
        try:
            return self._do_request(...)
        except LLMRateLimitError:
            retry_count += 1
            time.sleep(2 ** retry_count)  # 指数退避
```

---

## 扩展指南

### 添加新的LLM提供商

1. 创建实现类：

```python
# implementations/llm/openai_client.py
from interfaces.llm_client import LLMClient, ChatResponse

class OpenAIClient(LLMClient):
    def chat(self, messages, ...):
        # 实现OpenAI API调用
        pass
```

2. 注册到容器：

```python
container.register_factory(
    LLMClient,
    lambda: OpenAIClient(),
    singleton=True
)
```

### 添加新的记忆存储后端

1. 创建实现类：

```python
# implementations/memory/redis_memory_store.py
from interfaces.memory import MemoryStore

class RedisMemoryStore(MemoryStore):
    def get_character_memory(self, character_name: str):
        # 实现Redis存储
        pass
```

2. 注册到容器：

```python
container.register_class(MemoryStore, RedisMemoryStore)
```

---

## 文件清单

### 接口定义文件

| 文件路径 | 说明 |
|----------|------|
| `interfaces/__init__.py` | 接口包初始化，导出所有接口 |
| `interfaces/llm_client.py` | LLM客户端接口 |
| `interfaces/memory.py` | 记忆存储接口 |
| `interfaces/observability.py` | 可观测性接口 |
| `interfaces/config.py` | 配置管理接口 |
| `interfaces/storage.py` | 持久化存储接口 |
| `interfaces/embedding.py` | 嵌入服务接口 |

### 核心文件

| 文件路径 | 说明 |
|----------|------|
| `core/__init__.py` | 核心包初始化 |
| `core/container.py` | 依赖注入容器 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-04-15 | 初始版本，定义7个核心接口 |

---

## 附录

### A. 类型注解规范

- 使用 Python 3.9+ 内置泛型类型：`list`, `dict`, `tuple`
- 使用 `Optional` 表示可选参数
- 使用 `Any` 表示任意类型
- 使用自定义数据类表示复杂数据结构

### B. 命名规范

- 接口名：使用名词，首字母大写，如 `LLMClient`
- 方法名：使用动词或动词短语，小写下划线，如 `get_character_memory`
- 数据类：使用名词，首字母大写，如 `ChatMessage`
- 异常名：以 `Error` 结尾，如 `LLMRequestError`
