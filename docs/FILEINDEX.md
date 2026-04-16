# 项目文件索引 - 面向接口重构后

> 本文档描述重构完成后的项目结构和文件职责
> 重构目标：实现依赖注入、面向接口编程、模块解耦
> 最后更新：2026-04-16

## 目录结构

```
novel/
├── .trae/
│   └── skills/
│       └── refactor-to-interfaces/     # 重构助手 Skill
│           └── SKILL.md
├── interfaces/                          # 抽象接口层
│   ├── __init__.py
│   ├── llm_client.py                   # LLM 客户端接口
│   ├── embedding.py                    # 嵌入服务接口
│   ├── memory.py                       # 记忆存储接口
│   ├── observability.py                # 可观测性接口
│   ├── config.py                       # 配置管理接口
│   └── storage.py                      # 持久化存储接口
├── implementations/                     # 接口实现层
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── moonshot_client.py          # Moonshot API 实现
│   │   ├── ollama_client.py            # Ollama 本地模型实现
│   │   └── factory.py                  # LLM 客户端工厂
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── infini_embedding.py         # InfiniAI 嵌入实现
│   │   └── factory.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── simple_memory_store.py      # 简单内存存储实现
│   │   ├── rag_memory_store.py         # RAG 向量存储实现
│   │   └── factory.py
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── file_backend.py             # 文件日志实现
│   │   ├── null_backend.py             # 空实现（禁用观测）
│   │   └── factory.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── json_storage.py             # JSON 文件存储
│   │   └── factory.py
│   └── config/
│       ├── __init__.py
│       ├── yaml_config.py              # YAML 配置实现
│       └── factory.py
├── core/                                # 核心领域逻辑
│   ├── __init__.py
│   ├── container.py                    # 依赖注入容器
│   ├── container_config.py             # 容器配置
│   ├── nodes/                          # LLM 节点（纯业务逻辑）
│   │   ├── __init__.py
│   │   ├── director_general.py         # 总导演节点
│   │   ├── director_chapter.py         # 章节导演节点
│   │   ├── role_assigner.py            # 角色分配节点
│   │   ├── role_actor.py               # 角色扮演节点
│   │   ├── self_check.py               # 自检节点
│   │   ├── memory_summarizer.py        # 记忆总结节点
│   │   └── text_polisher.py            # 文本润色节点
│   ├── iterators/                      # 迭代器
│   │   ├── __init__.py
│   │   ├── node_sequence.py            # 节点序列迭代器
│   │   └── chapter_iterator.py         # 章节迭代器
│   └── context/                        # 上下文管理
│       ├── __init__.py
│       └── chapter_context.py          # 章节上下文
├── schemas/                             # 数据模型（Pydantic）
│   ├── __init__.py
│   ├── inputs.py                       # 输入模型
│   ├── outputs.py                      # 输出模型
│   ├── memory.py                       # 记忆相关模型
│   └── common.py                       # 通用模型
├── api/                                 # API 层（FastAPI）
│   ├── __init__.py
│   ├── app.py                          # FastAPI 应用实例
│   ├── dependencies.py                 # FastAPI 依赖注入
│   └── routes/                         # 路由定义
│       ├── __init__.py
│       ├── generation.py               # 生成相关路由
│       ├── websocket.py                # WebSocket 路由
│       └── snapshots.py                # 快照管理路由
├── services/                            # 应用服务层
│   ├── __init__.py
│   ├── interfaces.py                   # 服务层接口
│   ├── novel_generator.py              # 小说生成主服务
│   ├── state_manager.py                # 状态管理服务
│   └── snapshot_manager.py             # 快照管理服务
├── utils/                               # 工具函数
│   ├── __init__.py
│   ├── decorators.py                   # 装饰器（json_output, validate_schema）
│   └── helpers.py                      # 辅助函数
├── tests/                               # 测试目录
│   ├── __init__.py
│   ├── test_container.py               # 容器单元测试
│   ├── test_websocket.py               # WebSocket 测试
│   └── test_integration.py             # 集成测试
├── docs/                                # 文档目录
│   ├── FILEINDEX.md                    # 本文档（主要维护）
│   ├── api_spec.md                     # API 规范
│   ├── change_log.md                   # 变更日志
│   ├── container_guide.md              # 容器使用指南
│   ├── interface_spec.md               # 接口规范
│   ├── llm_node_index.md               # LLM 节点索引
│   ├── phase1_completion_report.md     # 阶段一完成报告
│   ├── rag_memory.md                   # RAG 记忆文档
│   ├── tool_reference.md               # 工具参考
│   └── variable_dict.md                # 变量字典
├── ui/                                  # 前端 UI（Tauri+React）
│   └── dist/
├── logs/                                # 日志目录
├── output/                              # 输出目录
├── skills/                              # Skill 文档
│   ├── main.skill
│   ├── novel_architect.skill
│   ├── llm_nodes.skill
│   ├── llm_client.skill
│   ├── decorators.skill
│   ├── iterators.skill
│   ├── schemas.skill
│   ├── rag_memory.skill
│   ├── observability.skill
│   ├── sliding_window_review.skill
│   └── 重构代码.skills
├── config.yaml                          # 主配置文件
├── global_memory.json                   # 全局记忆数据
└── main.py                              # 应用入口（精简版）
```

