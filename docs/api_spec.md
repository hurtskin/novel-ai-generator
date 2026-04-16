# API 规范文档

## Pydantic 模型字段说明

### DirectorGeneralInput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| theme | str | 是 | 小说主题 |
| style | str | 是 | 写作风格 |
| total_words | int | 是 | 目标总字数 |
| character_count | int | 是 | 角色数量 |
| genre | str | 是 | 文体类型 |

### DirectorGeneralOutput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| world_building | WorldBuilding | 是 | 世界观设定 |
| writing_style | WritingStyle | 是 | 写作风格对象 |
| outline | List[ChapterOutline] | 是 | 章节大纲列表 |
| chapter_count | int | 是 | 章节总数 |
| characters | List[CharacterProfile] | 是 | 角色档案列表 |
| conflict_design | ConflictDesign | 是 | 冲突设计 |
| foreshadowing | List[HookDesign] | 是 | 伏笔设计列表 |
| character_arcs | List[ArcDesign] | 是 | 角色弧光列表 |
| tone | str | 是 | 整体基调 |
| genre_specific | GenreSpecific | 是 | 文体特定配置 |

### WorldBuilding

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| setting | str | 是 | 故事背景 |
| time_period | str | 是 | 时间段 |
| location | str | 是 | 地点 |
| social_structure | str | 是 | 社会结构 |
| rules | Dict[str, Any] | 是 | 规则设定 |

### WritingStyle

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tone | str | 是 | 语气 |
| perspective | str | 是 | 视角 |
| pacing | str | 是 | 节奏 |
| language_level | str | 是 | 语言层次 |

### ChapterOutline

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| chapter_id | int | 是 | 章节ID |
| title | str | 是 | 章节标题 |
| summary | str | 是 | 章节概要 |
| key_events | List[str] | 是 | 关键事件列表 |
| characters_involved | List[str] | 是 | 涉及角色列表 |

### CharacterProfile

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| name | str | 是 | 角色名 |
| role | str | 是 | 角色定位 |
| background | str | 是 | 角色背景 |
| personality | str | 是 | 性格特点 |
| goals | str | 是 | 角色目标 |
| relationships | Dict[str, str] | 是 | 关系映射 |

### ConflictDesign

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| main_conflict | str | 是 | 主要冲突 |
| sub_conflicts | List[str] | 是 | 次要冲突列表 |
| stakes | str | 是 |  stakes 风险 |

### HookDesign

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| hook_type | str | 是 | 钩子类型 |
| content | str | 是 | 钩子内容 |
| placement | str | 是 | 放置位置 |

### ArcDesign

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| character_name | str | 是 | 角色名 |
| starting_state | str | 是 | 起始状态 |
| turning_point | str | 是 | 转折点 |
| ending_state | str | 是 | 结束状态 |

### GenreSpecific

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| genre | str | 是 | 文体类型 |
| specific_fields | Dict[str, Any] | 是 | 文体特定字段 |

### DirectorChapterInput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| chapter_id | int | 是 | 章节ID |
| director_general_output | DirectorGeneralOutput | 是 | 总导演输出 |
| global_memory_snapshot | Dict[str, Any] | 是 | 全局记忆快照 |
| genre | str | 是 | 文体类型 |

### DirectorChapterOutput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| chapter_outline | ChapterOutlineRef | 是 | 章节大纲 |
| node_sequence | List[NodeConfig] | 是 | 节点序列 |
| node_count | int | 是 | 节点数量 |
| character_presence_plan | Dict[str, List[int]] | 是 | 角色出场计划 |
| genre_specific | GenreSpecific | 是 | 文体特定配置 |

### NodeConfig

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| node_id | str | 是 | 节点ID |
| type | str | 是 | 节点类型 |
| character | Optional[str] | 否 | 关联角色 |
| description | str | 是 | 节点描述 |

