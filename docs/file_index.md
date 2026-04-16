# 文件索引

## 后端核心模块

| 文件名 | 描述 | 关键类/函数 | 依赖 |
|--------|------|------------|------|
| main.py | FastAPI 主入口，核心生成循环，API 端点，状态管理 | generate_task(), generation_state, ChapterContext | 所有其他模块 |
| llm_nodes.py | LLM 节点实现（总导演/章节导演/角色分配/角色扮演/自检/润色） | director_general, director_chapter, role_assigner, role_actor, self_check, text_polisher | schemas, llm_client, decorators |
| schemas.py | Pydantic 数据模型定义 | DirectorGeneralInput/Output, RoleAssignerInput/Output, etc. | pydantic |
| llm_client.py | LLM 客户端单例（支持 Moonshot） | get_llm_client(), LlmClient | - |
| context_managers.py | 章节上下文管理器，全局记忆读写 | ChapterContext, load_config, load_global_memory, save_global_memory | yaml, json, shutil |
| iterators.py | 节点序列和章节迭代器 | NodeSequence, ChapterIterator | - |
| memory_store.py | 记忆检索器 | memory_retriever, update_memory, RetrievalMetrics | - |
| rag_memory.py | RAG 向量存储和检索 | add_chunks(), search(), index_chunks | numpy |
| observability.py | 运行时追踪、日志、性能收集、WebSocket广播、快照管理 | Observability, start_span(), get_observability | yaml, json, threading |
| decorators.py | JSON输出和Schema验证装饰器 | json_output, validate_schema | pydantic, json |

## 配置文件

| 文件名 | 描述 | 关键配置项 |
|--------|------|-----------|
| config.yaml | 用户配置文件 | api.provider, api.model, generation.temperature, generation.mock_mode |
| global_memory.json | 全局记忆存储 | 章节摘要列表 |
| vector_store/index.json | RAG 向量索引 | 文本块向量和元数据 |

## 前端模块 (novel_ai/)

| 路径 | 描述 | 技术栈 |
|------|------|--------|
| src/App.tsx | React 主应用组件 | React, TypeScript |
| src/api/client.ts | API 客户端和 WebSocket 连接 | axios, WebSocket |
| src/stores/appStore.ts | Zustand 全局状态管理 | Zustand |
| src/components/ChatPanel.tsx | 对话/生成内容面板 | React |
| src/components/DebugPanel.tsx | 调试信息面板 | React |
| src/components/InterventionPanel.tsx | 人工干预面板 | React |
| src/components/PerformancePanel.tsx | 性能监控面板 | React |
| src/components/ProgressPanel.tsx | 进度显示面板 | React |
| src/components/SettingsPanel.tsx | 设置面板 | React |
| src-tauri/ | Tauri Rust 后端 | Rust |
| src-tauri/tauri.conf.json | Tauri 窗口配置 | JSON |

## Skills 文档

| 文件名 | 描述 | 用途 |
|--------|------|------|
| skills/main.skill | 主程序文档 | 理解 FastAPI 服务和生成流程 |
| skills/novel_architect.skill | 系统架构规范 | 理解整体架构和模块关系 |
| skills/sliding_window_review.skill | 滑动窗口审查系统 | 理解节点审查机制 |
| skills/llm_nodes.skill | LLM 节点文档 | 理解 6 大生成节点和单元类型 |
| skills/observability.skill | 可观测性文档 | 理解追踪、指标和日志 |
| skills/rag_memory.skill | RAG 记忆文档 | 理解向量检索和记忆管理 |
| skills/schemas.skill | 数据模型文档 | 理解 Pydantic Schema 定义 |
| skills/decorators.skill | 装饰器工具文档 | 理解 JSON 解析和 Schema 验证 |
| skills/iterators.skill | 迭代器工具文档 | 理解 NodeSequence 和 ChapterIterator |
| skills/llm_client.skill | LLM 客户端文档 | 理解 API 调用和流式输出 |
| skills/sliding_window_review.md | 滑动窗口审查说明（旧版） | 历史文档 |

## Docs 文档

| 文件名 | 描述 |
|--------|------|
| docs/api_spec.md | API 规范 |
| docs/change_log.md | 变更日志 |
| docs/file_index.md | 本文件索引 |
| docs/llm_node_index.md | LLM 节点索引 |
| docs/rag_memory.md | RAG 记忆文档 |
| docs/tool_reference.md | 工具参考 |
| docs/variable_dict.md | 变量字典 |

## 依赖关系图

```
main.py
├── llm_nodes.py
│   ├── schemas.py
│   ├── llm_client.py
│   └── decorators.py
├── schemas.py
├── llm_client.py
├── context_managers.py
├── iterators.py
├── memory_store.py
├── rag_memory.py
├── observability.py
└── decorators.py
```

## 数据流

```
用户输入 → main.py (/api/start)
    ↓
director_general (总导演规划)
    ↓
ChapterIterator (章节循环)
    ↓
ChapterContext (章节上下文)
    ↓
director_chapter (章节导演)
    ↓
NodeSequence (节点循环)
    ↓
role_assigner → RAG search → role_actor
    ↓
self_check (滑动窗口审查)
    ↓
[通过] → 保存到文件/RAG → 下一节点
[失败] → 重试 / 人工干预
    ↓
text_polisher (章节润色)
    ↓
输出文件
```

## 修改历史

| 日期 | 文件 | 变更 |
|------|------|------|
| 2026-04-14 | skills/main.skill | 新增主程序文档 |
| 2026-04-14 | skills/observability.skill | 新增可观测性文档 |
| 2026-04-14 | skills/rag_memory.skill | 新增 RAG 记忆文档 |
| 2026-04-14 | skills/schemas.skill | 新增数据模型文档 |
| 2026-04-14 | skills/llm_nodes.skill | 新增 LLM 节点文档 |
| 2026-04-14 | skills/llm_client.skill | 新增 LLM 客户端文档 |
| 2026-04-14 | skills/iterators.skill | 新增迭代器文档 |
| 2026-04-14 | skills/decorators.skill | 新增装饰器文档 |
| 2026-04-14 | skills/sliding_window_review.skill | 更新为实际代码实现 |
| 2026-04-14 | skills/novel_architect.skill | 更新为实际架构文档 |
| 2026-04-14 | docs/file_index.md | 更新文件索引 |
| 2026-04-09 | main.py | 新增滑动窗口审查、人工干预 |
| 2026-04-09 | llm_nodes.py | 新增 text_polisher |
| 2026-04-09 | novel_ai/ | 新增 Tauri 前端 |