## 文件职责说明

### 1. 接口层 (interfaces/)

| 文件 | 职责 | 关键接口 |
|------|------|---------|
| `llm_client.py` | 定义 LLM 客户端契约 | `LLMClient`, `LLMClientFactory` |
| `embedding.py` | 定义嵌入服务契约 | `EmbeddingClient`, `VectorStore` |
| `memory.py` | 定义记忆存储契约 | `MemoryStore`, `MemoryRetriever` |
| `observability.py` | 定义可观测性契约 | `ObservabilityBackend`, `Span` |
| `config.py` | 定义配置管理契约 | `ConfigProvider` |
| `storage.py` | 定义持久化存储契约 | `StorageBackend` |
| `__init__.py` | 接口包初始化，导出所有接口 | - |

### 2. 实现层 (implementations/)

#### 2.1 LLM 实现 (llm/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `moonshot_client.py` | Moonshot API 调用，支持流式、重试、性能收集 | `LLMClient` |
| `ollama_client.py` | Ollama 本地模型调用 | `LLMClient` |
| `factory.py` | LLM 客户端工厂，管理实例生命周期 | `LLMClientFactory` |
| `__init__.py` | LLM 实现包初始化 | - |

#### 2.2 嵌入实现 (embedding/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `infini_embedding.py` | InfiniAI 嵌入服务，文本向量化 | `EmbeddingClient` |
| `factory.py` | 嵌入客户端工厂 | - |
| `__init__.py` | 嵌入实现包初始化 | - |

#### 2.3 记忆实现 (memory/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `simple_memory_store.py` | 基于内存的字典存储，支持全局/章节记忆 | `MemoryStore` |
| `rag_memory_store.py` | 基于向量检索的 RAG 存储 | `MemoryStore` |
| `factory.py` | 记忆存储工厂 | `MemoryStoreFactory` |
| `__init__.py` | 记忆实现包初始化 | - |

#### 2.4 可观测性实现 (observability/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `file_backend.py` | 文件日志观测后端，支持追踪、指标、WebSocket | `ObservabilityBackend` |
| `null_backend.py` | 空观测后端（零开销禁用观测） | `ObservabilityBackend` |
| `factory.py` | 观测后端工厂 | `ObservabilityFactory` |
| `__init__.py` | 观测性实现包初始化 | - |

#### 2.5 存储实现 (storage/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `json_storage.py` | JSON 文件 CRUD 操作 | `StorageBackend` |
| `factory.py` | 存储后端工厂 | `StorageBackendFactory` |
| `__init__.py` | 存储实现包初始化 | - |

#### 2.6 配置实现 (config/)

| 文件 | 职责 | 实现接口 |
|------|------|---------|
| `yaml_config.py` | YAML 配置管理，支持热重载 | `ConfigProvider` |
| `factory.py` | 配置提供者工厂 | `ConfigProviderFactory` |
| `__init__.py` | 配置实现包初始化 | - |

