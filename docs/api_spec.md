# API 规范文档

> 本文档描述 Novel AI Generator 的 HTTP API 和 WebSocket 接口规范
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [概述](#概述)
2. [HTTP API](#http-api)
3. [WebSocket API](#websocket-api)
4. [数据模型](#数据模型)
5. [错误处理](#错误处理)
6. [示例代码](#示例代码)

---

## 概述

### 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **编码**: UTF-8

### 认证

当前版本暂不需要认证，后续版本将添加 API Key 认证。

---

## HTTP API

### 生成管理

#### 启动生成任务

```http
POST /api/start
```

启动新的小说生成任务。

**请求体**:

```json
{
  "book_id": "default",
  "chapter_id": 1,
  "theme": "校园青春恋爱",
  "style": "轻松",
  "characters": ["阳光少年", "转学生女主"],
  "total_words": 10000,
  "character_count": 2,
  "genre": "novel"
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| book_id | string | 否 | 书籍ID，默认 "default" |
| chapter_id | integer | 否 | 起始章节，默认 1 |
| theme | string | 是 | 小说主题 |
| style | string | 是 | 写作风格 |
| characters | string[] | 否 | 角色描述列表 |
| total_words | integer | 是 | 目标总字数 |
| character_count | integer | 是 | 角色数量 |
| genre | string | 是 | 文体类型 |

**响应**:

```json
{
  "status": "started",
  "book_id": "default",
  "chapter_id": 1
}
```

#### 查询生成状态

```http
GET /api/status
```

获取当前生成任务的详细状态。

**响应**:

```json
{
  "is_running": true,
  "is_paused": false,
  "is_stopped": false,
  "current_chapter": 1,
  "current_node": "role_actor_3",
  "total_chapters": 5,
  "progress": {
    "chapter_progress": 20,
    "overall_progress": 15
  },
  "error": null,
  "novel_content": "生成的内容预览..."
}
```

**字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| is_running | boolean | 是否正在运行 |
| is_paused | boolean | 是否已暂停 |
| is_stopped | boolean | 是否已停止 |
| current_chapter | integer | 当前章节ID |
| current_node | string | 当前节点ID |
| total_chapters | integer | 总章节数 |
| progress | object | 进度信息 |
| error | string | 错误信息 |
| novel_content | string | 当前生成内容 |

#### 暂停生成

```http
POST /api/pause
```

暂停当前生成任务。

**响应**:

```json
{
  "status": "paused"
}
```

#### 恢复生成

```http
POST /api/resume
```

恢复已暂停的生成任务。

**响应**:

```json
{
  "status": "resumed"
}
```

#### 停止生成

```http
POST /api/stop
```

停止当前生成任务。

**响应**:

```json
{
  "status": "stopped"
}
```

### 节点管理

#### 重新生成节点

```http
POST /api/regenerate
```

重新生成指定章节和节点的内容。

**请求体**:

```json
{
  "chapter_id": 1,
  "node_id": "role_actor_3"
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| chapter_id | integer | 是 | 章节ID，必须 >= 1 |
| node_id | string | 是 | 节点ID，非空 |

**响应**:

```json
{
  "status": "regenerating",
  "chapter_id": 1,
  "node_id": "role_actor_3"
}
```

**错误响应**:

| 状态码 | 描述 |
|--------|------|
| 400 | 无法再生指定节点（业务限制） |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

#### 重试节点

```http
POST /api/retry_node
```

重试当前失败的节点生成。

**响应**:

```json
{
  "status": "success",
  "message": "Retry attempt 1 initiated for node role_actor_3",
  "chapter_id": 1,
  "node_id": "role_actor_3",
  "retry_count": 1,
  "can_retry": true
}
```

### 版本管理

#### 获取版本列表

```http
GET /api/versions
```

获取当前章节的所有版本。

**响应**:

```json
{
  "chapter_id": 1,
  "current_version": "v1.2",
  "versions": [
    {
      "version_id": "v1.0",
      "created_at": "2026-04-19T10:00:00Z",
      "description": "初始版本"
    },
    {
      "version_id": "v1.1",
      "created_at": "2026-04-19T10:05:00Z",
      "description": "修正角色对话"
    }
  ]
}
```

#### 选择版本

```http
POST /api/select_version
```

选择特定版本作为当前版本。

**请求体**:

```json
{
  "chapter_id": 1,
  "version_id": "v1.1"
}
```

**响应**:

```json
{
  "status": "success",
  "chapter_id": 1,
  "selected_version": "v1.1"
}
```

### 快照管理

#### 获取快照列表

```http
GET /api/snapshots
```

获取所有可用的状态快照。

**响应**:

```json
{
  "snapshots": [
    {
      "snapshot_id": "snap_001",
      "created_at": "2026-04-19T10:00:00Z",
      "chapter_id": 1,
      "node_id": "role_actor_5",
      "description": "自动保存"
    }
  ]
}
```

#### 恢复快照

```http
POST /api/snapshots/{snapshot_id}/restore
```

恢复到指定快照状态。

**响应**:

```json
{
  "status": "success",
  "snapshot_id": "snap_001",
  "restored_to": {
    "chapter_id": 1,
    "node_id": "role_actor_5"
  }
}
```

---

## WebSocket API

### 连接

```
ws://localhost:8000/api/stream
```

### 消息格式

所有消息使用 JSON 格式。

### 客户端消息

#### 订阅事件

```json
{
  "type": "subscribe",
  "events": ["token", "progress", "status", "complete"]
}
```

#### 发送干预指令

```json
{
  "type": "intervention",
  "action": "accept",
  "chapter_id": 1,
  "node_id": "role_actor_3"
}
```

### 服务端消息

#### Token 消息

流式生成的 token。

```json
{
  "type": "token",
  "data": {
    "content": "生成的文本片段",
    "chapter_id": 1,
    "node_id": "role_actor_3",
    "timestamp": "2026-04-19T10:00:00.123Z"
  }
}
```

#### 进度消息

生成进度更新。

```json
{
  "type": "progress",
  "data": {
    "chapter_id": 1,
    "node_id": "role_actor_3",
    "chapter_progress": 45,
    "overall_progress": 23,
    "current_node_type": "dialogue",
    "target_character": "主角A"
  }
}
```

#### 状态消息

生成状态变化。

```json
{
  "type": "status",
  "data": {
    "status": "running",
    "chapter_id": 1,
    "node_id": "role_actor_3",
    "timestamp": "2026-04-19T10:00:00Z"
  }
}
```

#### 审查消息

需要人工干预。

```json
{
  "type": "need_manual_review",
  "data": {
    "chapter_id": 1,
    "node_id": "role_actor_3",
    "content": "需要审查的内容",
    "issues": ["角色行为不一致", "时间线错误"],
    "suggestions": "建议修改为..."
  }
}
```

#### 完成消息

生成完成。

```json
{
  "type": "complete",
  "data": {
    "chapter_id": 1,
    "total_tokens": 5000,
    "cost_usd": 0.05,
    "duration_seconds": 120
  }
}
```

#### 错误消息

发生错误。

```json
{
  "type": "error",
  "data": {
    "error_code": "GENERATION_FAILED",
    "message": "生成失败: API 超时",
    "chapter_id": 1,
    "node_id": "role_actor_3"
  }
}
```

---

## 数据模型

### 输入模型

#### DirectorGeneralInput

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| theme | string | 是 | 小说主题 |
| style | string | 是 | 写作风格 |
| total_words | integer | 是 | 目标总字数 |
| character_count | integer | 是 | 角色数量 |
| genre | string | 是 | 文体类型 |

#### DirectorChapterInput

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| chapter_id | integer | 是 | 章节ID |
| director_general_output | object | 是 | 总导演输出 |
| global_memory_snapshot | object | 是 | 全局记忆快照 |
| genre | string | 是 | 文体类型 |

### 输出模型

#### DirectorGeneralOutput

| 字段 | 类型 | 描述 |
|------|------|------|
| world_building | object | 世界观设定 |
| writing_style | object | 写作风格 |
| outline | array | 章节大纲列表 |
| chapter_count | integer | 章节总数 |
| characters | array | 角色列表 |
| conflict_design | object | 冲突设计 |
| foreshadowing | array | 伏笔列表 |
| character_arcs | array | 角色弧光 |
| tone | string | 整体基调 |
| genre_specific | object | 文体特定配置 |

#### RoleActorOutput

| 字段 | 类型 | 描述 |
|------|------|------|
| generated_content | string | 生成的文本内容 |
| state_change_report | object | 状态变化报告 |

### 性能指标

#### PerformanceMetrics

| 字段 | 类型 | 描述 |
|------|------|------|
| ttf_ms | float | 首Token延迟（毫秒） |
| tps | float | 生成速度（tokens/秒） |
| api_latency_ms | float | API延迟（毫秒） |
| prompt_tokens | integer | 输入Token数 |
| completion_tokens | integer | 输出Token数 |
| total_tokens | integer | 总Token数 |
| cost_usd | float | 预估成本（美元） |

---

## 错误处理

### HTTP 错误码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "total_words",
        "message": "必须大于0"
      }
    ]
  }
}
```

### 错误代码

| 代码 | 描述 |
|------|------|
| VALIDATION_ERROR | 参数验证失败 |
| GENERATION_IN_PROGRESS | 生成任务已在运行 |
| NO_ACTIVE_GENERATION | 没有活动的生成任务 |
| NODE_NOT_FOUND | 节点不存在 |
| VERSION_NOT_FOUND | 版本不存在 |
| SNAPSHOT_NOT_FOUND | 快照不存在 |
| LLM_API_ERROR | LLM API 调用失败 |
| RATE_LIMIT_ERROR | 速率限制 |

---

## 示例代码

### Python 客户端

```python
import requests
import websocket
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/stream"

# 启动生成
def start_generation():
    response = requests.post(f"{BASE_URL}/api/start", json={
        "theme": "校园青春恋爱",
        "style": "轻松",
        "total_words": 10000,
        "character_count": 2,
        "genre": "novel"
    })
    return response.json()

# WebSocket 连接
def on_message(ws, message):
    data = json.loads(message)
    if data["type"] == "token":
        print(f"Token: {data['data']['content']}")
    elif data["type"] == "progress":
        print(f"Progress: {data['data']['overall_progress']}%")
    elif data["type"] == "complete":
        print("Generation complete!")
        ws.close()

ws = websocket.WebSocketApp(WS_URL, on_message=on_message)
ws.run_forever()
```

### JavaScript 客户端

```javascript
// 启动生成
async function startGeneration() {
  const response = await fetch('http://localhost:8000/api/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      theme: '校园青春恋爱',
      style: '轻松',
      total_words: 10000,
      character_count: 2,
      genre: 'novel'
    })
  });
  return await response.json();
}

// WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/api/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'token':
      console.log('Token:', data.data.content);
      break;
    case 'progress':
      console.log('Progress:', data.data.overall_progress + '%');
      break;
    case 'complete':
      console.log('Generation complete!');
      ws.close();
      break;
  }
};
```

### cURL 示例

```bash
# 启动生成
curl -X POST http://localhost:8000/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "校园青春恋爱",
    "style": "轻松",
    "total_words": 10000,
    "character_count": 2,
    "genre": "novel"
  }'

# 查询状态
curl http://localhost:8000/api/status

# 暂停生成
curl -X POST http://localhost:8000/api/pause

# 重新生成节点
curl -X POST http://localhost:8000/api/regenerate \
  -H "Content-Type: application/json" \
  -d '{"chapter_id": 1, "node_id": "role_actor_3"}'
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，添加快照管理、版本管理接口 |
| 1.1.0 | 2026-04-15 | 添加 WebSocket 流式接口 |
| 1.0.0 | 2026-04-01 | 初始版本 |
