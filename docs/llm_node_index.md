# LLM 节点索引

> 本文档记录系统中所有 LLM 节点的完整信息，包括输入输出 Schema、提示词内容和使用说明
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [节点概览](#节点概览)
2. [DirectorGeneral（总导演节点）](#1-directorgeneral总导演节点)
3. [DirectorChapter（章节导演节点）](#2-directorchapter章节导演节点)
4. [RoleAssigner（角色分配器节点）](#3-roleassigner角色分配器节点)
5. [RoleActor（角色演员节点）](#4-roleactor角色演员节点)
6. [MemorySummarizer（记忆总结器节点）](#5-memorysummarizer记忆总结器节点)
7. [SelfCheck（自我检查节点）](#6-selfcheck自我检查节点)
8. [TextPolisher（文本润色节点）](#7-textpolisher文本润色节点)

---

## 节点概览

### 节点执行流程

```
DirectorGeneral (总导演)
    ↓
ChapterIterator (章节迭代器)
    ↓
DirectorChapter (章节导演)
    ↓
NodeSequence (节点序列迭代器)
    ↓
RoleAssigner → RAG Search → RoleActor
    ↓
SelfCheck (质量检查)
    ↓
[通过] → 保存 → 下一节点
[失败] → 重试 / 人工干预
    ↓
MemorySummarizer (记忆总结)
    ↓
ChapterIterator (下一章节)
    ↓
TextPolisher (章节润色) [章节完成时]
```

### 六种单元类型

| 类型 | 名称 | 职责 | 典型长度 |
|------|------|------|----------|
| narrator | 旁白叙事 | 时间推进、背景交代、总结过渡 | 300-500字 |
| environment | 环境描写 | 空间场景、时间氛围、光线色彩 | 200-400字 |
| action | 动作描写 | 面部表情、肢体动作、手势细节 | 150-300字 |
| dialogue | 角色对话 | 台词内容、说话方式、对话节奏 | 100-300字 |
| psychology | 角色心理 | 内心独白、情绪波动、心理活动 | 200-400字 |
| conflict | 冲突/悬念 | 矛盾冲突、悬念设置、危机升级 | 300-500字 |

---

## 1. DirectorGeneral（总导演节点）

**文件位置**: `core/nodes/director_general.py`

**功能**: 生成完整的作品大纲，包括世界观、角色列表、章节大纲、角色弧光等。

### 输入 Schema

```python
class DirectorGeneralInput(BaseModel):
    theme: str                      # 作品主题
    style: str                      # 作品风格
    total_words: int                # 目标总字数
    character_count: int            # 角色数量
    genre: str                      # 文体类型
    user_theme: str                 # 用户输入的主题
    user_style: str                 # 用户输入的风格
    user_total_words: int           # 用户输入的总字数
    user_character_count: int       # 用户输入的角色数
    character_names: List[str]      # 固定的角色姓名列表
    character_cards: List[CharacterCard]  # 所有角色的详细卡片信息
```

### 输出 Schema

```python
class DirectorGeneralOutput(BaseModel):
    world_building: WorldBuilding           # 世界观设定
    writing_style: WritingStyle             # 写作风格
    outline: List[ChapterOutline]           # 章节大纲列表
    chapter_count: int                      # 章节数量
    characters: List[CharacterProfile]      # 角色列表
    character_names: List[str]              # 固定角色姓名
    character_cards: List[CharacterCard]    # 角色卡片
    conflict_design: ConflictDesign         # 冲突设计
    foreshadowing: List[HookDesign]         # 伏笔列表
    character_arcs: List[ArcDesign]         # 角色弧光
    tone: str                               # 作品基调
    genre_specific: GenreSpecific           # 文体特定内容
```

### 系统提示词

```
你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。
禁止：解释、分析、markdown代码块、任何JSON之外的文字。
只输出纯JSON。
```

### 用户提示词模板

```
作为小说总导演，请根据以下信息创作完整的作品大纲。

## 基本信息
- 主题: {theme}
- 风格: {style}
- 总字数: {total_words}
- 角色数: {character_count}
- 文体: {genre}

## 文体要求
{genre_hint}

## 重要输出规则
1. 你必须输出真实的内容，禁止使用"描述"、"示例"、"..."等占位符
2. 每个JSON字段的值都必须是具体的、真实的描述
3. **重要**：character_names 必须列出所有角色的具体姓名
4. **重要**：character_cards 必须为每个角色生成详细的角色卡片

## 输出格式
必须严格遵循 JSON Schema 输出，包含以下字段：
- world_building: 世界观描述
- writing_style: 写作风格
- outline: 章节大纲数组
- chapter_count: 章节数量
- characters: 角色描述数组
- character_names: 固定角色姓名数组
- character_cards: 角色卡片数组
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

**文件位置**: `core/nodes/director_chapter.py`

**功能**: 根据总导演大纲生成特定章节的详细执行计划，包括节点序列、角色出场计划等。

### 输入 Schema

```python
class DirectorChapterInput(BaseModel):
    chapter_id: int                         # 章节 ID
    director_general_output: DirectorGeneralOutput  # 总导演输出
    global_memory_snapshot: Dict[str, Any]  # 全局记忆快照
    genre: str                              # 文体类型
    user_theme: str                         # 用户主题
    user_style: str                         # 用户风格
    user_total_words: int                   # 用户总字数
    user_character_count: int               # 用户角色数
    character_names: List[str]              # 固定角色姓名
    character_cards: List[CharacterCard]    # 角色卡片
    feedback: Optional[str]                 # 审查反馈
```

### 输出 Schema

```python
class DirectorChapterOutput(BaseModel):
    chapter_outline: ChapterOutlineRef      # 章节大纲
    node_sequence: List[NodeConfig]         # 节点序列
    node_count: int                         # 节点数量
    character_presence_plan: Dict[str, List[int]]  # 角色出场计划
    genre_specific: GenreSpecific           # 文体特定

class NodeConfig(BaseModel):
    node_id: str                            # 节点ID
    type: str                               # 节点类型 (narrator/environment/action/dialogue/psychology/conflict)
    priority: int                           # 优先级
    description: str                        # 节点描述
    character: Optional[str]                # 关联角色
```

### 系统提示词

```
你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。
禁止：解释、分析、markdown代码块、任何JSON之外的文字。
只输出纯JSON。
```

### 用户提示词模板

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

## 角色卡片（每个角色的详细信息）
{character_cards}

## 文体要求
{genre_hint}

## 用户输入信息
- 主题: {user_theme}
- 风格: {user_style}
- 总字数: {user_total_words}
- 角色数: {user_character_count}

## 上一轮审查反馈
{feedback}

## 重要规则
1. **必须使用固定角色姓名**：严格使用 character_names 中的姓名
2. **必须遵循角色卡片**：角色行为、对话必须符合角色设定
3. **必须包含6种单元类型**：narrator/environment/action/dialogue/psychology/conflict
4. 禁止使用占位符

## 输出格式
- chapter_outline: 章节大纲
- node_sequence: 节点序列数组（必须包含所有6种单元类型）
- node_count: 节点数量
- character_presence_plan: 角色出场计划
- genre_specific: 文体特定内容

STRICT RULES:
1. 只输出JSON
2. 直接输出纯JSON对象
```

---

## 3. RoleAssigner（角色分配器节点）

**文件位置**: `core/nodes/role_assigner.py`

**功能**: 根据当前节点信息和角色档案，生成适合该节点的角色扮演提示。

### 输入 Schema

```python
class RoleAssignerInput(BaseModel):
    current_node: CurrentNodeInfo                   # 当前节点信息
    character_profile: CharacterProfileData         # 角色档案
    assembled_memory: AssembledMemoryData           # 记忆信息
    relationship_matrix: RelationshipMatrixData     # 关系矩阵
    item_status: ItemStatusData                     # 物品状态
    genre: str                                      # 文体类型
    current_situation: str                          # 当前情境
    goals: str                                      # 目标
    constraints: List[str]                          # 约束条件
    user_theme: str                                 # 用户主题
    user_style: str                                 # 用户风格
    user_total_words: int                           # 用户总字数
    user_character_count: int                       # 用户角色数
    character_names: List[str]                      # 固定角色姓名
    character_cards: List[CharacterCard]            # 角色卡片
    feedback: Optional[str]                         # 审查反馈
```

### 输出 Schema

```python
class RoleAssignerOutput(BaseModel):
    target_character: str                           # 目标角色
    generation_prompt: PromptComponents             # 生成提示
    feedback: str                                   # 审查反馈

class PromptComponents(BaseModel):
    identity: str                                   # 身份设定
    long_term_memory: List[str]                     # 长期记忆
    short_term_memory: List[str]                    # 短期记忆
    recent_events: str                              # 最近事件
    current_situation: str                          # 当前情况
    relationships: Dict[str, str]                   # 关系映射
    items: List[str]                                # 物品列表
    goals: str                                      # 目标
    constraints: List[str]                          # 约束条件
    genre_hints: str                                # 文体提示
```

### 单元类型提示词映射

```python
UNIT_TYPE_PROMPTS = {
    "narrator": """
你正在创作旁白叙事单元。这个单元负责：
- 推进时间线
- 交代背景信息
- 总结过渡场景
- 切换不同场景
注意：保持客观叙述，不要加入角色主观感受。
""",
    "environment": """
你正在创作环境描写单元。这个单元负责：
- 描述空间场景
- 渲染时间氛围
- 刻画光线色彩
- 营造环境细节
注意：调动五感（视觉、听觉、嗅觉、触觉、味觉）。
""",
    "action": """
你正在创作动作描写单元。这个单元负责：
- 描写面部表情
- 刻画肢体动作
- 描述手势细节
- 展现场景动态
注意：动作要符合角色性格和当前情境。
""",
    "dialogue": """
你正在创作角色对话单元。这个单元负责：
- 撰写台词内容
- 设计说话方式
- 控制对话节奏
- 展现人物关系
注意：对话要自然，符合角色身份和性格。
""",
    "psychology": """
你正在创作角色心理单元。这个单元负责：
- 描写内心独白
- 刻画情绪波动
- 展现心理活动
- 揭示人物动机
注意：心理活动要细腻真实，有层次感。
""",
    "conflict": """
你正在创作冲突/悬念单元。这个单元负责：
- 设置矛盾冲突
- 营造悬念氛围
- 升级危机 tension
- 推动情节发展
注意：冲突要有张力，让读者产生阅读欲望。
"""
}
```

---

## 4. RoleActor（角色演员节点）

**文件位置**: `core/nodes/role_actor.py`

**功能**: 根据角色分配器生成的提示词，扮演指定角色生成具体文本内容。

### 输入 Schema

```python
class RoleActorInput(BaseModel):
    generation_prompt: PromptComponents     # 生成提示词组件
    chapter_id: int                         # 当前章节ID
    node_id: str                            # 当前节点ID
    node_type: str                          # 节点类型
    target_character: str                   # 目标角色
    genre: str                              # 文体类型
```

### 输出 Schema

```python
class RoleActorOutput(BaseModel):
    generated_content: str                  # 生成的文本内容
    state_change_report: StateChangeReport  # 状态变化报告

class StateChangeReport(BaseModel):
    new_memories: List[str]                 # 新记忆列表
    emotion_shift: str                      # 情感变化
    new_discoveries: List[str]              # 新发现列表
    relationship_updates: Dict[str, str]    # 关系更新
```

### 系统提示词

根据单元类型动态生成：

```python
UNIT_TYPE_INSTRUCTIONS = {
    "narrator": "你是旁白叙述者。用客观、流畅的语言叙述故事。",
    "environment": "你是环境描写专家。用细腻的笔触描绘场景氛围。",
    "action": "你是动作描写专家。用精准的语言刻画人物动作。",
    "dialogue": "你是{target_character}。用符合身份的语气说话。",
    "psychology": "你是心理描写专家。深入刻画{target_character}的内心世界。",
    "conflict": "你是冲突设计专家。创造紧张刺激的戏剧冲突。"
}
```

### 用户提示词模板

```
## 角色身份
{identity}

## 长期记忆
{long_term_memory}

## 短期记忆
{short_term_memory}

## 最近事件
{recent_events}

## 当前情况
{current_situation}

## 人物关系
{relationships}

## 携带物品
{items}

## 当前目标
{goals}

## 约束条件
{constraints}

## 文体提示
{genre_hints}

## 审查反馈
{feedback}

请根据以上信息，生成符合当前情境的内容。
输出格式必须是JSON：
{{
    "generated_content": "生成的文本内容",
    "state_change_report": {{
        "new_memories": ["新记忆1", "新记忆2"],
        "emotion_shift": "情感变化描述",
        "new_discoveries": ["新发现1"],
        "relationship_updates": {{"角色B": "关系变化"}}
    }}
}}
```

---

## 5. MemorySummarizer（记忆总结器节点）

**文件位置**: `core/nodes/memory_summarizer.py`

**功能**: 将原始记忆压缩成结构化的记忆卡片，便于后续检索和使用。

### 输入 Schema

```python
class MemorySummarizerInput(BaseModel):
    raw_memories: List[RawMemory]           # 原始记忆列表
    chapter_id: int                         # 章节ID

class RawMemory(BaseModel):
    character: str                          # 涉及角色
    content: str                            # 记忆内容
    emotion: str                            # 情感状态
    timestamp: str                          # 时间戳
```

### 输出 Schema

```python
class MemorySummarizerOutput(BaseModel):
    summary_cards: List[MemoryCard]         # 压缩后的记忆卡片

class MemoryCard(BaseModel):
    event_id: str                           # 事件唯一标识
    timestamp: str                          # 时间描述
    location: str                           # 发生地点
    core_action: str                        # 核心动作/发现
    emotion_marks: Dict[str, str]           # 各角色情感标记
    relationship_changes: Dict[str, str]    # 关系变化
    key_quote: str                          # 关键引言
    future_impacts: List[str]               # 未来影响事件
    source_index: str                       # 来源索引
```

### 提示词

```
请将以下原始记忆整理成结构化的记忆卡片。

原始记忆：
{raw_memories}

请提取关键信息，生成记忆卡片：
- event_id: 事件唯一标识
- timestamp: 时间描述
- location: 发生地点
- core_action: 核心动作
- emotion_marks: 各角色情感
- relationship_changes: 关系变化
- key_quote: 关键引言
- future_impacts: 未来影响
- source_index: 来源索引

输出JSON格式。
```

---

## 6. SelfCheck（自我检查节点）

**文件位置**: `core/nodes/self_check.py`

**功能**: 对生成的内容进行质量审查，检查一致性、连贯性、风格等问题。

### 输入 Schema

```python
class SelfCheckInput(BaseModel):
    content: str                            # 待检查内容
    chapter_id: int                         # 章节ID
    node_id: str                            # 节点ID
    node_type: str                          # 节点类型
    target_character: Optional[str]         # 目标角色
    previous_content: Optional[str]         # 前文内容
    character_profiles: Dict[str, Any]      # 角色档案
    genre: str                              # 文体类型
```

### 输出 Schema

```python
class SelfCheckOutput(BaseModel):
    needs_revision: bool                    # 是否需要修改
    issue_types: List[str]                  # 问题类型列表
    specific_issues: List[str]              # 具体问题列表
    improvement_suggestions: str            # 改进建议

class IssueType(str, Enum):
    CHARACTER_CONSISTENCY = "character_consistency"     # 角色一致性
    PLOT_CONTINUITY = "plot_continuity"                 # 情节连贯性
    STYLE_DEVIATION = "style_deviation"                 # 风格偏离
    LOGIC_ERROR = "logic_error"                         # 逻辑错误
    TIMELINE_ISSUE = "timeline_issue"                   # 时间线问题
    DIALOGUE_QUALITY = "dialogue_quality"               # 对话质量
    DESCRIPTION_VIVIDNESS = "description_vividness"     # 描写生动性
```

### 检查维度

| 维度 | 检查内容 |
|------|----------|
| 角色一致性 | 行为是否符合角色设定、性格是否前后一致 |
| 情节连贯性 | 与上文是否衔接、情节是否通顺 |
| 风格偏离 | 是否符合整体风格、文体是否统一 |
| 逻辑错误 | 时间线是否正确、因果关系是否合理 |
| 对话质量 | 对话是否自然、是否符合角色身份 |
| 描写生动性 | 描写是否细腻、是否有画面感 |

### 提示词

```
请对以下内容进行质量审查：

## 待检查内容
{content}

## 上下文信息
- 章节: {chapter_id}
- 节点: {node_id}
- 类型: {node_type}
- 角色: {target_character}

## 角色档案
{character_profiles}

## 前文内容
{previous_content}

请从以下维度进行检查：
1. 角色一致性
2. 情节连贯性
3. 风格偏离
4. 逻辑错误
5. 对话质量
6. 描写生动性

输出JSON格式：
{{
    "needs_revision": true/false,
    "issue_types": ["问题类型"],
    "specific_issues": ["具体问题描述"],
    "improvement_suggestions": "改进建议"
}}
```

---

## 7. TextPolisher（文本润色节点）

**文件位置**: `core/nodes/text_polisher.py`

**功能**: 对完整章节进行最终润色，提升文学性和可读性。

### 输入 Schema

```python
class TextPolisherInput(BaseModel):
    raw_chapter_content: str                # 原始章节内容
    chapter_id: int                         # 章节ID
    chapter_outline: ChapterOutlineRef      # 章节大纲
    writing_style: WritingStyle             # 写作风格
    genre: str                              # 文体类型
```

### 输出 Schema

```python
class TextPolisherOutput(BaseModel):
    polished_content: str                   # 润色后的内容
    changes_summary: List[str]              # 修改摘要
    quality_score: float                    # 质量评分 0-100
```

### 润色维度

| 维度 | 说明 |
|------|------|
| 语言流畅度 | 句子是否通顺、用词是否准确 |
| 文学性 | 修辞手法、语言美感 |
| 节奏感 | 段落节奏、阅读体验 |
| 一致性 | 人称、时态、风格统一 |
| 错别字检查 | 文字错误、标点符号 |

### 提示词

```
请对以下章节内容进行润色：

## 原始内容
{raw_chapter_content}

## 章节大纲
{chapter_outline}

## 写作风格
{writing_style}

## 润色要求
1. 提升语言流畅度
2. 增强文学性和画面感
3. 优化段落节奏
4. 确保人称时态一致
5. 修正错别字和标点

保持原有情节和角色设定不变，只优化表达方式。

输出JSON格式：
{{
    "polished_content": "润色后的完整内容",
    "changes_summary": ["修改点1", "修改点2"],
    "quality_score": 85.5
}}
```

---

## 节点配置参数

### 温度参数建议

| 节点 | 温度 | 说明 |
|------|------|------|
| DirectorGeneral | 0.8 | 需要创意但要有结构 |
| DirectorChapter | 0.7 | 平衡创意和一致性 |
| RoleAssigner | 0.6 | 需要准确的角色分析 |
| RoleActor | 0.9 | 需要创意生成 |
| SelfCheck | 0.3 | 需要严格准确的检查 |
| TextPolisher | 0.5 | 平衡保持原意和优化 |

### Max Tokens 配置

| 节点 | Max Tokens | 说明 |
|------|------------|------|
| DirectorGeneral | 8192 | 需要生成长文本 |
| DirectorChapter | 4096 | 中等长度 |
| RoleAssigner | 2048 | 提示词组件 |
| RoleActor | 4096 | 生成内容 |
| SelfCheck | 2048 | 检查报告 |
| TextPolisher | 8192 | 润色完整章节 |

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，节点模块化 |
| 1.2.0 | 2026-04-15 | 添加6种单元类型支持 |
| 1.1.0 | 2026-04-11 | 添加审查反馈循环 |
| 1.0.0 | 2026-04-01 | 初始版本 |