### 3. 核心层 (core/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `container.py` | 依赖注入容器 | 管理接口与实现的绑定，支持生命周期、循环依赖检测 |
| `container_config.py` | 容器配置 | 容器初始化配置和默认绑定 |
| `nodes/director_general.py` | 总导演节点 | 生成作品全局规划（世界观、角色、大纲） |
| `nodes/director_chapter.py` | 章节导演节点 | 生成章节详细执行计划 |
| `nodes/role_assigner.py` | 角色分配节点 | 根据节点类型生成角色扮演提示 |
| `nodes/role_actor.py` | 角色扮演节点 | 执行角色扮演，产出正文内容 |
| `nodes/self_check.py` | 自检节点 | 滑动窗口审查内容质量 |
| `nodes/memory_summarizer.py` | 记忆总结节点 | 将原始记忆压缩为结构化卡片 |
| `nodes/text_polisher.py` | 文本润色节点 | 润色章节内容 |
| `iterators/node_sequence.py` | 节点序列迭代器 | 按顺序执行节点序列 |
| `iterators/chapter_iterator.py` | 章节迭代器 | 遍历所有章节 |
| `context/chapter_context.py` | 章节上下文 | 资源生命周期管理 |

### 4. API 层 (api/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `app.py` | FastAPI 应用 | 应用实例创建、中间件配置、CORS 设置 |
| `dependencies.py` | 依赖注入 | FastAPI 依赖函数，从容器解析服务 |
| `routes/generation.py` | 生成路由 | `/api/start`, `/api/pause`, `/api/resume`, `/api/stop` |
| `routes/websocket.py` | WebSocket 路由 | `/api/stream` 实时日志、进度、性能数据 |
| `routes/snapshots.py` | 快照路由 | `/api/snapshots`, `/api/snapshot/{name}` |

### 5. 服务层 (services/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `interfaces.py` | 服务层接口 | 服务层抽象接口定义 |
| `novel_generator.py` | 小说生成主服务 | 编排各个节点完成生成任务 |
| `state_manager.py` | 状态管理服务 | 管理生成状态机（运行/暂停/停止） |
| `snapshot_manager.py` | 快照管理服务 | 保存和恢复生成进度 |

### 6. 数据模型 (schemas/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `inputs.py` | 输入模型 | 所有节点输入的 Pydantic 模型 |
| `outputs.py` | 输出模型 | 所有节点输出的 Pydantic 模型 |
| `memory.py` | 记忆模型 | 记忆卡片、RawMemory 等相关模型 |
| `common.py` | 通用模型 | 共享的数据结构（PerformanceMetrics 等） |

### 7. 工具层 (utils/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `decorators.py` | 装饰器 | `@json_output`, `@validate_schema` |
| `helpers.py` | 辅助函数 | 通用工具函数 |

### 8. 测试层 (tests/)

| 文件 | 职责 | 说明 |
|------|------|------|
| `test_container.py` | 容器单元测试 | 32 个测试，覆盖生命周期、注入、循环依赖等 |
| `test_websocket.py` | WebSocket 测试 | WebSocket 连接和消息测试 |
| `test_integration.py` | 集成测试 | 端到端集成测试 |

## 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                    (应用入口)                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    api/app.py                                │
│                 (FastAPI 应用)                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   routes/    │ │  services/   │ │  dependencies │
│   (路由)      │ │  (服务层)     │ │   (依赖注入)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┴────────────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │  core/container.py   │
               │   (依赖注入容器)      │
               └──────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  interfaces/ │  │implementations│  │   core/      │
│   (接口定义)  │  │   (实现层)    │  │  (领域逻辑)   │
└──────────────┘  └──────────────┘  └──────────────┘
       ▲                 │
       └─────────────────┘
              (实现依赖接口)
