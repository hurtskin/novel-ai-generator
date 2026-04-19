# 工具参考手册

本文档提供 Novel AI Generator 中所有核心工具和组件的详细使用参考。

---

## 目录

- [LLM 客户端](#llm-客户端)
- [LLM 节点](#llm-节点)
- [依赖注入容器](#依赖注入容器)
- [配置管理](#配置管理)
- [存储后端](#存储后端)
- [记忆系统](#记忆系统)
- [嵌入服务](#嵌入服务)
- [可观测性](#可观测性)

---

## LLM 客户端

### 接口定义

```python
from interfaces import LLMClient, LLMClientFactory

class LLMClient(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> LLMResponse:
        pass
```

### MoonshotClient 实现

Moonshot API 客户端，支持流式输出和性能指标收集。

#### 初始化

```python
from implementations.llm.moonshot_client import MoonshotClient
from implementations.llm.factory import LLMClientFactoryImpl

# 通过工厂创建
factory = LLMClientFactoryImpl()
client = factory.create(
    base_url="https://api.moonshot.cn/v1",
    api_key="your-api-key",
    default_model="kimi-k2.5"
)

# 或直接实例化
client = MoonshotClient(
    base_url="https://api.moonshot.cn/v1",
    api_key="your-api-key",
    default_model="kimi-k2.5",
    timeout=60,
    max_retries=3
)
```

#### chat 方法

与 LLM API 交互并获取响应。

**参数：**

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| messages | List[Dict[str, str]] | 是 | 消息列表，格式为 `[{"role": "system", "content": "..."}, ...]` |
| model | str | 否 | 模型名称，默认使用配置中的模型 |
| temperature | float | 否 | 温度参数，控制随机性 |
| top_p | float | 否 | top_p 参数，控制多样性 |
| max_tokens | int | 否 | 最大生成 token 数 |
| stream_callback | Callable[[str], None] | 否 | 流式回调函数，每个 token 触发 |

**返回值 (LLMResponse)：**

```python
{
    "content": "完整生成文本",
    "usage": {
        "prompt_tokens": 1200,
        "completion_tokens": 800,
        "total_tokens": 2000
    },
    "performance": {
        "ttf_ms": 450.0,          # 首次响应时间
        "tps": 45.2,              # tokens per second
        "api_latency_ms": 320.0,  # API 延迟
        "cost_usd": 0.0087        # 预估成本（美元）
    }
}
```

**示例：**

```python
response = await client.chat(
    messages=[
        {"role": "system", "content": "你是一个专业的小说作家。"},
        {"role": "user", "content": "写一个关于AI的短篇故事开头。"}
    ],
    temperature=0.7,
    max_tokens=1000,
    stream_callback=lambda token: print(token, end="")
)

print(f"\n总 token: {response['usage']['total_tokens']}")
print(f"成本: ${response['performance']['cost_usd']:.4f}")
```

#### 成本计算

使用 Moonshot 官方定价（2026年4月）：

| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| kimi-k2.5 | 12 元/百万 token | 60 元/百万 token |

**计算公式：**

```
cost_cny = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
cost_usd = cost_cny / exchange_rate  # 汇率约 7.2
```

**示例：**

```
输入: 1200 tokens, 输出: 800 tokens
输入成本: 1200 * 12 / 1_000_000 = 0.0144 元
输出成本: 800 * 60 / 1_000_000 = 0.048 元
总成本: 0.0624 元 ≈ 0.0087 USD
```

#### 重试逻辑

- 最多重试 3 次
- 指数退避：1s, 2s, 4s
- 处理错误码：
  - 429: 速率限制
  - 500-599: 服务端错误
  - 网络超时

#### 流式解析

SSE 格式解析示例：

```
data: {"choices": [{"delta": {"content": "你"}}]}
data: {"choices": [{"delta": {"content": "好"}}]}
data: {"choices": [{"delta": {"content": "！"}}]}
data: [DONE]
```

### OllamaClient 实现

Ollama 本地模型客户端。

#### 初始化

```python
from implementations.llm.ollama_client import OllamaClient

client = OllamaClient(
    base_url="http://localhost:11434",
    default_model="llama3.2:latest",
    timeout=120
)
```

#### 特点

- 支持本地模型运行
- 无需 API 密钥
- 适合开发和测试
- 支持模型热切换

---

## LLM 节点

### director_general - 总导演节点

生成作品的全局规划和设定。

#### 输入 (DirectorGeneralInput)

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| theme | str | 是 | 小说主题 |
| style | str | 是 | 写作风格 |
| total_words | int | 是 | 目标总字数 |
| character_count | int | 是 | 角色数量 |
| genre | str | 是 | 文体类型 (novel/script/game_story/dialogue/article) |

#### 输出 (DirectorGeneralOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| world_building | WorldBuilding | 世界观设定 |
| writing_style | WritingStyle | 写作风格对象 |
| outline | List[ChapterOutline] | 章节大纲列表 |
| chapter_count | int | 章节总数 |
| characters | List[CharacterProfile] | 角色档案列表 |
| conflict_design | ConflictDesign | 冲突设计 |
| foreshadowing | List[HookDesign] | 伏笔设计列表 |
| character_arcs | List[ArcDesign] | 角色弧光列表 |
| tone | str | 整体基调 |
| genre_specific | GenreSpecific | 文体特定配置 |
| _metadata | dict | 元数据（性能指标、usage统计） |

#### 使用示例

```python
from core.nodes.director_general import DirectorGeneralNode
from schemas import DirectorGeneralInput

node = DirectorGeneralNode(llm_client)

input_data = DirectorGeneralInput(
    theme="AI觉醒与人类共存",
    style="赛博朋克悬疑",
    total_words=100000,
    character_count=5,
    genre="novel"
)

result = await node.execute(input_data)

print(f"章节数: {result.chapter_count}")
print(f"角色数: {len(result.characters)}")
print(f"成本: ${result._metadata['performance']['cost_usd']:.4f}")
```

#### Genre 类型处理

| genre | 处理指令 |
|-------|----------|
| novel | 强调章节结构和角色弧光 |
| script | 强调场景镜头和对白格式 |
| game_story | 强调分支选择和状态机 |
| dialogue | 强调多轮对话和记忆累积 |
| article | 强调论点论据结构 |

### director_chapter - 章节导演节点

将章节大纲转换为详细的场景序列。

#### 输入 (DirectorChapterInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| chapter_outline | ChapterOutline | 当前章节大纲 |
| world_building | WorldBuilding | 世界观设定 |
| characters | List[CharacterProfile] | 角色列表 |
| previous_chapter_summary | str | 前一章摘要 |
| chapter_id | int | 章节ID |

#### 输出 (DirectorChapterOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| scenes | List[Scene] | 场景列表 |
| scene_count | int | 场景数量 |
| estimated_words | int | 预估字数 |
| chapter_arc | str | 本章弧光描述 |

### role_assigner - 角色分配节点

为每个场景选择合适的角色并准备提示词。

#### 输入 (RoleAssignerInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| scene | Scene | 当前场景 |
| characters | List[CharacterProfile] | 可用角色列表 |
| chapter_memory | List[str] | 本章记忆 |
| global_memory | GlobalMemory | 全局记忆 |

#### 输出 (RoleAssignerOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| target_character | str | 目标角色名称 |
| generation_prompt | PromptComponents | 生成提示词组件 |
| scene_context | str | 场景上下文 |

### role_actor - 角色扮演节点

扮演指定角色生成内容。

#### 输入 (RoleActorInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| generation_prompt | PromptComponents | 生成提示词组件 |
| chapter_id | int | 当前章节ID |
| node_id | str | 当前节点ID |
| node_type | str | 节点类型 |
| target_character | str | 目标角色 |
| genre | str | 文体类型 |
| stream_callback | Callable | 流式回调（可选） |

#### 输出 (RoleActorOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| generated_content | str | 生成的内容 |
| state_change_report | StateChangeReport | 状态变更报告 |
| unit_type | str | 单元类型 |

### memory_summarizer - 记忆总结节点

压缩原始记忆为结构化记忆卡片。

#### 输入 (MemorySummarizerInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| raw_memories | List[RawMemory] | 原始记忆列表 |
| max_cards | int | 最大卡片数 |

#### 输出 (MemorySummarizerOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| summary_cards | List[MemoryCard] | 记忆卡片列表 |

### self_check - 自检节点

检查生成内容的一致性和质量。

#### 输入 (SelfCheckInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| content | str | 待检查内容 |
| check_type | str | 检查类型 |
| reference_material | Dict | 参考材料 |

#### 输出 (SelfCheckOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| passed | bool | 是否通过 |
| issues | List[str] | 问题列表 |
| suggestions | List[str] | 建议列表 |
| score | float | 质量评分 |

### text_polisher - 文本润色节点

润色和优化生成内容。

#### 输入 (TextPolisherInput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| content | str | 待润色内容 |
| polish_type | str | 润色类型 |
| style_hints | str | 风格提示 |

#### 输出 (TextPolisherOutput)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| polished_content | str | 润色后的内容 |
| changes | List[str] | 修改列表 |

---

## 依赖注入容器

### 容器初始化

```python
from core.container import Container
from core.container_config import configure_container

# 创建容器
container = Container()

# 配置容器
configure_container(container)

# 或手动注册
container.register_instance(ConfigProvider, config_provider)
container.register_factory(LLMClient, lambda c: create_llm_client(c.resolve(ConfigProvider)))
```

### 服务解析

```python
# 解析服务
llm_client = container.resolve(LLMClient)
memory_store = container.resolve(MemoryStore)

# 带生命周期解析
with container.create_scope() as scope:
    scoped_service = scope.resolve(MyService)
    # 使用服务
```

### 构造函数注入

```python
class MyService:
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        config: ConfigProvider
    ):
        self.llm_client = llm_client
        self.memory_store = memory_store
        self.config = config

# 自动注入
service = container.resolve(MyService)
```

---

## 配置管理

### YamlConfigProvider

YAML 配置文件管理，支持热重载。

#### 初始化

```python
from implementations.config.yaml_config import YamlConfigProvider

config = YamlConfigProvider("config.yaml")
```

#### 方法

| 方法名 | 返回类型 | 描述 |
|--------|----------|------|
| get(key, default=None) | Any | 获取配置值 |
| get_str(key, default="") | str | 获取字符串配置 |
| get_int(key, default=0) | int | 获取整数配置 |
| get_float(key, default=0.0) | float | 获取浮点数配置 |
| get_bool(key, default=False) | bool | 获取布尔配置 |
| get_list(key, default=[]) | List | 获取列表配置 |
| get_dict(key, default={}) | Dict | 获取字典配置 |
| reload() | None | 重新加载配置 |

#### 配置示例

```yaml
api:
  provider: moonshot
  base_url: "https://api.moonshot.cn/v1"
  api_key: "${API_KEY}"
  model: "kimi-k2.5"
  timeout: 60
  max_retries: 3

generation:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 4096

memory:
  truncation: 8000
  vector_dim: 1024

pricing:
  kimi-k2.5:
    input_per_million: 12
    output_per_million: 60
```

---

## 存储后端

### JsonStorageBackend

JSON 文件持久化存储。

#### 初始化

```python
from implementations.storage.json_storage import JsonStorageBackend

storage = JsonStorageBackend(base_path="./output")
```

#### 方法

| 方法名 | 参数 | 返回 | 描述 |
|--------|------|------|------|
| save | key, data | bool | 保存数据 |
| load | key | Optional[Dict] | 加载数据 |
| delete | key | bool | 删除数据 |
| exists | key | bool | 检查存在 |
| list_keys | prefix | List[str] | 列出键 |

#### 使用示例

```python
# 保存数据
storage.save("global_memory", global_memory_dict)

# 加载数据
data = storage.load("global_memory")

# 删除数据
storage.delete("global_memory")

# 列出键
keys = storage.list_keys("chapter_")
```

---

## 记忆系统

### SimpleMemoryStore

基于内存的字典存储，适合开发和测试。

```python
from implementations.memory.simple_memory_store import SimpleMemoryStore

memory = SimpleMemoryStore()
memory.store_global(key="world_building", value=world_data)
memory.store_chapter(chapter_id=1, key="summary", value=summary)
```

### RAGMemoryStore

基于向量检索的 RAG 存储，支持语义搜索。

```python
from implementations.memory.rag_memory_store import RAGMemoryStore

memory = RAGMemoryStore(
    embedding_client=embedding_client,
    vector_store=vector_store
)

# 存储记忆
memory.store_global(
    key="character_profile_1",
    value=character_data,
    metadata={"type": "character", "name": "林深"}
)

# 检索相关记忆
results = memory.retrieve_relevant(
    query="林深的背景故事",
    top_k=5,
    filter={"type": "character"}
)
```

---

## 嵌入服务

### InfiniEmbeddingClient

InfiniAI 嵌入服务客户端。

```python
from implementations.embedding.infini_embedding import InfiniEmbeddingClient

client = InfiniEmbeddingClient(
    api_key="your-api-key",
    model="infini-embedding-v1",
    batch_size=32
)

# 获取嵌入向量
vectors = await client.embed(["文本1", "文本2", "文本3"])

# 获取单个嵌入
vector = await client.embed_one("单个文本")
```

### SimpleVectorStore

简单的内存向量存储。

```python
from implementations.embedding.infini_embedding import SimpleVectorStore

store = SimpleVectorStore(dimension=1024)

# 添加向量
store.add(
    id="doc1",
    vector=vector,
    metadata={"source": "chapter1"}
)

# 搜索相似向量
results = store.search(
    query_vector=query_vec,
    top_k=5,
    filter={"source": "chapter1"}
)
```

---

## 可观测性

### FileObservabilityBackend

文件日志观测后端。

```python
from implementations.observability.file_backend import FileObservabilityBackend

obs = FileObservabilityBackend(
    log_dir="./logs",
    app_name="novel-ai"
)

# 记录日志
obs.log_info("Generation started", context={"chapter_id": 1})
obs.log_error("API failed", error=exception, context={"retry": 2})

# 记录追踪
with obs.start_trace("chapter_generation", {"chapter_id": 1}) as span:
    span.add_event("director_general_started")
    # 执行业务逻辑
    span.add_event("director_general_completed")

# 记录性能指标
obs.record_metric("llm_latency", 450.0, {"model": "kimi-k2.5"})
```

### NullObservabilityBackend

空观测后端，零开销，适合生产环境禁用观测。

```python
from implementations.observability.null_backend import NullObservabilityBackend

obs = NullObservabilityBackend()
# 所有方法调用都是空操作
```

---

## 快速参考

### 常用导入

```python
# 接口
from interfaces import (
    LLMClient, LLMClientFactory,
    MemoryStore, MemoryRetriever,
    ConfigProvider,
    StorageBackend,
    ObservabilityBackend,
    EmbeddingClient, VectorStore
)

# 实现
from implementations.llm.factory import LLMClientFactoryImpl
from implementations.memory.factory import MemoryStoreFactoryImpl
from implementations.config.yaml_config import YamlConfigProvider
from implementations.storage.json_storage import JsonStorageBackend

# 核心
from core.container import Container
from core.container_config import configure_container

# 节点
from core.nodes import (
    DirectorGeneralNode,
    DirectorChapterNode,
    RoleAssignerNode,
    RoleActorNode,
    MemorySummarizerNode,
    SelfCheckNode,
    TextPolisherNode
)

# 模式
from schemas import (
    DirectorGeneralInput, DirectorGeneralOutput,
    RoleActorInput, RoleActorOutput,
    MemoryCard, RawMemory
)
```

### 配置模板

```yaml
# config.yaml
api:
  provider: moonshot
  base_url: "https://api.moonshot.cn/v1"
  api_key: "${API_KEY}"
  model: "kimi-k2.5"
  timeout: 60
  max_retries: 3

generation:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 4096

memory:
  truncation: 8000
  vector_dim: 1024
  use_rag: true

storage:
  base_path: "./output"

observability:
  enabled: true
  log_dir: "./logs"

pricing:
  kimi-k2.5:
    input_per_million: 12
    output_per_million: 60
```

---

## 故障排除

### 常见问题

#### API 速率限制

**症状：** 429 Too Many Requests

**解决：**

```python
# 增加重试次数和退避时间
client = MoonshotClient(
    max_retries=5,
    # 使用更长的超时
    timeout=120
)
```

#### 内存溢出

**症状：** 生成长内容时内存不足

**解决：**

```python
# 使用流式输出
await client.chat(
    messages=messages,
    stream_callback=lambda t: write_to_file(t)
)
```

#### 循环依赖

**症状：** Container 报错 Circular dependency detected

**解决：**

```python
# 使用属性注入替代构造函数注入
class ServiceA:
    def __init__(self):
        self._service_b = None
    
    @property
    def service_b(self):
        if self._service_b is None:
            self._service_b = container.resolve(ServiceB)
        return self._service_b
```

---

*文档版本：2.0.0 | 最后更新：2026-04-19*
