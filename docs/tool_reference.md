# 工具参考手册

## LlmClient

LLM 客户端单例类，支持 Moonshot API 和 Ollama 本地模型。

### 初始化

```python
from llm_client import get_llm_client

client = get_llm_client()
```

### 方法

#### `chat(messages, model=None, temperature=None, top_p=None, max_tokens=None, stream_callback=None)`

与 LLM API 交互并获取响应。

**参数：**
- `messages` (list[dict]): 消息列表，格式为 `[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]`
- `model` (str, optional): 模型名称，默认使用配置文件中的模型
- `temperature` (float, optional): 温度参数
- `top_p` (float, optional): top_p 参数
- `max_tokens` (int, optional): 最大生成 token 数
- `stream_callback` (Callable, optional): 流式回调函数，每个 token 触发一次

**返回：**
```python
{
    "content": "完整生成文本",
    "usage": {
        "prompt_tokens": 1200,
        "completion_tokens": 800,
        "total_tokens": 2000
    },
    "performance": {
        "ttf_ms": 450.0,
        "tps": 45.2,
        "api_latency_ms": 320.0,
        "cost_usd": 0.0624
    }
}
```

### 成本计算

使用 Moonshot 官方定价：

- **kimi-k2.5**: 输入 12 元/百万 token，输出 60 元/百万 token

**公式：**
```
cost_usd = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
```

**示例：**
```
输入: 1200 tokens, 输出: 800 tokens
输入成本: 1200 * 12 / 1_000_000 = 0.0144 元
输出成本: 800 * 60 / 1_000_000 = 0.048 元
总成本: 0.0624 元 ≈ 0.0094 USD (按汇率 7.2)
```

### 重试逻辑

- 最多重试 3 次
- 指数退避：1s, 2s, 4s
- 处理错误码：429 (速率限制), 500+ (服务端错误)

### 流式解析

SSE 格式解析：
```
data: {"choices": [{"delta": {"content": "你"}}]}
data: {"choices": [{"delta": {"content": "好"}}]}
data: {"choices": [{"delta": {"content": "！"}}]}
data: [DONE]
```

### 配置 (config.yaml)

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

pricing:
  kimi-k2.5:
    input_per_million: 12
    output_per_million: 60
```

## director_general

总导演 LLM 节点，生成作品的全局规划和设定。

### 初始化

```python
from llm_nodes import director_general
from schemas import DirectorGeneralInput

input_data = DirectorGeneralInput(
    theme="AI觉醒与人类共存",
    style="赛博朋克悬疑",
    total_words=100000,
    character_count=5,
    genre="novel"
)
result = director_general(input_data)
```

### 参数 (DirectorGeneralInput)

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| theme | str | 是 | 小说主题 |
| style | str | 是 | 写作风格 |
| total_words | int | 是 | 目标总字数 |
| character_count | int | 是 | 角色数量 |
| genre | str | 是 | 文体类型 |

### 返回值 (DirectorGeneralOutput)

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

### Genre 类型处理

| genre | 处理指令 |
|-------|----------|
| novel | 强调章节结构和角色弧光 |
| script | 强调场景镜头和对白格式 |
| game_story | 强调分支选择和状态机 |
| dialogue | 强调多轮对话和记忆累积 |
| article | 强调论点论据结构 |

### 性能指标

返回值包含 `_metadata.performance`：
- `ttf_ms`: 首次响应时间（毫秒）
- `tps`: tokens per second
- `api_latency_ms`: API 延迟（毫秒）
- `cost_usd`: 预估成本（美元）

### 持久化

结果自动保存到 `output/global_memory.json`

### 示例输出

```json
{
  "world_building": {
    "setting": "近未来都市",
    "time_period": "2049年",
    "location": "新上海",
    "social_structure": "AI公民权社会",
    "rules": {"ai_personhood": true}
  },
  "outline": [
    {"chapter_id": 1, "title": "觉醒", "summary": "...", "key_events": [...], "characters_involved": [...]}
  ],
  "characters": [
    {"name": "林深", "role": "主角", "background": "...", "personality": "内向", "goals": "寻找真相", "relationships": {}}
  ],
  "tone": "悬疑暗黑",
  "genre_specific": {"genre": "novel", "specific_fields": {"novel_type": "社会派推理"}}
}
```

### 装饰器

- `@json_output`: 自动解析 JSON
- `@validate_schema`: 自动验证输出 schema

### 依赖

- `LlmClient`: 从 config.yaml 读取配置
- `decorators`: json_output, validate_schema
- `schemas`: DirectorGeneralInput, DirectorGeneralOutput

## memory_summarizer

记忆摘要器 LLM 节点，将原始记忆片段压缩为结构化的记忆卡片。

### 初始化

```python
from llm_nodes import memory_summarizer
from schemas import RawMemory

