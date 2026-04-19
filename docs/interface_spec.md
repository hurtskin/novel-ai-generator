# 接口定义规范文档

> 本文档定义 Novel AI Generator 的抽象接口层规范
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [概述](#概述)
2. [设计原则](#设计原则)
3. [接口清单](#接口清单)
4. [详细接口定义](#详细接口定义)
5. [异常体系](#异常体系)
6. [最佳实践](#最佳实践)

---

## 概述

### 设计目标

- **解耦**: 业务逻辑与具体实现完全解耦
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

## 设计原则

### 1. 单一职责原则 (SRP)

每个接口只负责一个明确的功能领域：
- `LLMClient`: 只负责 LLM 通信
- `MemoryStore`: 只负责记忆存储
- `ObservabilityBackend`: 只负责可观测性

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
- 新增 LLM 提供商：实现 `LLMClient` 接口
- 新增存储后端：实现 `MemoryStore` 接口

---

## 接口清单

| 接口名 | 文件 | 职责 | 实现类 |
|--------|------|------|--------|
| `LLMClient` | `llm_client.py` | LLM 通信 | `MoonshotClient`, `OllamaClient` |
| `LLMClientFactory` | `llm_client.py` | 创建 LLM 客户端 | `LLMClientFactoryImpl` |
| `MemoryStore` | `memory.py` | 记忆存储 | `SimpleMemoryStore`, `RAGMemoryStore` |
| `MemoryRetriever` | `memory.py` | 记忆检索 | `SimpleMemoryRetriever` |
| `ObservabilityBackend` | `observability.py` | 可观测性 | `FileObservabilityBackend`, `NullObservabilityBackend` |
| `ConfigProvider` | `config.py` | 配置管理 | `YamlConfigProvider` |
| `StorageBackend` | `storage.py` | 持久化存储 | `JsonStorageBackend` |
| `EmbeddingClient` | `embedding.py` | 文本嵌入 | `InfiniEmbeddingClient` |
| `VectorStore` | `embedding.py` | 向量存储 | `SimpleVectorStore` |

---

## 详细接口定义

### 1. LLMClient 接口

**文件**: `interfaces/llm_client.py`

**职责**: 与大型语言模型进行通信

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
        """
        与 LLM 进行对话
        
        Args:
            messages: 消息列表
            model: 模型名称（可选，使用配置默认值）
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            stream_callback: 流式回调函数
            cache_id: 上下文缓存 ID
            
        Returns:
            ChatResponse: 包含生成内容、用量和性能指标
        """
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

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class PerformanceMetrics:
    ttf_ms: float           # 首 Token 延迟
    tps: float              # 生成速度
    api_latency_ms: float   # API 延迟
    cost_usd: float         # 预估成本
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

```python
class MemoryStore(ABC):
    @abstractmethod
    def get_character_memory(self, character_name: str) -> Optional[CharacterMemory]:
        """获取角色记忆"""
        pass
    
    @abstractmethod
    def update_memory(self, memory_update: MemoryUpdate) -> None:
        """更新记忆"""
        pass
    
    @abstractmethod
    def get_global_memory(self) -> Dict[str, Any]:
        """获取全局记忆"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有记忆"""
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

```python
class ObservabilityBackend(ABC):
    @abstractmethod
    def log_event(self, level: LogLevel, chapter: int, node: str, message: str) -> None:
        """记录事件日志"""
        pass
    
    @abstractmethod
    def start_span(self, chapter: int, node: str) -> Span:
        """开始追踪跨度"""
        pass
    
    @abstractmethod
    def end_span(self, span: Span, usage: Dict[str, int], performance: Dict[str, float]) -> None:
        """结束追踪跨度"""
        pass
    
    @abstractmethod
    def broadcast(self, msg_type: str, data: Any) -> None:
        """广播消息到 WebSocket 客户端"""
        pass
    
    @abstractmethod
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """记录指标"""
        pass
```

---

### 4. ConfigProvider 接口

**文件**: `interfaces/config.py`

**职责**: 配置管理和访问

```python
class ConfigProvider(ABC):
    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> T:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔（如 "api.model"）
            default: 默认值
        """
        pass
    
    @abstractmethod
    def get_string(self, key: str, default: str = "") -> str:
        """获取字符串配置"""
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载配置"""
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

```python
class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """保存数据"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查数据是否存在"""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有键"""
        pass
```

---

### 6. EmbeddingClient 接口

**文件**: `interfaces/embedding.py`

**职责**: 文本向量化

```python
class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表，每个向量是一个浮点数数组
        """
        pass
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        pass
```

---

### 7. VectorStore 接口

**文件**: `interfaces/embedding.py`

**职责**: 向量存储和检索

```python
class VectorStore(ABC):
    @abstractmethod
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """添加向量数据"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        相似度检索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有数据"""
        pass
```

---

## 异常体系

### 基础异常类

```python
class InterfaceError(Exception):
    """接口层基础异常"""
    pass

class ConfigurationError(InterfaceError):
    """配置错误"""
    pass

class NotImplementedError(InterfaceError):
    """方法未实现"""
    pass
```

### LLM 相关异常

```python
class LLMError(InterfaceError):
    """LLM 客户端基础异常"""
    pass

class LLMRequestError(LLMError):
    """请求错误（4xx）"""
    pass

class LLMRateLimitError(LLMError):
    """速率限制（429）"""
    pass

class LLMTimeoutError(LLMError):
    """超时错误"""
    pass

class LLMAuthenticationError(LLMError):
    """认证错误（401）"""
    pass
```

### 存储相关异常

```python
class StorageError(InterfaceError):
    """存储基础异常"""
    pass

class StorageNotFoundError(StorageError):
    """数据不存在"""
    pass

class StorageIOError(StorageError):
    """IO 错误"""
    pass
```

---

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

### 2. 使用工厂模式

对于需要配置的实现，使用工厂模式：

```python
class LLMClientFactory(ABC):
    @abstractmethod
    def create_client(self, config: Dict[str, Any]) -> LLMClient:
        pass

class MoonshotClientFactory(LLMClientFactory):
    def create_client(self, config: Dict[str, Any]) -> LLMClient:
        return MoonshotClient(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
```

### 3. 异常处理

在实现层捕获具体异常，转换为接口异常：

```python
class MoonshotClient(LLMClient):
    def chat(self, messages, **kwargs) -> ChatResponse:
        try:
            response = self._make_request(messages, **kwargs)
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError("Rate limit exceeded")
            elif e.response.status_code == 401:
                raise LLMAuthenticationError("Invalid API key")
            else:
                raise LLMRequestError(f"HTTP error: {e}")
        except requests.Timeout:
            raise LLMTimeoutError("Request timeout")
```

### 4. 类型注解

始终使用完整的类型注解：

```python
from typing import Optional, List, Dict, Any

def process_memory(
    memory: MemoryStore,
    character: str,
    updates: List[MemoryUpdate]
) -> Dict[str, Any]:
    ...
```

### 5. 文档字符串

为所有接口方法编写文档字符串：

```python
def chat(
    self,
    messages: List[ChatMessage],
    model: Optional[str] = None,
    **kwargs
) -> ChatResponse:
    """
    与 LLM 进行对话
    
    Args:
        messages: 消息列表，格式为 [{"role": "...", "content": "..."}]
        model: 模型名称，None 表示使用默认模型
        **kwargs: 其他参数
        
    Returns:
        ChatResponse: 包含生成内容和性能指标
        
    Raises:
        LLMRateLimitError: 达到速率限制
        LLMTimeoutError: 请求超时
    """
    pass
```

---

## 扩展指南

### 添加新的 LLM 后端

1. 创建实现类：

```python
# implementations/llm/openai_client.py
from interfaces.llm_client import LLMClient, ChatMessage, ChatResponse

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def chat(self, messages, **kwargs) -> ChatResponse:
        # 实现 OpenAI API 调用
        pass
```

2. 创建工厂：

```python
class OpenAIClientFactory(LLMClientFactory):
    def create_client(self, config: Dict[str, Any]) -> LLMClient:
        return OpenAIClient(
            api_key=config["api_key"],
            base_url=config.get("base_url", "https://api.openai.com/v1")
        )
```

3. 注册到容器：

```python
container.register(LLMClientFactory, OpenAIClientFactory, name="openai")
```

### 添加新的存储后端

1. 实现 StorageBackend 接口
2. 创建对应的工厂类
3. 在容器配置中注册

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，添加 EmbeddingClient 和 VectorStore 接口 |
| 1.1.0 | 2026-04-15 | 添加 ConfigProvider 接口 |
| 1.0.0 | 2026-04-01 | 初始版本 |
