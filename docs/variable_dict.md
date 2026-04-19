# 变量字典

本文档详细说明 Novel AI Generator 中使用的所有变量、字段及其含义。

---

## 目录

- [输入输出变量](#输入输出变量)
- [配置变量](#配置变量)
- [性能指标变量](#性能指标变量)
- [记忆系统变量](#记忆系统变量)
- [状态变量](#状态变量)
- [元数据变量](#元数据变量)

---

## 输入输出变量

### DirectorGeneralInput

总导演节点输入参数。

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|------|------|--------|
| theme | str | 是 | 小说主题 | "AI觉醒与人类共存" |
| style | str | 是 | 写作风格 | "赛博朋克悬疑" |
| total_words | int | 是 | 目标总字数 | 100000 |
| character_count | int | 是 | 角色数量 | 5 |
| genre | str | 是 | 文体类型 | "novel" |

### DirectorGeneralOutput

总导演节点输出结果。

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
| _metadata | Dict | 元数据（性能指标、usage统计） |

### WorldBuilding

世界观设定对象。

| 字段名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| setting | str | 世界设定描述 | "近未来都市" |
| time_period | str | 时间背景 | "2049年" |
| location | str | 主要地点 | "新上海" |
| social_structure | str | 社会结构 | "AI公民权社会" |
| rules | Dict[str, Any] | 世界规则 | {"ai_personhood": true} |
| technology_level | str | 科技水平 | "高度发达" |
| magic_system | Optional[str] | 魔法/异能系统 | null |

### WritingStyle

写作风格对象。

| 字段名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| narrative_perspective | str | 叙事视角 | "第三人称有限视角" |
| narrative_voice | str | 叙事声音 | "冷静客观" |
| sentence_structure | str | 句式结构 | "长短句结合" |
| vocabulary_level | str | 词汇水平 | "中等偏上" |
| pacing | str | 节奏控制 | "张弛有度" |
| dialogue_style | str | 对话风格 | "自然口语化" |
| description_density | str | 描写密度 | "适度" |
| genre_conventions | List[str] | 文体惯例 | ["悬疑铺垫", "反转结局"] |

### ChapterOutline

章节大纲对象。

| 字段名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| chapter_id | int | 章节ID | 1 |
| title | str | 章节标题 | "觉醒" |
| summary | str | 章节摘要 | "主角发现AI异常..." |
| key_events | List[str] | 关键事件 | ["发现异常", "初次调查"] |
| characters_involved | List[str] | 涉及角色 | ["林深", "AI-7"] |
| estimated_words | int | 预估字数 | 5000 |
| emotional_arc | str | 情感弧线 | "疑惑→震惊→决心" |
| cliffhanger | Optional[str] | 悬念设置 | "AI-7突然开口说话" |

### CharacterProfile

角色档案对象。

| 字段名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| name | str | 角色名称 | "林深" |
| role | str | 角色定位 | "主角" |
| background | str | 背景故事 | "前AI工程师..." |
| personality | str | 性格特征 | "内向、理性、执着" |
| goals | str | 核心目标 | "寻找真相" |
| fears | str | 内心恐惧 | "被AI取代" |
| relationships | Dict[str, str] | 人物关系 | {"AI-7": "怀疑对象"} |
| character_arc | str | 角色弧光 | "从怀疑者到理解者" |
| distinctive_features | List[str] | 显著特征 | ["左手机械义肢"] |
| speech_patterns | str | 语言习惯 | "简洁直接，少用修辞" |

### DirectorChapterInput

章节导演节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| chapter_outline | ChapterOutline | 当前章节大纲 |
| world_building | WorldBuilding | 世界观设定 |
| characters | List[CharacterProfile] | 角色列表 |
| previous_chapter_summary | str | 前一章摘要 |
| chapter_id | int | 章节ID |

### DirectorChapterOutput

章节导演节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| scenes | List[Scene] | 场景列表 |
| scene_count | int | 场景数量 |
| estimated_words | int | 预估字数 |
| chapter_arc | str | 本章弧光描述 |

### Scene

场景对象。

| 字段名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| scene_id | str | 场景ID | "ch1_sc1" |
| setting | str | 场景设定 | "深夜的实验室" |
| time | str | 时间 | "凌晨2点" |
| characters_present | List[str] | 在场角色 | ["林深"] |
| plot_point | str | 情节点 | "发现异常数据" |
| emotional_tone | str | 情感基调 | "紧张、神秘" |
| narrative_unit_type | str | 叙事单元类型 | "action" |
| estimated_words | int | 预估字数 | 800 |

### RoleAssignerInput

角色分配节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| scene | Scene | 当前场景 |
| characters | List[CharacterProfile] | 可用角色列表 |
| chapter_memory | List[str] | 本章记忆 |
| global_memory | GlobalMemory | 全局记忆 |

### RoleAssignerOutput

角色分配节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| target_character | str | 目标角色名称 |
| generation_prompt | PromptComponents | 生成提示词组件 |
| scene_context | str | 场景上下文 |

### PromptComponents

提示词组件。

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

### RoleActorInput

角色扮演节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| generation_prompt | PromptComponents | 生成提示词组件 |
| chapter_id | int | 当前章节ID |
| node_id | str | 当前节点ID |
| node_type | str | 节点类型 |
| target_character | str | 目标角色 |
| genre | str | 文体类型 |
| stream_callback | Callable | 流式回调（可选） |

### RoleActorOutput

角色扮演节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| generated_content | str | 生成的内容 |
| state_change_report | StateChangeReport | 状态变更报告 |
| unit_type | str | 单元类型 |

### StateChangeReport

状态变更报告。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| new_memories | List[str] | 新产生的记忆片段列表 |
| emotion_shift | str | 情感变化描述 |
| new_discoveries | List[str] | 新发现/新线索列表 |
| relationship_updates | Dict[str, Dict] | 关系变化 |
| inventory_changes | List[str] | 物品变化 |

### MemorySummarizerInput

记忆总结节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| raw_memories | List[RawMemory] | 原始记忆列表 |
| max_cards | int | 最大卡片数 |

### RawMemory

原始记忆。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| character | str | 涉及的角色名称 |
| content | str | 记忆的具体内容 |
| emotion | str | 当前情感状态 |
| timestamp | str | 时间戳 |
| importance | float | 重要性评分 |

### MemorySummarizerOutput

记忆总结节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| summary_cards | List[MemoryCard] | 记忆卡片列表 |

### MemoryCard

记忆卡片。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| event_id | str | 事件唯一标识 |
| timestamp | str | 时间描述 |
| location | str | 发生地点 |
| core_action | str | 核心动作/发现 |
| emotion_marks | Dict[str, str] | 各角色情感标记 |
| relationship_changes | Dict[str, str] | 关系变化 |
| key_quote | str | 关键引言 |
| future_impacts | List[str] | 未来影响事件 |
| source_index | str | 来源索引 |

### SelfCheckInput

自检节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| content | str | 待检查内容 |
| check_type | str | 检查类型 |
| reference_material | Dict | 参考材料 |

### SelfCheckOutput

自检节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| passed | bool | 是否通过 |
| issues | List[str] | 问题列表 |
| suggestions | List[str] | 建议列表 |
| score | float | 质量评分 |

### TextPolisherInput

文本润色节点输入。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| content | str | 待润色内容 |
| polish_type | str | 润色类型 |
| style_hints | str | 风格提示 |

### TextPolisherOutput

文本润色节点输出。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| polished_content | str | 润色后的内容 |
| changes | List[str] | 修改列表 |

---

## 配置变量

### config.yaml 完整配置项

| 变量路径 | 类型 | 默认值 | 描述 |
|----------|------|--------|------|
| api.provider | str | "moonshot" | API 提供商 |
| api.base_url | str | "https://api.moonshot.cn/v1" | API 基础URL |
| api.api_key | str | - | API 密钥（支持环境变量 ${API_KEY}） |
| api.model | str | "kimi-k2.5" | 默认模型 |
| api.timeout | int | 60 | 超时秒数 |
| api.max_retries | int | 3 | 最大重试次数 |
| generation.temperature | float | 0.7 | 生成温度 |
| generation.top_p | float | 0.9 | top_p 参数 |
| generation.max_tokens | int | 4096 | 最大 token 数 |
| memory.truncation | int | 8000 | 记忆截断阈值 |
| memory.vector_dim | int | 1024 | 向量维度 |
| memory.use_rag | bool | true | 是否使用RAG |
| storage.base_path | str | "./output" | 存储基础路径 |
| observability.enabled | bool | true | 是否启用观测 |
| observability.log_dir | str | "./logs" | 日志目录 |
| pricing.kimi-k2.5.input_per_million | int | 12 | 输入价格（元/百万token） |
| pricing.kimi-k2.5.output_per_million | int | 60 | 输出价格（元/百万token） |

---

## 性能指标变量

### LLMResponse Performance

| 变量名 | 类型 | 描述 | 单位 |
|--------|------|------|------|
| ttf_ms | float | 首次响应时间（Time To First Token） | 毫秒 |
| tps | float | 每秒生成 token 数（Tokens Per Second） | tokens/s |
| api_latency_ms | float | API 总延迟 | 毫秒 |
| cost_usd | float | 预估成本 | 美元 |

### Usage Statistics

| 变量名 | 类型 | 描述 |
|--------|------|------|
| prompt_tokens | int | 输入 token 数 |
| completion_tokens | int | 输出 token 数 |
| total_tokens | int | 总 token 数 |

### 元数据变量 (_metadata)

所有 LLM 节点输出都包含 `_metadata` 字段：

| 变量名 | 类型 | 描述 |
|--------|------|------|
| _metadata.performance | Dict | 性能指标 |
| _metadata.usage | Dict | Token 使用统计 |
| _metadata.node_id | str | 节点ID |
| _metadata.timestamp | str | 执行时间戳 |
| _metadata.duration_ms | float | 执行耗时 |

---

## 记忆系统变量

### GlobalMemory

全局记忆存储。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| world_building | WorldBuilding | 世界观设定 |
| characters | List[CharacterProfile] | 角色档案 |
| outline | List[ChapterOutline] | 章节大纲 |
| writing_style | WritingStyle | 写作风格 |
| conflict_design | ConflictDesign | 冲突设计 |
| foreshadowing | List[HookDesign] | 伏笔设计 |

### ChapterMemory

章节级记忆。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| chapter_id | int | 章节ID |
| summary | str | 章节摘要 |
| scenes | List[Scene] | 场景列表 |
| memory_cards | List[MemoryCard] | 记忆卡片 |
| generated_content | List[GeneratedUnit] | 生成内容单元 |

### MemoryEntry

记忆条目（RAG存储）。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| id | str | 唯一标识 |
| content | str | 记忆内容 |
| embedding | List[float] | 向量嵌入 |
| metadata | Dict | 元数据 |
| timestamp | str | 时间戳 |
| importance | float | 重要性评分 |

---

## 状态变量

### GenerationState

生成状态。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| state_id | str | 状态ID |
| chapter_id | int | 当前章节ID |
| scene_id | str | 当前场景ID |
| node_id | str | 当前节点ID |
| status | str | 状态（idle/running/paused/completed/error） |
| progress | float | 进度百分比 |
| current_task | str | 当前任务描述 |
| error_message | Optional[str] | 错误信息 |

### Snapshot

快照对象。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| snapshot_id | str | 快照ID |
| timestamp | str | 创建时间 |
| state | GenerationState | 生成状态 |
| global_memory | GlobalMemory | 全局记忆 |
| chapter_memories | Dict[int, ChapterMemory] | 章节记忆 |
| metadata | Dict | 元数据 |

---

## 元数据变量

### WebSocket Message

WebSocket 消息格式。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| type | str | 消息类型（token/state/error/complete） |
| data | Dict | 消息数据 |
| timestamp | str | 时间戳 |

### TokenMessage

Token 流消息。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| type | str | "token" |
| data.token | str | 生成的token |
| data.node_id | str | 节点ID |
| data.character | str | 角色名称 |

### StateMessage

状态更新消息。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| type | str | "state" |
| data.status | str | 状态 |
| data.progress | float | 进度 |
| data.current_task | str | 当前任务 |

### ErrorMessage

错误消息。

| 变量名 | 类型 | 描述 |
|--------|------|------|
| type | str | "error" |
| data.error | str | 错误信息 |
| data.node_id | Optional[str] | 出错节点 |

---

## 变量命名规范

### 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `DirectorGeneralInput` |
| 变量名 | snake_case | `chapter_id`, `total_words` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有变量 | _前缀 | `_metadata`, `_cache` |
| 布尔变量 | is_/has_/use_ 前缀 | `is_enabled`, `use_rag` |

### 类型注解

```python
# 基础类型
chapter_id: int
theme: str
is_active: bool
score: float

# 容器类型
characters: List[str]
metadata: Dict[str, Any]
outline: List[ChapterOutline]

# 可选类型
cliffhanger: Optional[str]
callback: Optional[Callable[[str], None]]

# Union 类型
result: Union[str, None]
```

---

## 变量速查表

### 按模块分类

#### API 层变量

| 变量名 | 类型 | 位置 | 用途 |
|--------|------|------|------|
| container | Container | dependencies.py | 依赖注入容器 |
| llm_client | LLMClient | dependencies.py | LLM 客户端 |
| generator | NovelGenerator | dependencies.py | 生成器服务 |

#### 服务层变量

| 变量名 | 类型 | 位置 | 用途 |
|--------|------|------|------|
| state_manager | StateManager | novel_generator.py | 状态管理 |
| snapshot_manager | SnapshotManager | novel_generator.py | 快照管理 |
| memory_store | MemoryStore | novel_generator.py | 记忆存储 |

#### 核心层变量

| 变量名 | 类型 | 位置 | 用途 |
|--------|------|------|------|
| _llm_client | LLMClient | nodes/*.py | LLM 客户端（私有） |
| _config | ConfigProvider | nodes/*.py | 配置（私有） |
| _observability | ObservabilityBackend | nodes/*.py | 观测（私有） |

---

*文档版本：2.0.0 | 最后更新：2026-04-19*