raw_memories = [
    RawMemory(
        character="林深",
        content="发现陈默公寓里的照片有裁剪痕迹",
        emotion="警觉压抑"
    ),
    RawMemory(
        character="陈默",
        content="右手挡住抽屉方向，眼神闪躲",
        emotion="防御紧张"
    )
]
cards = memory_summarizer(raw_memories)
```

### 参数

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| raw_memories | List[RawMemory] | 是 | 原始记忆列表 |

### RawMemory 结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| character | str | 涉及的角色 |
| content | 记忆内容 | 记忆的具体描述 |
| emotion | str | 当前情感状态 |

### 返回值

返回 `List[MemoryCard]`，每个卡片包含：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| event_id | str | 事件ID，格式如 "E-5-1" |
| timestamp | str | 时间戳描述 |
| location | str | 发生地点 |
| core_action | str | 核心动作/发现 |
| emotion_marks | Dict[str, str] | 情感标记 |
| relationship_changes | Dict[str, str] | 关系变化 |
| key_quote | str | 关键引言 |
| future_impacts | List[str] | 未来影响事件ID |
| source_index | str | 来源索引 |

### 示例输出

```json
[
  {
    "event_id": "E-5-1",
    "timestamp": "案发后第3天雨夜",
    "location": "陈默公寓",
    "core_action": "林深发现照片裁剪痕迹",
    "emotion_marks": {"林深": "警觉压抑", "陈默": "防御紧张"},
    "relationship_changes": {"林深→陈默": "信任-15"},
    "key_quote": "这雨下得跟那天一样",
    "future_impacts": ["E-8-2对峙", "E-12-1真相揭露"],
    "source_index": "章5/节点2/1200字"
  }
]
```

### 轻量模型

- 使用 `kimi-k2-0905-preview` 轻量模型
- 温度 0.3（更确定性输出）
- 定价：输入 1 元/百万，输出 5 元/百万

### 性能指标

返回值包含性能数据：
- `ttf_ms`: 首次响应时间
- `tps`: tokens per second
- `api_latency_ms`: API 延迟
- `cost_usd`: 预估成本

### 装饰器

- `@json_output`: 自动解析 JSON（无 @validate_schema，输出较灵活）

### 触发方式

由 `ChapterContext.exit` 调用（预留接口，T4 中 TODO）

### 依赖

- `LlmClient`: 使用轻量模型
- `decorators`: json_output
- `schemas`: RawMemory, MemoryCard

## ChapterContext

章节上下文管理器，用于管理单章执行期间的状态和资源。

### 初始化

```python
from context_managers import ChapterContext

with ChapterContext(chapter_id=1) as ctx:
    config = ctx["config"]
    global_mem = ctx["global"]
    chapter_mem = ctx["chapter"]