```

## 重构后的关键改进

### 1. 依赖注入
- 所有组件通过 `Container` 解析依赖
- 不再使用单例模式，便于测试时 Mock
- 支持三种生命周期：Transient、Singleton、Scoped

### 2. 接口隔离
- 每个模块只依赖接口，不依赖具体实现
- 可以轻松替换实现（如切换 LLM 提供商）
- 新增实现无需修改业务逻辑

### 3. 职责分离
- `interfaces/`：定义契约
- `implementations/`：提供实现
- `core/`：业务逻辑
- `api/`：接口适配
- `services/`：应用服务

### 4. 可测试性
- 可以为每个接口创建 Mock 实现
- 单元测试不依赖外部服务
- 32 个容器单元测试，100% 通过

### 5. 可扩展性
- 添加新 LLM 提供商：实现 `LLMClient` 接口
- 添加新存储后端：实现 `MemoryStore` 接口
- 添加新观测后端：实现 `ObservabilityBackend` 接口

## 配置文件示例

```yaml
# config.yaml
api:
  provider: moonshot  # 可切换: moonshot, ollama
  base_url: https://api.moonshot.cn/v1
  model: kimi-k2.5
  timeout: 60
  max_retries: 3

generation:
  temperature: 1
  top_p: 0.95
  max_tokens: 4096
  mock_mode: false
  debug: false

memory:
  backend: simple     # 可切换: simple, rag
  truncation: 8000

observability:
  backend: file       # 可切换: file, null

storage:
  backend: json       # 可切换: json

embedding:
  api_key: "${EMBEDDING_API_KEY}"
  base_url: https://cloud.infini-ai.com/maas
  model: bge-m3
  dimensions: 1024
  batch_size: 32

pricing:
  kimi-k2.5:
    input_per_million: 12
    output_per_million: 60

ui:
  theme: dark
  font_size: 14
  language: zh

performance:
  cost_alert_usd: 5
```

## 文档索引

| 文档 | 路径 | 内容概述 |
|------|------|---------|
| 文件索引 | `docs/FILEINDEX.md` | 本文档，项目结构和文件职责 |
| API 规范 | `docs/api_spec.md` | HTTP API 和 WebSocket 规范 |
| 变更日志 | `docs/change_log.md` | 项目变更历史记录 |
| 容器指南 | `docs/container_guide.md` | 依赖注入容器使用指南 |
| 接口规范 | `docs/interface_spec.md` | 接口定义规范文档 |
| LLM 节点索引 | `docs/llm_node_index.md` | 所有 LLM 节点的提示词和 Schema |
| 阶段一报告 | `docs/phase1_completion_report.md` | 第一阶段完成状态报告 |
| RAG 记忆 | `docs/rag_memory.md` | RAG 记忆系统文档 |
| 工具参考 | `docs/tool_reference.md` | 工具函数参考手册 |
| 变量字典 | `docs/variable_dict.md` | 变量定义和说明 |

## 迁移检查清单

### 已完成 ✅

- [x] 创建 `interfaces/` 目录和接口定义
- [x] 创建 `implementations/` 目录和实现类
- [x] 实现 `core/container.py` 依赖注入容器
- [x] 实现 `core/container_config.py` 容器配置
- [x] 迁移 `llm_client.py` → `implementations/llm/`
- [x] 迁移 `memory_store.py` → `implementations/memory/`
- [x] 迁移 `rag_memory.py` → `implementations/memory/`
- [x] 迁移 `observability.py` → `implementations/observability/`
- [x] 拆分 `llm_nodes.py` → `core/nodes/`
- [x] 拆分 `iterators.py` → `core/iterators/`
- [x] 拆分 `context_managers.py` → `core/context/`
- [x] 创建 `api/` 目录和路由模块
- [x] 创建 `services/` 目录和服务类
- [x] 重构 `main.py` 为精简入口
- [x] 更新所有导入语句
- [x] 编写接口规范文档
- [x] 编写容器使用指南
- [x] 编写单元测试（32 个测试通过）

### 待处理 ⚠️

- [ ] 清理根目录遗留文件（`llm_nodes.py`, `llm_client.py`, `memory_store.py`, `rag_memory.py`, `observability.py`, `schemas.py`）
- [ ] 编写集成测试
- [ ] 更新 Skill 文档

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-04-16 | 初始版本，完成面向接口重构 |
