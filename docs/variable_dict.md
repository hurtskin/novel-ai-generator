# 变量字典

## LLM 节点变量

### director_general

| 变量名 | 类型 | 描述 | 来源 |
|--------|------|------|------|
| input_data | DirectorGeneralInput | 输入参数 | 输入参数 |
| output_data | DirectorGeneralOutput | 全局规划输出 | 输出结果 |
| _metadata | dict | 元数据 | 附加信息 |

#### DirectorGeneralInput

| 字段名 | 类型 | 描述 |
|--------|------|------|
| theme | str | 小说主题 |
| style | str | 写作风格 |
| total_words | int | 目标总字数 |
| character_count | int | 角色数量 |
| genre | str | 文体类型 |

#### DirectorGeneralOutput

| 字段名 | 类型 | 描述 |
|--------|------|------|
| world_building | WorldBuilding | 世界观设定 |
| writing_style | WritingStyle | 写作风格 |
| outline | List[ChapterOutline] | 章节大纲 |
| chapter_count | int | 章节总数 |
| characters | List[CharacterProfile] | 角色列表 |
| conflict_design | ConflictDesign | 冲突设计 |
| foreshadowing | List[HookDesign] | 伏笔列表 |
| character_arcs | List[ArcDesign] | 角色弧光 |
| tone | str | 整体基调 |
| genre_specific | GenreSpecific | 文体特定配置 |

### memory_summarizer

| 变量名 | 类型 | 描述 | 来源 |
|--------|------|------|------|
| raw_memories | List[RawMemory] | 原始记忆列表 | 输入参数 |
| summary_cards | List[MemoryCard] | 压缩后的记忆卡片 | 输出结果 |

### RawMemory

| 字段名 | 类型 | 描述 |
|--------|------|------|
| character | str | 涉及的角色名称 |
| content | str | 记忆的具体内容 |
| emotion | str | 当前情感状态 |

### MemoryCard

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

## 配置变量

### config.yaml

| 变量路径 | 类型 | 默认值 | 描述 |
|----------|------|--------|------|
| api.model | str | "kimi-k2.5" | 默认模型 |
| api.timeout | int | 60 | 超时秒数 |
| api.max_retries | int | 3 | 最大重试次数 |
| generation.temperature | float | 0.7 | 生成温度 |
| generation.top_p | float | 0.9 | top_p 参数 |
| generation.max_tokens | int | 4096 | 最大 token 数 |
| memory.truncation | int | 8000 | 记忆截断阈值 |
| pricing.kimi-k2-0905-preview.input_per_million | int | 1 | 轻量模型输入价格 |
| pricing.kimi-k2-0905-preview.output_per_million | int | 5 | 轻量模型输出价格 |

## 性能指标变量

| 变量名 | 类型 | 描述 | 单位 |
|--------|------|------|------|
| ttf_ms | float | 首次响应时间 | 毫秒 |
| tps | float | 每秒 token 数 | tokens/s |
| api_latency_ms | float | API 总延迟 | 毫秒 |
| prompt_tokens | int | 输入 token 数 | - |
| completion_tokens | int | 输出 token 数 | - |
| total_tokens | int | 总 token 数 | - |
| cost_usd | float | 预估成本 | 美元 |

### role_actor

| 变量名 | 类型 | 描述 | 来源 |
|--------|------|------|------|
| role_assigner_output | RoleAssignerOutput | 角色分配器输出（包含 generation_prompt） | 输入参数 |
| chapter_id | int | 当前章节 ID | 输入参数 |
| node_id | str | 当前节点 ID | 输入参数 |
| stream_callback | Callable, optional | 流式回调函数，用于推送 token 到 UI | 输入参数 |
| update_memory_callback | Callable, optional | 记忆更新回调函数 | 输入参数 |
| generated_content | str | 角色扮演生成的内容 | 输出结果 |
| state_change_report | Dict[str, Any] | 状态变更报告 | 输出结果 |

#### RoleAssignerOutput

| 字段名 | 类型 | 描述 |
|--------|------|------|
| target_character | str | 目标角色名称 |
| generation_prompt | PromptComponents | 生成提示词组件 |

#### PromptComponents

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

#### StateChangeReport

| 字段名 | 类型 | 描述 |
|--------|------|------|
| new_memories | List[str] | 新产生的记忆片段列表 |
| emotion_shift | str | 情感变化描述 |
| new_discoveries | List[str] | 新发现/新线索列表 |
| relationship_updates | Dict[str, Dict] | 关系变化（格式：{"角色名": {"trust": 数值, "status": "关系描述"}}） |