```

### 参数

- `chapter_id` (int): 章节编号
- `config_path` (str, optional): 配置文件路径，默认 "config.yaml"
- `memory_path` (str, optional): 全局记忆文件路径，默认 "global_memory.json"

### 上下文对象

`yield` 返回的字典包含：

- `config` (dict): 加载的配置信息
- `global` (dict): 全局记忆（characters, events, recent_detailed）
- `chapter` (dict): 章节记忆（空字典 {"characters": {}, "events": []}）
- `chapter_dir` (str): 章节临时目录路径

### 生命周期

#### enter (进入时)
1. 加载 config.yaml
2. 加载 global_memory.json（若不存在则创建默认结构）
3. 初始化 chapter_memory（空字典）
4. 创建 chapter_{n}/ 临时目录

#### exit (退出时)
1. 调用 memory_summarizer（TODO - T7 实现）
2. 摘要追加到 global_mem["recent_detailed"]
3. 保存更新后的 global_memory.json
4. 清理 chapter_{n}/ 临时目录

### 异常处理

- 使用 try/finally 确保 exit 始终执行清理
- 即使发生异常，也会保存记忆和清理临时文件

### 示例

```python
with ChapterContext(chapter_id=3) as ctx:
    # 读取配置
    print(ctx["config"]["api"]["model"])
    
    # 访问全局记忆
    characters = ctx["global"]["characters"]
    
    # 使用章节记忆
    ctx["chapter"]["events"].append({"type": "scene_change", "detail": "..."})
```

### TODO 标记

- **第 45-47 行**: memory_summarizer 调用预留接口，待 T7 实现

## NodeSequence

节点序列迭代器，用于管理章节内 LLM 节点的执行顺序和重试逻辑。

### 初始化

```python
from iterators import NodeSequence

node_sequence = ["node1", "node2", "node3"]
sequence = NodeSequence(node_sequence)
```

### 参数

- `node_sequence` (list): 节点名称列表

### 属性

- `current_index` (int): 当前迭代位置
- `retry_count` (int): 重试次数统计
- `node_sequence` (list): 存储的节点序列

### 方法

#### `__iter__()`

返回迭代器本身。

```python
for node in sequence:
    print(node)
```

#### `__next__()`

返回下一个节点，若越界则抛出 `StopIteration`。

#### `send(feedback)`

接收反馈并重置迭代器，用于节点执行失败需要重新执行整个序列的场景。

**参数：**
- `feedback` (any): 改进建议或反馈信息

**返回：**
- `"reset"`: 表示已重置迭代器

**示例：**

```python
sequence = NodeSequence(chapter_plan["node_sequence"])
for node in sequence:
    result = execute_node(node)
    check = self_check(result)
    if check["needs_revision"]:
        sequence.send(check["improvement_suggestions"])
        # 重置后重新迭代当前章节所有节点
```

### 使用场景

与 ChapterContext 配合使用：

```python
with ChapterContext(5) as ctx:
    sequence = NodeSequence(chapter_plan["node_sequence"])
    for node in sequence:
        result = execute_node(node)
        # ... 验证逻辑
        if needs_revision:
            sequence.send(feedback)
```


## role_assigner

角色分配器 LLM 节点，负责为当前节点生成角色扮演提示。

### 初始化

```python
from llm_nodes import role_assigner
from schemas import RoleAssignerInput, CurrentNodeInfo, CharacterProfileData, AssembledMemoryData, RelationshipMatrixData, ItemStatusData

input_data = RoleAssignerInput(
    current_node=CurrentNodeInfo(
        node_id="n-001",
        type="dialogue",
        description="林深试探陈默",
        target_character="林深"
    ),
    character_profile=CharacterProfileData(
        name="林深",
        role="侦探",
        background="28岁，专业侦探",
        personality="冷静理性，观察入微",
        goals="获取信任，寻找证据",
        relationships={"陈默": "表面朋友，实际怀疑"}
    ),
    assembled_memory=AssembledMemoryData(
        long_term=["第3章被救", "第4章发现打火机"],
        short_term=["本章试探陈默"],
        recent_events="你刚说完'这雨下得跟那天一样'"
    ),
    relationship_matrix=RelationshipMatrixData(
        relationships={"陈默": "信任45↓，表面朋友实际怀疑"}
    ),
    item_status=ItemStatusData(
        items=["父亲的怀表"],
        item_details={"父亲的怀表": "父亲遗物，一直随身携带"}
    ),
    genre="novel",
    current_situation="陈默正在倒茶，右手挡在抽屉方向",
    goals="获取信任假象，寻找证据",
    constraints=["禁止直接质问", "禁止表现出审问姿态"]
)