### MemoryCard

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| event_id | str | 是 | 事件ID |
| timestamp | str | 是 | 时间戳 |
| location | str | 是 | 地点 |
| core_action | str | 是 | 核心动作 |
| emotion_marks | Dict[str, str] | 是 | 情感标记 |
| relationship_changes | Dict[str, str] | 是 | 关系变化 |
| key_quote | str | 是 | 关键引语 |
| future_impacts | List[str] | 是 | 未来影响 |
| source_index | str | 是 | 源索引 |

### RoleAssignerOutput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| target_character | str | 是 | 目标角色 |
| generation_prompt | PromptComponents | 是 | 生成提示词 |

### PromptComponents

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| identity | str | 是 | 身份设定 |
| long_term_memory | List[str] | 是 | 长期记忆 |
| short_term_memory | List[str] | 是 | 短期记忆 |
| recent_events | str | 是 | 最近事件 |
| current_situation | str | 是 | 当前情况 |
| relationships | Dict[str, str] | 是 | 关系映射 |
| items | List[str] | 是 | 物品列表 |
| goals | str | 是 | 目标 |
| constraints | List[str] | 是 | 约束条件 |
| genre_hints | str | 是 | 文体提示 |

### RoleActorOutput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| generated_content | str | 是 | 生成内容 |
| state_change_report | StateChangeReport | 是 | 状态变化报告 |

### StateChangeReport

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| new_memories | List[str] | 是 | 新记忆列表 |
| emotion_shift | str | 是 | 情感变化 |
| new_discoveries | List[str] | 是 | 新发现列表 |
| relationship_updates | Dict[str, str] | 是 | 关系更新 |

### SelfCheckOutput

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| needs_revision | bool | 是 | 是否需要修改 |
| issue_types | List[str] | 是 | 问题类型列表 |
| specific_issues | List[str] | 是 | 具体问题列表 |
| improvement_suggestions | str | 是 | 改进建议 |

### PerformanceMetrics

| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| ttf_ms | float | 是 | 首Token延迟(ms) |
| tps | float | 是 | 生成速度(tokens/s) |
| api_latency_ms | float | 是 | API延迟(ms) |
| prompt_tokens | int | 是 | 输入Token数 |
| completion_tokens | int | 是 | 输出Token数 |
| total_tokens | int | 是 | 总Token数 |
| cost_usd | float | 是 | 预估成本(USD) |

## HTTP API 端点

### 启动生成任务
- **端点**: `POST /api/start`
- **描述**: 启动小说生成任务
- **请求体**:
```json
{
  "book_id": "string",
  "chapter_id": 1,
  "theme": "string",
  "style": "novel",
  "characters": ["角色1", "角色2"],
  "total_words": 10000,
  "character_count": 3,
  "genre": "novel"
}
```
- **参数说明**:
  - `book_id` (string, optional): 书籍ID，用于标识不同的生成任务，默认为 "default"
  - `chapter_id` (int, optional): 起始章节ID，默认为 1
  - `theme` (string, required): 小说主题，如 "校园青春恋爱"、"玄幻冒险" 等
  - `style` (string, required): 写作风格，如 "喜剧"、"正剧"、"轻松" 等
  - `characters` (string[], optional): 角色描述列表，如 ["阳光少年", "转学生女主"]
  - `total_words` (int, required): 目标总字数
  - `character_count` (int, required): 角色数量
  - `genre` (string, required): 文体类型，如 "novel"、"script"、"dialogue" 等
- **响应**:
```json
{"status": "started"}
```

### 查询状态
- **端点**: `GET /api/status`
- **描述**: 查询当前生成任务状态
- **响应**:
```json
{
  "is_running": false,
  "is_paused": false,
  "is_stopped": false,
  "current_chapter": 1,
  "current_node": "DIRECTOR_GENERAL",
  "total_chapters": 3,
  "error": null,
  "novel_content": "..."
}
```

### 暂停
- **端点**: `POST /api/pause`
- **响应**: `{"status": "paused"}`

### 继续
- **端点**: `POST /api/resume`
- **响应**: `{"status": "resumed"}`

### 终止
- **端点**: `POST /api/stop`
- **响应**: `{"status": "stopped"}`

