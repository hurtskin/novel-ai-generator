# LLM 节点索引

本文档记录了系统中所有 LLM 节点的完整提示词内容、输入输出 Schema。

---

## 目录

1. [DirectorGeneral（总导演节点）](#1-directorgeneral总导演节点)
2. [DirectorChapter（章节导演节点）](#2-directorchapter章节导演节点)
3. [RoleAssigner（角色分配器节点）](#3-roleassigner角色分配器节点)
4. [RoleActor（角色演员节点）](#4-roleactor角色演员节点)
5. [MemorySummarizer（记忆总结器节点）](#5-memorysummarizer记忆总结器节点)
6. [SelfCheck（自我检查节点）](#6-selfcheck自我检查节点)

---

## 1. DirectorGeneral（总导演节点）

**文件位置**: `llm_nodes.py:449`

**功能**: 生成完整的作品大纲，包括世界观、角色列表、章节大纲、角色弧光等。

### 输入 Schema

```python
DirectorGeneralInput:
  - theme: str                    # 作品主题
  - style: str                    # 作品风格
  - total_words: int              # 目标总字数
  - character_count: int           # 角色数量
  - genre: str                    # 文体类型 (novel/script/game_story/dialogue/article)
  - user_theme: str               # 用户输入的主题
  - user_style: str               # 用户输入的风格
  - user_total_words: int         # 用户输入的总字数
  - user_character_count: int     # 用户输入的角色数
  - character_names: List[str]    # 固定的角色姓名列表
  - character_cards: List[CharacterCard]  # 所有角色的详细卡片信息
  - cache_config: Optional[CacheConfig]   # Context Caching 配置
  - cached_static_context: Optional[CachedContent]  # 已缓存的静态上下文
```

### 输出 Schema

```python
DirectorGeneralOutput:
  - world_building: str           # 世界观设定
  - writing_style: str            # 写作风格
  - outline: List[str]            # 章节大纲列表
  - chapter_count: int            # 章节数量
  - characters: List[str]         # 角色列表
  - character_names: List[str]    # 固定角色姓名
  - character_cards: List[CharacterCard]  # 角色卡片
  - conflict_design: str          # 冲突设计
  - foreshadowing: List[str]      # 伏笔列表
  - character_arcs: List[str]     # 角色弧光
  - tone: str                     # 作品基调
  - genre_specific: str           # 文体特定内容
```

### 系统提示词

```
你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。
```

### 用户提示词

```
作为小说总导演，请根据以下信息创作完整的作品大纲。

## 基本信息
- 主题: {input_data.theme}
- 风格: {input_data.style}
- 总字数: {input_data.total_words}
- 角色数: {input_data.character_count}
- 文体: {input_data.genre}

## 文体要求
{genre_hint}
- novel: 强调章节结构和角色弧光，注重心理描写和情节推进
- script: 强调场景镜头和对白格式，每个场景包含舞台指示
- game_story: 强调分支选择和状态机，考虑玩家决策影响
- dialogue: 强调多轮对话和记忆累积，对话要自然流畅
- article: 强调论点论据结构，逻辑清晰，论证有力

## 重要输出规则
1. 你必须输出真实的内容，禁止使用"描述"、"示例"、"..."等占位符
2. 每个JSON字段的值都必须是具体的、真实的描述
3. **重要**：character_names 必须列出所有角色的具体姓名，后续所有章节必须使用这些固定姓名
4. **重要**：character_cards 必须为每个角色生成详细的角色卡片，包含性格特点、说话风格、习惯、优点、缺点、恐惧、秘密等

## 输出格式
必须严格遵循 JSON Schema 输出，包含以下字段：
- world_building: 世界观描述
- writing_style: 写作风格
- outline: 章节大纲数组
- chapter_count: 章节数量
- characters: 角色描述数组
- character_names: 固定角色姓名数组
- character_cards: 角色卡片数组（每个包含 name, role, background, personality, goals, relationships, speaking_style, habits, strengths, weaknesses, fears, secrets）
- conflict_design: 冲突设计
- foreshadowing: 伏笔数组
- character_arcs: 角色弧光数组
- tone: 作品基调
- genre_specific: 文体特定内容

STRICT RULES:
1. 只输出JSON，不要输出任何其他内容
2. 不要输出markdown代码块标记
3. 直接输出纯JSON对象
```

---

## 2. DirectorChapter（章节导演节点）

**文件位置**: `llm_nodes.py:568`

**功能**: 根据总导演大纲生成特定章节的详细执行计划，包括节点序列、角色出场计划等。支持生成包含6种单元类型的节点序列。

### 输入 Schema

```python
DirectorChapterInput:
  - chapter_id: int                    # 章节 ID
  - director_general_output: Dict       # 总导演输出
  - global_memory_snapshot: Dict       # 全局记忆快照
  - genre: str                         # 文体类型
  - user_theme: str                    # 用户主题
  - user_style: str                   # 用户风格
  - user_total_words: int             # 用户总字数
  - user_character_count: int         # 用户角色数
  - character_names: List[str]       # 固定角色姓名
  - character_cards: List[CharacterCard]  # 角色卡片
  - feedback: str                      # 审查反馈（可选）
```

### 输出 Schema

```python
DirectorChapterOutput:
  - chapter_outline: ChapterOutlineRef  # 章节大纲
  - node_sequence: List[NodeConfig]    # 节点序列（必须包含所有6种单元类型）
    - node_id: str
    - type: str                        # 节点类型 (narrator/environment/action/dialogue/psychology/conflict)
    - priority: int
    - description: str
    - character: str
  - node_count: int                   # 节点数量
  - character_presence_plan: Dict      # 角色出场计划
  - genre_specific: GenreSpecific      # 文体特定
```

### 节点单元类型

本章的每个节点必须属于以下6种单元类型之一：

| 类型 | 名称 | 职责 |
|------|------|------|
| narrator | 旁白叙事 | 时间推进、背景交代、总结过渡、场景切换 |
| environment | 环境描写 | 空间场景、时间氛围、光线色彩、环境细节 |
| action | 动作描写 | 面部表情、肢体动作、手势细节 |
| dialogue | 角色对话 | 台词内容、说话方式、对话节奏 |
| psychology | 角色心理 | 内心独白、情绪波动、心理活动 |
| conflict | 冲突/悬念 | 矛盾冲突、悬念设置、危机升级 |

### 系统提示词

```
你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。
```

### 用户提示词

```
作为章节导演，请根据总导演大纲生成第 {chapter_id} 章的详细执行计划。

## 总大纲中的章节列表
{outline_list}

## 章节信息
- 章节ID: {chapter_id}
- 标题: {title}
- 摘要: {summary}
- 关键事件: {key_events}
- 涉及角色: {characters_involved}
- 固定角色姓名: {character_names}

## 角色卡片（每个角色的详细信息，后续节点必须严格遵循）
{character_cards}

## 文体要求
{genre_hint}

## 用户输入信息
- 主题: {user_theme}
- 风格: {user_style}
- 总字数: {user_total_words}
- 角色数: {user_character_count}

## 上一轮审查反馈（请根据此反馈调整内容）
{feedback}

## 重要规则
1. **必须使用固定角色姓名**：必须严格使用 character_names 中的姓名，禁止使用"主角1"、"主角2"等代称
2. **必须遵循角色卡片**：所有角色行为、对话必须符合角色卡片的性格设定
3. 必须输出真实的章节内容，禁止使用占位符

## 输出格式
必须严格遵循 JSON Schema 输出：
- chapter_outline: 章节大纲
- node_sequence: 节点序列数组
- node_count: 节点数量
- character_presence_plan: 角色出场计划
- genre_specific: 文体特定内容

STRICT RULES:
1. 只输出JSON，不要输出任何其他内容
2. 直接输出纯JSON对象
```

---

## 3. RoleAssigner（角色分配器节点）

**文件位置**: `llm_nodes.py:845`

**功能**: 根据当前节点信息和角色档案，生成适合该节点的角色扮演提示。支持6种单元类型（narrator/environment/action/dialogue/psychology/conflict），根据节点类型生成不同的 prompt 模板。

### 输入 Schema

```python
RoleAssignerInput:
  - current_node: CurrentNodeInfo      # 当前节点信息
    - node_id: str
    - type: str                       # 节点类型 (narrator/environment/action/dialogue/psychology/conflict)
    - description: str
    - target_character: Optional[str]
  - character_profile: CharacterProfileData  # 角色档案
  - assembled_memory: AssembledMemoryData  # 记忆信息
  - relationship_matrix: RelationshipMatrixData
  - item_status: ItemStatusData
  - genre: str                    # 文体类型
  - current_situation: str        # 当前情境
  - goals: str                    # 目标
  - constraints: List[str]        # 约束条件
  - user_theme: str               # 用户主题
  - user_style: str               # 用户风格
  - user_total_words: int         # 用户总字数
  - user_character_count: int     # 用户角色数
  - character_names: List[str]    # 固定角色姓名
  - character_cards: List[CharacterCard]  # 角色卡片
  - cache_config: Optional[CacheConfig]
  - cached_static_context: Optional[CachedContent]
  - feedback: str                 # 审查反馈（可选）
```

### 输出 Schema

```python
RoleAssignerOutput:
  - target_character: str         # 目标角色
  - generation_prompt: PromptComponents  # 生成提示
  - feedback: str                 # 审查反馈，传递给 RoleActor
```

### 系统提示词

```
你是角色分配器，负责为当前节点生成角色扮演提示。
根据角色档案、记忆、关系和物品状态，生成适合该节点的角色 generation_prompt。

你必须输出一个完整的 generation_prompt，包含所有必要信息让下一个节点能够准确扮演该角色。

STRICT RULES:
1. 只输出JSON，不要输出任何其他内容
2. 不要输出markdown代码块标记
3. 直接输出纯JSON对象
```

### 用户提示词

```
请根据以下信息生成角色 generation_prompt：

## 固定角色姓名列表（必须严格使用这些姓名，禁止使用其他姓名）
{character_names}

## 所有角色卡片（每个角色的详细信息，生成提示时必须严格遵循）
{character_cards}

## 当前节点信息
- 节点ID: {node_id}
- 节点类型: {type}
- 本节点场景描述: {description}
- 指定扮演角色: {target_character}

## 当前角色档案
- 姓名: {name}
- 角色: {role}
- 背景: {background}
- 性格特点: {personality}
- 目标: {goals}
- 与其他角色的关系: {relationships}

## 记忆信息
- 长期记忆: {long_term_memory}
- 短期记忆: {short_term_memory}
- 最近事件: {recent_events}

## 当前情境
{current_situation}

## 你需要做的事情
生成一个详细的角色扮演提示，让角色能够：
1. 知道自己的身份和性格
2. 知道当前正在发生什么事件
3. 知道应该如何反应（根据性格特点）
4. 知道与其他角色的关系

## 输出格式
生成 JSON 格式的 generation_prompt：
{
    "identity": "你是[姓名]，[详细身份描述]，你的性格是[性格特点]",
    "current_event": "当前场景中正在发生的事件: [详细描述]",
    "expected_reaction": "根据你的性格，你应该做出以下反应: [具体行为和对话]",
    "long_term_memory": ["长期记忆片段列表"],
    "short_term_memory": ["短期记忆片段列表"],
    "recent_events": "最近事件描述",
    "current_situation": "当前情境描述",
    "relationships": {"其他角色": "关系描述"},
    "items": ["当前持有的物品"],
    "goals": "当前目标",
    "constraints": ["行为约束列表"],
    "genre_hints": "文体特定提示"
}

**重要约束**：
1. identity 字段必须以"你是XXX"开头，明确角色姓名
2. current_event 必须详细描述当前场景正在发生的事
3. expected_reaction 必须根据角色性格描述角色会做什么、说什么
4. 所有内容必须严格使用固定角色姓名列表中的姓名
5. 禁止创造新角色，只能使用固定角色姓名列表中的角色
6. **必须遵循角色卡片**：所有行为和对话必须符合角色卡片的性格设定
```

---

## 4. RoleActor（角色演员节点）

**文件位置**: `llm_nodes.py:26`

**功能**: 根据角色分配器生成的提示，执行角色扮演，产出符合角色身份的正文内容。支持6种单元类型，根据节点类型调整输出内容。

### 输入 Schema

```python
输入参数:
  - role_assigner_output: RoleAssignerOutput  # 角色分配器输出
  - chapter_id: int                             # 当前章节 ID
  - node_id: str                               # 当前节点 ID
  - node_type: str                             # 节点类型 (narrator/environment/action/dialogue/psychology/conflict)
  - feedback: str                               # 审查反馈（可选）
  - stream_callback: Optional[Callable]        # 流式回调
  - update_memory_callback: Optional[Callable] # 记忆更新回调
  - user_theme: str                            # 用户主题
  - user_style: str                            # 用户风格
  - user_total_words: int                      # 用户总字数
  - user_character_count: int                 # 用户角色数
```

### 单元类型对应输出

| 节点类型 | 输出内容 | 示例 |
|---------|---------|------|
| narrator | 旁白叙述、时间推进 | "三天后，城里的局势变得更加紧张..." |
| environment | 环境描写、场景氛围 | "雨后的青石板路泛着湿润的光泽..." |
| action | 动作描写、表情肢体 | "他皱起眉头，右手不自觉地摩挲着..." |
| dialogue | 角色对话、台词内容 | "『我们真的没有别的选择了吗？』..." |
| psychology | 心理描写、内心独白 | "她心里涌起一股不安..." |
| conflict | 冲突悬念、紧张氛围 | "『站住别动！』一个低沉的声音..." |

### 输出 Schema

```python
RoleActorOutput:
  - generated_content: str                     # 生成的正文内容
  - state_change_report: StateChangeReport    # 状态变更报告
    - content: str                           # 正文（从JSON解析）
    - new_memories: List[str]                # 新记忆
    - emotion_shift: str                      # 情感变化
    - new_discoveries: List[str]             # 新发现
    - relationship_updates: Dict[str, str]   # 关系更新
```

### 系统提示词

```
{identity}

{current_event}

{expected_reaction}

重要：你是一个角色扮演AI。不要输出任何JSON、结构化数据或分析。只输出角色在当前情境下的自然对话和行动描述。
```

### 用户提示词

```
请根据以上设定，以指定角色的身份和视角进行角色扮演。
你需要产出符合角色身份的语言和行为，推动剧情发展，展现角色的情感变化。

## 输出格式（严格JSON）
你必须输出一个JSON对象，包含以下字段：
- content: 角色扮演的正文内容（小说情节、对白、动作描写等）
- new_memories: 字符串列表，记录新形成的记忆
- emotion_shift: 字符串，描述情感变化
- new_discoveries: 字符串列表，记录新发现的信息
- relationship_updates: 对象，键是角色名，值是关系描述字符串

示例格式：
{
  "content": "正文内容应该在这里，包含角色对话和行动描写...",
  "new_memories": ["在咖啡馆遇见新朋友", "聊了很多关于旅行的话题"],
  "emotion_shift": "感到开心和放松",
  "new_discoveries": ["发现对方也喜欢阅读"],
  "relationship_updates": {"角色B": "成为朋友"}
}

请开始角色扮演，输出JSON：

## 角色设定
{identity}

## 当前事件
{current_event}

## 预期反应
{expected_reaction}

## 背景记忆
{long_term_memory}

## 本章记忆
{short_term_memory}

## 场景设定
{current_situation}

## 场景目标
{goals}

## 注意事项
{constraints}

## 用户输入信息
- 主题: {user_theme}
- 风格: {user_style}
- 总字数: {user_total_words}
- 角色数: {user_character_count}
```

---

## 5. MemorySummarizer（记忆总结器节点）

**文件位置**: `llm_nodes.py:338`

**功能**: 将原始记忆片段压缩为结构化的记忆卡片。

### 输入 Schema

```python
输入参数:
  - raw_memories: List[RawMemory]
    - character: str    # 角色
    - content: str     # 内容
    - emotion: str     # 情感
```

### 输出 Schema

```python
输出:
  - List[MemoryCard]
    - event_id: str           # 事件ID
    - timestamp: str          # 时间戳
    - location: str           # 发生地点
    - core_action: str        # 核心动作
    - emotion_marks: Dict     # 情感标记
    - relationship_changes: Dict  # 关系变化
    - key_quote: str          # 关键引言
    - future_impacts: List[str]  # 未来影响
    - source_index: str        # 来源索引
```

### 系统提示词

```
你是一个记忆压缩专家。你的任务是将原始记忆片段压缩为结构化的记忆卡片。
```

### 用户提示词

```
请将以下原始记忆片段压缩为结构化的记忆卡片。

## 原始记忆
--- 记忆 1 ---
{"character": "角色A", "content": "记忆内容1", "emotion": "情感1"}
--- 记忆 2 ---
{"character": "角色B", "content": "记忆内容2", "emotion": "情感2"}
...

## 输出要求
请生成 JSON 数组，每个卡片包含以下字段：
- event_id: 事件ID，格式如 E-章节-序号
- timestamp: 时间戳，描述性如"案发后第3天雨夜"
- location: 发生地点
- core_action: 核心动作/发现，简短描述
- emotion_marks: 情感标记，dict格式如{"角色名": "情感描述"}
- relationship_changes: 关系变化，dict格式如{"角色A→角色B": "变化描述"}
- key_quote: 关键引言/台词
- future_impacts: 未来影响，关联的事件ID列表
- source_index: 来源索引，格式如"章5/节点2/字数"

请仅返回JSON数组，不要包含其他文字。
```

---

## 6. SelfCheck（自我检查节点）

**文件位置**: `llm_nodes.py:723`

**功能**: 对比总导演标准与当前章节内容，检查一致性。

### 输入 Schema

```python
输入参数:
  - director_general_standards: Dict    # 总导演标准
  - current_chapter_content: str       # 当前章节内容
  - global_memory_consistency: Dict    # 全局记忆一致性要求
```

### 输出 Schema

```python
SelfCheckOutput:
  - needs_revision: bool               # 是否需要修改
  - issue_types: List[str]             # 问题类型列表
  - specific_issues: List[str]         # 具体问题列表
  - improvement_suggestions: str       # 改进建议
```

### 系统提示词

```
你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。
```

### 用户提示词

```
作为质量审查专家，请对比总导演标准与当前章节内容，检查一致性。

## 总导演标准
{standards_summary}

## 全局记忆一致性要求
{memory_summary}

## 当前章节内容
{current_chapter_content}

## 检查要点
1. 角色行为是否与角色设定一致，角色前后名称是否一致
2. 情节发展是否符合章节大纲
3. 角色关系变化是否与记忆一致
4. 情感转折是否合理

## 输出格式
请输出 JSON 格式的检查结果：
{
    "needs_revision": true/false,
    "issue_types": ["一致性", "记忆", "角色", "情节", "伏笔"] 中的一项或多项,
    "specific_issues": ["具体问题描述1", "具体问题描述2"],
    "improvement_suggestions": "改进建议，需要详细说明如何修复问题"
}

注意：只要内容长度足够且有意义，没有出现严重的错误，就返回 needs_revision: false
```

---

## 节点调用关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        作品生成流程                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐                                          │
│  │  DirectorGeneral     │ ◄─── DirectorGeneralInput               │
│  │  (总导演节点)          │ ───► DirectorGeneralOutput              │
│  │                      │     (大纲/角色/章节列表)                    │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  DirectorChapter     │ ◄─── DirectorChapterInput               │
│  │  (章节导演节点)        │ ───► DirectorChapterOutput             │
│  │                      │     (章节大纲/节点序列)                    │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐     ┌──────────────────────┐            │
│  │  RoleAssigner        │ ──► │  RoleActor           │            │
│  │  (角色分配器)         │     │  (角色演员)           │            │
│  │                      │     │                      │            │
│  │ 输入:                │     │ 输入:                │            │
│  │ - CurrentNodeInfo   │     │ - generation_prompt  │            │
│  │ - CharacterProfile │     │                      │            │
│  │ - AssembledMemory  │     │ 输出:                │            │
│  │ - RelationshipMatrix│    │ - generated_content  │            │
│  │ - ItemStatus       │     │ - state_change_report│            │
│  │                      │     │                      │            │
│  │ 输出:                │     │ 输出后:              │            │
│  │ - generation_prompt │     │ ▼ 更新记忆           │            │
│  └──────────┬───────────┘     └──────────┬───────────┘            │
│             │                             │                        │
│             │         ┌───────────────────┘                        │
│             │         │                                             │
│             ▼         ▼                                             │
│  ┌──────────────────────┐                                          │
│  │  MemorySummarizer    │ ◄─── List[RawMemory]                    │
│  │  (记忆总结器)         │ ───► List[MemoryCard]                   │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  SelfCheck          │ ◄─── 内容+标准+记忆                       │
│  │  (自我检查)          │ ───► SelfCheckOutput                      │
│  │                      │     (needs_revision/问题列表)            │
│  └──────────────────────┘                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Schema 对照表

| 节点名称 | 输入 Schema | 输出 Schema | 主要功能 |
|---------|------------|------------|---------|
| DirectorGeneral | DirectorGeneralInput | DirectorGeneralOutput | 生成作品大纲 |
| DirectorChapter | DirectorChapterInput | DirectorChapterOutput | 生成章节执行计划 |
| RoleAssigner | RoleAssignerInput | RoleAssignerOutput | 生成角色扮演提示 |
| RoleActor | RoleAssignerOutput | RoleActorOutput | 执行角色内容生成 |
| MemorySummarizer | List[RawMemory] | List[MemoryCard] | 压缩记忆为结构化卡片 |
| SelfCheck | 自定义 | SelfCheckOutput | 内容质量审查 |

---

## 节点参数详解

### 角色卡片 (CharacterCard)

```python
class CharacterCard(BaseModel):
    name: str                    # 角色姓名
    role: str                    # 角色身份
    background: str               # 背景故事
    personality: str              # 性格描述
    goals: str                   # 角色目标
    relationships: Dict[str, str]  # 与其他角色的关系
    speaking_style: str = ""     # 说话风格
    habits: List[str] = []       # 习惯动作
    strengths: List[str] = []     # 优点
    weaknesses: List[str] = []    # 缺点
    fears: List[str] = []        # 恐惧
    secrets: List[str] = []      # 秘密
```

### 文体类型 (genre)

| 类型 | 说明 | 特点 |
|------|------|------|
| novel | 小说 | 第三人称有限视角，心理描写丰富，注重角色内心变化 |
| script | 剧本 | 场景镜头和对白格式，动作指示清晰，每场戏有明确目的 |
| game_story | 游戏叙事 | 分支选择和状态机影响，预留触发条件，考虑玩家体验 |
| dialogue | 对话 | 多轮对话和记忆累积，对话体现关系演变，关键节点清晰 |
| article | 文章 | 论点论据结构，中心论点明确，逻辑递进清晰 |