result = role_assigner(input_data)
```

### 装饰器

- `@json_output`: 自动解析 JSON 输出
- `@validate_schema(schema_class=RoleAssignerOutput)`: 自动验证输出格式

### 输入参数

**RoleAssignerInput:**
- `current_node` (CurrentNodeInfo): 当前节点信息
  - `node_id`: 节点ID
  - `type`: 节点类型
  - `description`: 节点描述
  - `target_character`: 目标角色
- `character_profile` (CharacterProfileData): 角色档案
  - `name`: 姓名
  - `role`: 角色
  - `background`: 背景
  - `personality`: 性格
  - `goals`: 目标
  - `relationships`: 关系字典
- `assembled_memory` (AssembledMemoryData): 组装后的记忆
  - `long_term`: 长期记忆列表
  - `short_term`: 短期记忆列表
  - `recent_events`: 最近事件描述
- `relationship_matrix` (RelationshipMatrixData): 关系矩阵
  - `relationships`: 关系字典
- `item_status` (ItemStatusData): 物品状态
  - `items`: 物品列表
  - `item_details`: 物品详情字典
- `genre` (str): 文体类型 (novel/script/game_story/dialogue/article)
- `current_situation` (str): 当前情境描述
- `goals` (str): 角色目标
- `constraints` (list): 行为约束列表

### 输出 (RoleAssignerOutput)

```json
{
    "target_character": "林深",
    "generation_prompt": {
        "identity": "你是林深，28岁侦探...",
        "long_term_memory": ["第3章被救", "第4章发现打火机"],
        "short_term_memory": ["本章试探陈默"],
        "recent_events": "你刚说完'这雨下得跟那天一样'",
        "current_situation": "陈默正在倒茶，右手挡在抽屉方向",
        "relationships": {"陈默": "信任45↓，表面朋友实际怀疑"},
        "items": ["父亲的怀表"],
        "goals": "获取信任假象，寻找证据",
        "constraints": ["禁止直接质问", "禁止表现出审问姿态"],
        "genre_hints": "novel：第三人称有限视角，心理描写丰富"
    }
}
```

### Genre 处理

根据不同文体类型调整 prompt 风格提示：

- **novel**: 第三人称有限视角，心理描写丰富，注重角色内心变化
- **script**: 场景镜头和对白格式，动作指示清晰，每场戏有明确目的
- **game_story**: 分支选择和状态机影响，预留触发条件，考虑玩家体验
- **dialogue**: 多轮对话和记忆累积，对话体现关系演变，关键节点清晰
- **article**: 论点论据结构，中心论点明确，逻辑递进清晰

### 依赖

- LlmClient 单例
- @json_output 装饰器
- @validate_schema 装饰器
- RoleAssignerInput / RoleAssignerOutput 模型（schemas.py）

## role_actor

角色扮演器 LLM 节点，负责根据角色分配器的提示生成角色扮演内容。

### 初始化

```python
from llm_nodes import role_actor
from schemas import RoleAssignerOutput, PromptComponents

generation_prompt = PromptComponents(
    identity="你是林深，28岁侦探...",
    long_term_memory=["第3章被救", "第4章发现打火机"],
    short_term_memory=["本章试探陈默"],
    recent_events="你刚说完'这雨下得跟那天一样'",
    current_situation="陈默正在倒茶，右手挡在抽屉方向",
    relationships={"陈默": "信任45↓，表面朋友实际怀疑"},
    items=["父亲的怀表"],
    goals="获取信任假象，寻找证据",
    constraints=["禁止直接质问", "禁止表现出审问姿态"],
    genre_hints="novel：第三人称有限视角，心理描写丰富"
)

role_assigner_output = RoleAssignerOutput(
    target_character="林深",
    generation_prompt=generation_prompt
)

def stream_callback(token):
    """流式回调：实时推送 token 到 UI"""
    print(token, end="")

def update_memory_callback(memory_update):
    """记忆更新回调：自动更新章节记忆"""
    print(f"Memory update: {memory_update}")