### 重新生成节点
- **端点**: `POST /api/regenerate`
- **描述**: 指定章节和节点重新生成
- **请求体**:
```json
{
  "chapter_id": 1,
  "node_id": "node_1"
}
```
- **响应**:
```json
{"status": "regenerating", "chapter_id": 1, "node_id": "node_1"}
```

### 获取快照列表
- **端点**: `GET /api/snapshots`
- **响应**:
```json
{"snapshots": ["snapshot1", "snapshot2"]}
```

### 加载快照
- **端点**: `GET /api/snapshot/{name}`
- **描述**: 加载指定名称的状态快照
- **响应**:
```json
{
  "status": "success",
  "snapshot": {
    "timestamp": "2026-04-09T12:00:00",
    "generation_state": {...},
    "node_metrics": [...],
    "chapter_metrics": {...},
    "total_metrics": {...}
  }
}
```

### 保存快照
- **端点**: `POST /api/snapshot/{name}`
- **描述**: 保存当前状态为快照
- **响应**:
```json
{"status": "saved", "path": "logs/snapshots/name.json"}
```

### 性能指标
- **端点**: `GET /api/performance`
- **描述**: 获取性能指标汇总
- **响应**:
```json
{
  "per_node": [...],
  "per_chapter": [...],
  "summary": {
    "total_chapters": 3,
    "total_duration_min": 5.2,
    "total_tokens": 15000,
    "total_cost_usd": 0.85,
    "avg_chapter_time_min": 1.73
  }
}
```

### 配置信息
- **端点**: `GET /api/config`
- **描述**: 获取当前配置信息（动态从 config.yaml 读取）
- **响应**:
```json
{
  "api": {
    "model": "kimi-k2.5",
    "base_url": "https://api.moonshot.cn/v1",
    "timeout": 60,
    "max_retries": 3
  },
  "generation": {
    "temperature": 1,
    "top_p": 0.95,
    "max_tokens": 4096
  },
  "memory": {
    "truncation": 8000
  },
  "ui": {
    "theme": "dark",
    "font_size": 14
  },
  "performance": {
    "cost_alert_usd": 5
  }
}
```

### 保存配置
- **端点**: `POST /api/config`
- **描述**: 保存配置到 config.yaml 并重新加载（动态生效，无需重启）
- **请求体**:
```json
{
  "api": {
    "model": "kimi-k2"
  },
  "generation": {
    "temperature": 0.8
  }
}
```
- **响应**:
```json
{
  "status": "saved"
}
```

## WebSocket API

### 流式连接
- **端点**: `WS /api/stream`
- **描述**: 实时接收日志、进度、性能数据

### 消息类型

#### 日志消息
```json
{
  "type": "log",
  "data": {
    "timestamp": "2026-04-09T12:00:00",
    "level": "INFO",
    "chapter": 1,
    "node": "DIRECTOR_GENERAL",
    "message": "Node started"
  }
}
```

#### 进度消息
```json
{
  "type": "progress",
  "data": {
    "current": 1,
    "total": 3,
    "percentage": 33.3,
    "current_node": "CHAPTER_1",
    "estimated_remaining_cost": 0.5
  }
}
```

#### Token 消息
```json
{
  "type": "token",
  "data": {
    "chapter": 1,
    "node": "node_1",
    "token": "这是"
  }
}
```

#### 性能消息
```json
{
  "type": "performance",
  "data": {
    "per_node": [...],
    "per_chapter": [...],
    "summary": {...}
  }
}
```

#### Pong 响应
```json
{"type": "pong"}
```

#### 状态消息
```json
{
  "type": "status",
  "data": {
    "current_chapter": 1,
    "current_node": "DIRECTOR_GENERAL",
    "total_chapters": 3,
    "is_running": true,
    "is_paused": false,
    "is_stopped": false
  }
}
```

#### 完成消息
```json
{
  "type": "complete",
  "data": {
    "message": "Generation completed",
    "output_file": "E:\\dev-py\\novel\\output\\novel_20260409_220138.txt"
  }
}
```
