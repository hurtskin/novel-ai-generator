# Novel AI Generator

一个基于多智能体协作的小说生成系统，支持实时流式输出、滑动窗口审查和人工干预。

## 系统特性

- **多智能体架构**：总导演 → 章节导演 → 角色分配 → 角色扮演 → 自检 → 润色
- **6种单元类型**：旁白(narrator)、环境(environment)、动作(action)、对话(dialogue)、心理(psychology)、冲突(conflict)
- **滑动窗口审查**：动态审查机制，支持版本管理和人工干预
- **RAG 记忆检索**：基于向量相似度的历史内容检索
- **实时流式输出**：WebSocket 实时推送生成进度和 token
- **可观测性**：分布式追踪、性能指标、成本统计
- **Mock 模式**：支持离线开发和测试

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+ (前端)
- Rust (Tauri 桌面端)

### 安装依赖

```bash
# 后端依赖
pip install fastapi uvicorn pydantic requests pyyaml

# 前端依赖
cd novel_ai
npm install
```

### 配置

编辑 `config.yaml`：

```yaml
api:
  provider: moonshot  # 或 ollama
  model: moonshot-v1-128k
  api_key: your-api-key
  base_url: https://api.moonshot.cn/v1

generation:
  mock_mode: false  # 设为 true 启用模拟模式
  temperature: 1
  max_tokens: 8192
```

### 启动服务

```bash
# 启动后端
python main.py

# 启动前端（开发模式）
cd novel_ai
npm run dev

# 构建桌面应用
cd novel_ai
npm run tauri build
```

## 项目结构

```
.
├── main.py                 # FastAPI 主入口
├── llm_nodes.py           # LLM 节点实现
├── schemas.py             # Pydantic 数据模型
├── llm_client.py          # LLM 客户端
├── context_managers.py    # 章节上下文管理
├── iterators.py           # 节点和章节迭代器
├── memory_store.py        # 记忆检索
├── rag_memory.py          # RAG 向量存储
├── observability.py       # 运行时追踪
├── decorators.py          # JSON 和 Schema 装饰器
├── config.yaml            # 配置文件
├── skills/                # Skill 文档
│   ├── main.skill
│   ├── novel_architect.skill
│   ├── llm_nodes.skill
│   ├── schemas.skill
│   ├── rag_memory.skill
│   ├── observability.skill
│   ├── llm_client.skill
│   ├── iterators.skill
│   ├── decorators.skill
│   └── sliding_window_review.skill
├── docs/                  # 文档
│   ├── file_index.md
│   ├── api_spec.md
│   └── ...
└── novel_ai/              # Tauri + React 前端
    ├── src/
    └── src-tauri/
```

## API 端点

### HTTP 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/start` | POST | 启动小说生成 |
| `/api/status` | GET | 获取生成状态 |
| `/api/pause` | POST | 暂停生成 |
| `/api/resume` | POST | 恢复生成 |
| `/api/stop` | POST | 停止生成 |
| `/api/select_version` | POST | 选择版本（人工干预） |
| `/api/retry_node` | POST | 重试当前节点 |

### WebSocket 端点

| 端点 | 描述 |
|------|------|
| `/api/stream` | 实时流式通信 |

**消息类型**：
- `token`: 流式 token
- `progress`: 进度更新
- `status`: 状态变化
- `need_manual_review`: 需要人工干预
- `complete`: 生成完成

## 生成流程

```
用户输入 → main.py
    ↓
director_general (总导演规划)
    ↓
ChapterIterator (章节循环)
    ↓
director_chapter (章节导演)
    ↓
NodeSequence (节点循环)
    ↓
role_assigner → RAG search → role_actor
    ↓
self_check (滑动窗口审查)
    ↓
[通过] → 保存 → 下一节点
[失败] → 重试 / 人工干预
    ↓
text_polisher (章节润色)
    ↓
输出文件
```

## 核心模块

### main.py
FastAPI 主入口，管理生成状态、滑动窗口审查、人工干预和 WebSocket 通信。

### llm_nodes.py
实现 6 大 LLM 节点：
- `director_general`: 总导演规划
- `director_chapter`: 章节导演
- `role_assigner`: 角色分配
- `role_actor`: 角色扮演
- `self_check`: 自检/审查
- `text_polisher`: 文本润色

### schemas.py
Pydantic 数据模型定义，包括：
- DirectorGeneralInput/Output
- DirectorChapterInput/Output
- RoleAssignerInput/Output
- PromptComponents
- SelfCheckOutput

### rag_memory.py
RAG 记忆系统：
- `EmbeddingClient`: 文本向量化
- `VectorStore`: 本地向量存储
- `RagMemorySystem`: 内容摄入和检索

### observability.py
可观测性模块：
- 分布式追踪（start_span/end_span）
- 性能指标收集
- 日志记录
- WebSocket 广播
- 快照管理

## 配置说明

### API 配置
```yaml
api:
  provider: moonshot      # LLM 提供商
  model: moonshot-v1-128k # 模型名称
  api_key: your-key       # API 密钥
  base_url: ...           # API 基础 URL
  max_retries: 5          # 最大重试次数
  timeout: 180            # 超时时间（秒）
```

### 生成配置
```yaml
generation:
  mock_mode: false        # 模拟模式（无需 API）
  temperature: 1          # 温度参数
  max_tokens: 8192        # 最大生成 token 数
  debug: true             # 调试模式
```

### Embedding 配置
```yaml
embedding:
  base_url: ...           # Embedding API URL
  api_key: your-key       # API 密钥
  model: bge-m3           # 模型名称
  dimensions: 1024        # 向量维度
```

## 开发指南

### 添加新的 LLM 节点

1. 在 `schemas.py` 中定义输入/输出模型
2. 在 `llm_nodes.py` 中实现节点函数
3. 使用 `@json_output` 和 `@validate_schema` 装饰器
4. 在 `main.py` 中集成到生成流程

### 使用 Mock 模式

```yaml
# config.yaml
generation:
  mock_mode: true
```

Mock 模式下，所有 LLM 调用返回预定义的模拟数据，无需真实 API 密钥。

### 调试

```python
# 启用调试日志
config.yaml:
  generation:
    debug: true

# 查看日志
tail -f logs/debug.log
```

## 文档

- [文件索引](docs/file_index.md) - 完整文件说明
- [API 规范](docs/api_spec.md) - API 详细规范
- [Skill 文档](skills/) - 各模块详细文档
  - [主程序](skills/main.skill)
  - [系统架构](skills/novel_architect.skill)
  - [LLM 节点](skills/llm_nodes.skill)
  - [数据模型](skills/schemas.skill)
  - [RAG 记忆](skills/rag_memory.skill)
  - [可观测性](skills/observability.skill)

## 许可证

MIT License