result = role_actor(
    role_assigner_output=role_assigner_output,
    chapter_id=5,
    node_id="n-002",
    stream_callback=stream_callback,
    update_memory_callback=update_memory_callback
)
```

### 装饰器

- `@json_output`: 自动解析 JSON 输出
- `@validate_schema(schema_class=RoleActorOutput)`: 自动验证输出格式

### 输入参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| role_assigner_output | RoleAssignerOutput | 是 | 角色分配器输出，包含 generation_prompt |
| chapter_id | int | 是 | 当前章节 ID |
| node_id | str | 是 | 当前节点 ID |
| stream_callback | Callable | 否 | 流式回调函数，用于推送 token 到 UI |
| update_memory_callback | Callable | 否 | 记忆更新回调函数 |

### generation_prompt 结构 (PromptComponents)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| identity | str | 角色身份设定 |
| long_term_memory | List[str] | 长期记忆列表 |
| short_term_memory | List[str] | 短期记忆（本章）列表 |
| recent_events | str | 最新事件描述 |
| current_situation | str | 当前状况描述 |
| relationships | Dict[str, str] | 人物关系字典 |
| items | List[str] | 携带物品列表 |
| goals | str | 当前目标 |
| constraints | List[str] | 行为约束列表 |
| genre_hints | str | 文体提示 |

### 输出 (RoleActorOutput)

```python
{
    "generated_content": "林深端起茶杯，目光不经意地扫过陈默身后的抽屉...",
    "state_change_report": {
        "new_memories": ["试探陈默，发现其防御姿态"],
        "emotion_shift": "从警觉压抑到确认怀疑",
        "new_discoveries": ["照片裁剪痕迹", "陈默右手挡抽屉"],
        "relationship_updates": {
            "陈默": {"trust": -15, "status": "表面朋友实际怀疑"}
        }
    }
}
```

### state_change_report 结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| new_memories | List[str] | 新产生的记忆片段列表 |
| emotion_shift | str | 情感变化描述 |
| new_discoveries | List[str] | 新发现/新线索列表 |
| relationship_updates | Dict[str, Dict] | 关系变化，格式：{"角色名": {"trust": 数值, "status": "关系描述"}} |

### 流式回调集成

`stream_callback(token)` 函数在每个 token 生成时被调用，用于实时推送内容到 UI：

```python
def stream_callback(token):
    # 方式1：直接打印
    print(token, end="")
    
    # 方式2：WebSocket 广播
    ws.send(json.dumps({"type": "token", "content": token}))
    
    # 方式3：累积到缓冲区
    accumulated_content += token
