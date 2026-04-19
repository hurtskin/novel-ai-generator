# 项目文件索引

> 本文档描述 Novel AI Generator 的项目结构和文件职责
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [项目概览](#项目概览)
2. [目录结构](#目录结构)
3. [核心文件说明](#核心文件说明)
4. [接口层](#接口层)
5. [实现层](#实现层)
6. [服务层](#服务层)
7. [API 层](#api-层)
8. [前端](#前端)

---

## 项目概览

```
novel/
├── main.py                      # 应用入口
├── config.yaml                  # 配置文件
├── config.example.yaml          # 配置示例
├── interfaces/                  # 抽象接口层
├── implementations/             # 接口实现层
├── core/                        # 核心业务逻辑
├── services/                    # 应用服务层
├── api/                         # API 层
├── schemas/                     # 数据模型
├── utils/                       # 工具函数
├── docs/                        # 文档
└── novel_ai/                    # Tauri + React 前端
```

---

## 目录结构

### 根目录文件

| 文件 | 职责 |
|------|------|
| `main.py` | 应用入口，初始化容器和启动 FastAPI |
| `config.yaml` | 运行时配置文件 |
| `config.example.yaml` | 配置示例模板 |
| `requirements.txt` | Python 依赖列表 |
| `.gitignore` | Git 忽略规则 |

### 接口层 (`interfaces/`)

| 文件 | 职责 | 接口定义 |
|------|------|----------|
| `__init__.py` | 接口包初始化 | - |
| `llm_client.py` | LLM 客户端接口 | `LLMClient`, `LLMClientFactory` |
| `memory.py` | 记忆存储接口 | `MemoryStore`, `MemoryRetriever` |
| `observability.py` | 可观测性接口 | `ObservabilityBackend` |
| `config.py` | 配置接口 | `ConfigProvider` |
| `storage.py` | 存储接口 | `StorageBackend` |
| `embedding.py` | 嵌入服务接口 | `EmbeddingClient`, `VectorStore` |

### 实现层 (`implementations/`)

#### LLM 实现 (`implementations/llm/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `moonshot_client.py` | Moonshot API 实现 | `MoonshotClient` |
| `ollama_client.py` | Ollama 本地模型实现 | `OllamaClient` |
| `factory.py` | LLM 客户端工厂 | `LLMClientFactoryImpl` |

#### 记忆实现 (`implementations/memory/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `simple_memory_store.py` | 简单内存存储 | `SimpleMemoryStore` |
| `rag_memory_store.py` | RAG 向量存储 | `RAGMemoryStore` |
| `factory.py` | 记忆存储工厂 | `MemoryStoreFactoryImpl` |

#### 可观测性实现 (`implementations/observability/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `file_backend.py` | 文件日志实现 | `FileObservabilityBackend` |
| `null_backend.py` | 空实现 | `NullObservabilityBackend` |
| `factory.py` | 观测后端工厂 | `ObservabilityFactoryImpl` |

#### 存储实现 (`implementations/storage/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `json_storage.py` | JSON 文件存储 | `JsonStorageBackend` |
| `factory.py` | 存储后端工厂 | `StorageBackendFactoryImpl` |

#### 嵌入实现 (`implementations/embedding/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `infini_embedding.py` | InfiniAI 嵌入服务 | `InfiniEmbeddingClient`, `SimpleVectorStore` |
| `factory.py` | 嵌入客户端工厂 | `EmbeddingClientFactoryImpl` |

#### 配置实现 (`implementations/config/`)

| 文件 | 职责 | 实现类 |
|------|------|--------|
| `__init__.py` | 包初始化 | - |
| `yaml_config.py` | YAML 配置管理 | `YamlConfigProvider` |
| `factory.py` | 配置提供者工厂 | `ConfigProviderFactoryImpl` |

### 核心层 (`core/`)

| 文件/目录 | 职责 |
|-----------|------|
| `__init__.py` | 核心包初始化 |
| `container.py` | 依赖注入容器实现 |
| `container_config.py` | 容器配置和初始化 |
| `nodes/` | LLM 节点实现 |
| `iterators/` | 迭代器实现 |
| `context/` | 上下文管理 |

#### 节点目录 (`core/nodes/`)

| 文件 | 职责 | 节点类 |
|------|------|--------|
| `__init__.py` | 节点包初始化 | - |
| `director_general.py` | 总导演节点 | `DirectorGeneralNode` |
| `director_chapter.py` | 章节导演节点 | `DirectorChapterNode` |
| `role_assigner.py` | 角色分配器节点 | `RoleAssignerNode` |
| `role_actor.py` | 角色演员节点 | `RoleActorNode` |
| `self_check.py` | 自检节点 | `SelfCheckNode` |
| `memory_summarizer.py` | 记忆总结器节点 | `MemorySummarizerNode` |
| `text_polisher.py` | 文本润色节点 | `TextPolisherNode` |

#### 迭代器目录 (`core/iterators/`)

| 文件 | 职责 | 类 |
|------|------|-----|
| `__init__.py` | 迭代器包初始化 | - |
| `chapter_iterator.py` | 章节迭代器 | `ChapterIterator` |
| `node_sequence.py` | 节点序列迭代器 | `NodeSequence` |

#### 上下文目录 (`core/context/`)

| 文件 | 职责 | 类 |
|------|------|-----|
| `__init__.py` | 上下文包初始化 | - |
| `chapter_context.py` | 章节上下文管理 | `ChapterContext` |

### 服务层 (`services/`)

| 文件 | 职责 | 服务类 |
|------|------|--------|
| `__init__.py` | 服务包初始化 | - |
| `interfaces.py` | 服务层接口定义 | `NovelGenerationService`, etc. |
| `novel_generator.py` | 小说生成主服务 | `NovelGenerator` |
| `state_manager.py` | 状态管理服务 | `StateManager` |
| `snapshot_manager.py` | 快照管理服务 | `SnapshotManager` |
| `version_selector.py` | 版本选择服务 | `VersionSelector` |
| `event_bus.py` | 事件总线 | `EventBus` |
| `performance_metrics.py` | 性能指标收集 | `PerformanceMetricsCollector` |
| `debug_log.py` | 调试日志服务 | `DebugLogService` |
| `file_output.py` | 文件输出服务 | `FileOutputService` |
| `rag_retrieval.py` | RAG 检索服务 | `RAGRetrievalService` |
| `node_regenerate.py` | 节点再生服务 | `NodeRegenerateService` |
| `node_retry.py` | 节点重试服务 | `NodeRetryService` |
| `config_manager.py` | 配置管理服务 | `ConfigManager` |

### API 层 (`api/`)

| 文件/目录 | 职责 |
|-----------|------|
| `__init__.py` | API 包初始化 |
| `app.py` | FastAPI 应用实例 |
| `dependencies.py` | FastAPI 依赖注入 |
| `routes/` | 路由定义 |

#### 路由目录 (`api/routes/`)

| 文件 | 职责 | 路由前缀 |
|------|------|----------|
| `__init__.py` | 路由包初始化 | - |
| `generation.py` | 生成相关路由 | `/api` |
| `websocket.py` | WebSocket 路由 | `/api/stream` |
| `snapshots.py` | 快照管理路由 | `/api/snapshots` |
| `versions.py` | 版本管理路由 | `/api/versions` |

### 数据模型 (`schemas/`)

| 文件 | 职责 |
|------|------|
| `__init__.py` | 模型包初始化 |
| `inputs.py` | 输入模型定义 |
| `outputs.py` | 输出模型定义 |
| `memory.py` | 记忆相关模型 |
| `common.py` | 通用模型定义 |

### 工具函数 (`utils/`)

| 文件 | 职责 |
|------|------|
| `__init__.py` | 工具包初始化 |
| `decorators.py` | 装饰器（json_output, validate_schema） |
| `helpers.py` | 辅助函数 |

### 前端 (`novel_ai/`)

| 文件/目录 | 职责 |
|-----------|------|
| `package.json` | Node.js 依赖 |
| `tsconfig.json` | TypeScript 配置 |
| `vite.config.ts` | Vite 配置 |
| `index.html` | 入口 HTML |
| `src/` | React 源码 |
| `src-tauri/` | Tauri 后端 |

#### React 源码 (`novel_ai/src/`)

| 文件/目录 | 职责 |
|-----------|------|
| `main.tsx` | React 入口 |
| `App.tsx` | 主应用组件 |
| `App.css` | 应用样式 |
| `api/client.ts` | API 客户端 |
| `stores/appStore.ts` | 状态管理 |
| `components/` | React 组件 |

#### 组件目录 (`novel_ai/src/components/`)

| 文件 | 职责 |
|------|------|
| `ChatPanel.tsx` | 聊天面板 |
| `ProgressPanel.tsx` | 进度面板 |
| `SettingsPanel.tsx` | 设置面板 |
| `DebugPanel.tsx` | 调试面板 |
| `InterventionPanel.tsx` | 干预面板 |
| `PerformancePanel.tsx` | 性能面板 |

---

## 核心文件说明

### main.py

应用入口文件，职责：
- 初始化日志配置
- 创建依赖注入容器
- 启动 FastAPI 应用

### core/container.py

依赖注入容器核心实现，职责：
- 依赖注册和解析
- 生命周期管理
- 循环依赖检测

### core/container_config.py

容器配置，职责：
- 定义默认绑定
- 初始化容器实例
- 配置实现类映射

### api/app.py

FastAPI 应用，职责：
- 创建 FastAPI 实例
- 注册路由
- 配置中间件
- 异常处理

### services/novel_generator.py

小说生成主服务，职责：
- 协调 LLM 节点执行
- 管理生成状态
- 处理迭代逻辑

---

## 文件命名规范

### Python 文件

- 小写字母 + 下划线
- 例如：`moonshot_client.py`, `simple_memory_store.py`

### TypeScript/React 文件

- PascalCase 组件文件
- camelCase 工具文件
- 例如：`ChatPanel.tsx`, `appStore.ts`

### 配置文件

- 小写字母 + 连字符
- 例如：`config.yaml`, `tsconfig.json`

---

## 导入规范

### 绝对导入

```python
# 推荐
from interfaces.llm_client import LLMClient
from core.container import Container

# 不推荐
from ..interfaces.llm_client import LLMClient
```

### 相对导入

仅在同一包内使用相对导入：

```python
# 同一包内可以使用
from .factory import LLMClientFactoryImpl
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，添加接口层和实现层 |
| 1.5.0 | 2026-04-17 | 添加快照和版本管理服务 |
| 1.0.0 | 2026-04-01 | 初始版本 |