```

### 验证失败处理

- 输出长度 < 50 字：自动重试该节点（最多 3 次）
- 重试时通过 `stream_callback` 推送重试提示：`[重试 1/3]`
- 3 次重试后仍失败：返回截断内容（50字）+ 警告日志

### 后处理

1. **自动记忆更新**：调用 `update_memory_callback` 更新章节记忆库
2. **性能指标收集**：从 KimiApiClient 返回结果中提取性能数据

### 性能指标

返回值包含 `_metadata.performance`：
- `ttf_ms`: 首次响应时间（毫秒）
- `tps`: tokens per second
- `api_latency_ms`: API 延迟（毫秒）
- `cost_usd`: 预估成本（美元）

### 依赖

- LlmClient 单例
- @json_output 装饰器
- @validate_schema 装饰器
- RoleAssignerOutput / RoleActorOutput 模型（schemas.py）
- PromptComponents 模型（schemas.py）

## memory_retriever

记忆检索器，纯 Python 实现（无 LLM 调用），从全局记忆中检索相关内容。

### 初始化

```python
from memory_store import memory_retriever, RetrievalMetrics
```

### 函数签名

```python
def memory_retriever(
    character: str,
    current_scene: Dict[str, Any],
    global_memory: Dict[str, Any],
    config: Dict[str, Any],
    metrics: Optional[RetrievalMetrics] = None
) -> Dict[str, Any]
```

### 参数

- `character` (str): 当前角色名称
- `current_scene` (dict): 当前场景信息，包含 `description` 和 `other_characters`
- `global_memory` (dict): 全局记忆，包含 `recent_detailed` 列表
- `config` (dict): 配置信息，需包含 `memory.recent_chapters` 和 `memory.truncation`
- `metrics` (RetrievalMetrics, optional): 性能指标收集对象

### 返回

```python
{
    "character": "张三",
    "current_scene": {...},
    "retrieved_memories": [...],  # 记忆卡片列表
    "memory_count": 3,
    "total_chars": 1500,
    "retrieval_time_ms": 12.5,
    "config_used": {
        "recent_chapters": 3,
        "truncation_limit": 2000
    }
}
```

### 检索算法

1. **取最近章节**: 从 `global_memory["recent_detailed"]` 取最近 `config.memory.recent_chapters` 章（默认 3）
2. **标签匹配**: 提取场景描述关键词，匹配记忆的 `emotion_marks`
3. **关系过滤**: 涉及场景中其他角色的记忆优先
4. **去重**: 按 `event_id` 去重
5. **截断**: 硬截断到 `config.memory.truncation`（默认 2000 字符）

### 辅助函数

#### `extract_keywords(text: str) -> List[str]`

简单分词，提取名词和动词（至少2个字符）。

```python
keywords = extract_keywords("主角在城墙上眺望远方")
# 返回: ["主角", "城墙", "眺望", "远方"]
```

#### `deduplicate(cards: List[Dict]) -> List[Dict]`

按 `event_id` 去重。

```python
unique = deduplicate(cards)
```

#### `truncate(cards: List[Dict], max_chars: int) -> List[Dict]`

按字符数截断，保留完整卡片。

```python
truncated = truncate(cards, max_chars=2000)
```

### 验证函数

#### `validate_token_overflow(context: Dict, max_tokens: int = 8000) -> bool`

检查检索结果是否超过 token 限制。

```python
if validate_token_overflow(context):
    raise Exception("Token overflow detected")
```

### 性能指标

`RetrievalMetrics` 收集：

- `retrieval_time_ms`: 检索耗时（毫秒）
- `cache_hit_rate`: 缓存命中率（当前版本返回 0.0）
- `cards_retrieved`: 检索到的卡片数
- `chars_returned`: 返回的总字符数

### 配置示例 (config.yaml)

```yaml
memory:
  truncation: 2000
  recent_chapters: 3
```

### 示例

```python
config = {"memory": {"truncation": 2000, "recent_chapters": 3}}
global_memory = {"recent_detailed": [...]}
current_scene = {
    "description": "主角在城墙上与敌军对峙",
    "other_characters": ["李四", "王五"]
}

context = memory_retriever("张三", current_scene, global_memory, config)
print(f"检索到 {context['memory_count']} 条记忆，耗时 {context['retrieval_time_ms']:.2f}ms")
```

### 依赖

- 无外部依赖（纯 Python 实现）
- 被 llm_nodes.py (MEMORY_RETRIEVER 节点) 依赖

## Observability

运行时追踪、日志、性能收集、WebSocket 广播模块。

### 初始化

```python
from observability import get_observability

obs = get_observability()
```

### 工具函数（推荐直接使用）

```python
from observability import log_event, start_span, end_span, broadcast, get_performance_summary
```

### 方法

#### `log_event(level, chapter, node, message)`

写入日志事件。

**参数：**
- `level` (str): 日志等级，DEBUG/INFO/WARNING/ERROR
- `chapter` (int): 章节编号
- `node` (str): 节点标识
- `message` (str): 日志消息

**输出：**
- logs/novel_{timestamp}.log（人类可读）
- WebSocket 广播

---

#### `start_span(chapter, node)` (上下文管理器)

开始一个追踪 span。

**参数：**
- `chapter` (int): 章节编号
- `node` (str): 节点标识

**返回：**
- 上下文管理器，yield span_id (str): span 唯一标识

**用法：**
```python
with observability.start_span(chapter, node) as span_id:
    # 执行节点逻辑
    pass
```

**输出：**
- logs/trace_{timestamp}.jsonl（结构化追踪）

---

#### `end_span(span_id, usage, performance)`

结束 span 并收集性能指标。

**参数：**
- `span_id` (str): start_span 返回的 span_id
- `usage` (dict): token 使用情况 `{prompt_tokens, completion_tokens, total_tokens}`
- `performance` (dict): 性能数据 `{ttf_ms, tps, duration_ms, api_latency_ms, retry_count}`

**输出：**
- 追踪文件
- 性能汇总（自动更新每节点/每章/总指标）

---

#### `broadcast(type, data)`

WebSocket 广播消息。

**参数：**
- `type` (str): 消息类型，log/progress/performance
- `data` (Any): 消息数据

---

#### `get_performance_summary() -> dict`

获取性能汇总数据。

**返回：**
```python
{
    "per_node": [
        {
            "node_id": "N-1",
            "chapter": 1,
            "model": "kimi-k2.5",
            "prompt_tokens": 1200,
            "completion_tokens": 800,
            "total_tokens": 2000,
            "ttf_ms": 450,
            "tps": 45.2,
            "duration_ms": 5000,
            "api_latency_ms": 320,
            "retry_count": 0,
            "cost_usd": 0.0624
        }
    ],
    "per_chapter": [
        {
            "chapter_id": 1,
            "total_nodes": 5,
            "total_duration_ms": 25000,
            "total_tokens": 10000,
            "avg_tps": 40.0,
            "total_retries": 1,
            "total_cost_usd": 0.312
        }
    ],
    "summary": {
        "total_chapters": 5,
        "total_duration_min": 2.5,
        "total_tokens": 50000,
        "total_cost_usd": 1.56,
        "avg_chapter_time_min": 0.5
    }
}
```

---

#### `register_ws(ws_connection)`

注册 WebSocket 连接用于广播。

---

#### `set_progress(current, total, current_node)`

广播进度更新。

**参数：**
- `current` (int): 当前进度
- `total` (int): 总数
- `current_node` (str): 当前节点

### 日志格式

```
[2026-04-09T05:25:00.123456] [INFO] [C5/N-3] Node started, span_id=a1b2c3d4
```

### 追踪文件格式 (JSONL)

```json
{"trace_id": "novel_20260409_052500", "chapter": 5, "node": "N-3", "event": "enter", "timestamp": "2026-04-09T05:25:00.123456", "span_id": "a1b2c3d4"}
{"trace_id": "novel_20260409_052500", "chapter": 5, "node": "N-3", "event": "exit", "duration_ms": 4500, "output_hash": "a1b2c3", "cost_usd": 0.0624, "prompt_tokens": 1200, "completion_tokens": 800, "timestamp": "2026-04-09T05:25:05.623456"}
```

### WebSocket 广播格式

```python
{"type": "log", "data": {"timestamp": "...", "level": "INFO", "chapter": 5, "node": "N-3", "message": "..."}}
{"type": "progress", "data": {"current": 3, "total": 10, "percentage": 30.0, "current_node": "N-3"}}
{"type": "performance", "data": {...}  # 同 get_performance_summary()}
```

### 成本计算公式

```python
cost_usd = (prompt_tokens * input_price_per_million + completion_tokens * output_price_per_million) / 1_000_000
```

**Moonshot 定价 (config.yaml):**
- kimi-k2.5: 输入 12 元/百万 token，输出 60 元/百万 token

**示例：**
```
输入: 1200 tokens, 输出: 800 tokens
成本 = (1200 * 12 + 800 * 60) / 1_000_000 = 0.0624 元 ≈ 0.0087 USD
```

### 依赖

- yaml: 读取 config.yaml 配置
- json: 结构化输出
- threading: 线程安全单例

### 日志等级

| 等级 | 用途 |
|------|------|
| DEBUG | API 原始 IO（请求/响应） |
| INFO | 节点进出、正常流程 |
| WARNING | 重试、截断、警告 |
| ERROR | 异常、失败 |
