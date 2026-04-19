# 变更日志

> 本文档记录 Novel AI Generator 的所有版本更新和变更历史
> 版本格式遵循 [语义化版本](https://semver.org/lang/zh-CN/)

---

## [2.0.0] - 2026-04-19

### 重大变更 - 面向接口架构重构

#### 新增架构层次

- **接口层** (`interfaces/`)
  - 新增 `LLMClient` 接口定义
  - 新增 `MemoryStore` / `MemoryRetriever` 接口
  - 新增 `ObservabilityBackend` 接口
  - 新增 `ConfigProvider` 接口
  - 新增 `StorageBackend` 接口
  - 新增 `EmbeddingClient` / `VectorStore` 接口

- **实现层** (`implementations/`)
  - 新增 `llm/` - LLM 客户端实现（Moonshot、Ollama）
  - 新增 `memory/` - 记忆存储实现（Simple、RAG）
  - 新增 `observability/` - 可观测性实现（File、Null）
  - 新增 `storage/` - 存储实现（JSON）
  - 新增 `embedding/` - 嵌入服务实现（InfiniAI）
  - 新增 `config/` - 配置实现（YAML）

- **核心层重构** (`core/`)
  - 新增 `container.py` - 依赖注入容器
  - 新增 `container_config.py` - 容器配置
  - 重构 `nodes/` - LLM 节点模块化
  - 重构 `iterators/` - 迭代器模块
  - 新增 `context/` - 上下文管理

- **服务层** (`services/`)
  - 新增 `novel_generator.py` - 小说生成主服务
  - 新增 `state_manager.py` - 状态管理
  - 新增 `snapshot_manager.py` - 快照管理
  - 新增 `interfaces.py` - 服务层接口

- **API 层** (`api/`)
  - 新增 `app.py` - FastAPI 应用
  - 新增 `dependencies.py` - 依赖注入
  - 新增 `routes/` - 路由模块

#### 依赖注入容器

- 实现完整的 DI 容器，支持：
  - 三种生命周期（Transient、Singleton、Scoped）
  - 构造函数自动注入
  - 命名注册
  - 工厂函数注册
  - 循环依赖检测

#### 代码质量改进

- 业务逻辑与具体实现完全解耦
- 支持 Mock 实现进行单元测试
- 易于添加新的 LLM 后端和存储实现
- 清晰的接口契约和文档

### 文档更新

- 重写所有文档，统一格式和版本号
- 新增接口规范文档
- 新增容器使用指南
- 新增 API 规范文档

---

## [1.5.0] - 2026-04-17

### 新增 - 快照管理系统

- `services/snapshot_manager.py`: 新增快照管理服务
  - 支持创建、恢复、删除快照
  - 自动快照（每5个节点）
  - 手动快照接口

- `api/routes/snapshots.py`: 新增快照管理路由
  - `GET /api/snapshots` - 获取快照列表
  - `POST /api/snapshots` - 创建快照
  - `POST /api/snapshots/{id}/restore` - 恢复快照
  - `DELETE /api/snapshots/{id}` - 删除快照

### 新增 - 版本管理系统

- `services/version_selector.py`: 新增版本选择服务
  - 支持版本历史记录
  - 版本对比功能
  - 版本回滚

- `api/routes/versions.py`: 新增版本管理路由
  - `GET /api/versions` - 获取版本列表
  - `POST /api/select_version` - 选择版本

---

## [1.4.0] - 2026-04-15

### 新增 - 流式检查提前返回

- `implementations/llm/moonshot_client.py`: 新增 `chat_with_completion_check()` 方法
  - 功能：流式调用 API，每100字符检查一次 JSON 完整性
  - 优势：如果 JSON 完整则提前返回，减少等待时间和成本
  - 回退逻辑：检测到纯文本格式时，提前返回原始内容

- 新增辅助方法：
  - `_find_json_object()`: 使用括号匹配提取完整 JSON 对象
  - `_check_json_complete()`: 检查 JSON 是否完整
  - `_looks_like_plain_text()`: 检测内容是否看起来像纯文本

### 功能增强 - JSON 解析多层回退

- `core/nodes/role_actor.py`: `_parse_state_change_report` 函数重写
  - 实现多层回退解析策略
  - 支持处理各种 LLM 返回格式
  - 自动修复常见 JSON 错误

---

## [1.3.0] - 2026-04-13

### 新增 - RAG 记忆系统

- `implementations/memory/rag_memory_store.py`: 新增 RAG 记忆系统
  - `EmbeddingClient`: 向量化客户端，调用外部 API
  - `VectorStore`: 本地向量存储，支持余弦相似度检索
  - `RagMemorySystem`: 主系统类，整合向量化和存储
  - `add_chunks()`: 添加已分块文本到向量库
  - `search()`: 检索相关内容

- `interfaces/embedding.py`: 新增嵌入服务接口

- `config.yaml`: 新增 embedding 配置
  - `api_key`: Embedding API 密钥
  - `base_url`: API 地址
  - `model`: 向量化模型 (bge-m3)
  - `dimensions`: 向量维度 (1024)

- `docs/rag_memory.md`: 新增 RAG 记忆系统文档

**特性**：
- 每次启动清空向量库
- 单例模式
- 本地 JSON 持久化

---

## [1.2.0] - 2026-04-11

### 功能增强 - 多单元角色系统

- `core/nodes/director_chapter.py`: 添加 6 种节点单元类型定义
  - `narrator`（旁白叙事）：时间推进、背景交代、总结过渡
  - `environment`（环境描写）：空间场景、时间氛围、光线色彩
  - `action`（动作描写）：面部表情、肢体动作、手势细节
  - `dialogue`（角色对话）：台词内容、说话方式、对话节奏
  - `psychology`（角色心理）：内心独白、情绪波动、心理活动
  - `conflict`（冲突/悬念）：矛盾冲突、悬念设置、危机升级

- `core/nodes/role_assigner.py`: 
  - 添加 `unit_type_prompts` 字典
  - 根据节点类型生成不同 prompt 模板

- `core/nodes/role_actor.py`:
  - 添加 `node_type` 参数
  - 根据单元类型调整 system prompt
  - 添加 `unit_type_instructions` 字典

### 功能增强 - 审查反馈传递链路

- `schemas/inputs.py`: `RoleAssignerInput` 添加 `feedback` 字段
- `schemas/outputs.py`: `RoleAssignerOutput` 添加 `feedback` 字段
- `core/nodes/role_assigner.py`: 提示词添加审查反馈部分
- `core/nodes/role_actor.py`: 添加 `feedback` 参数

### 功能增强 - 审查反馈循环

- `config.yaml`: `max_retries` 从 5 增加到 10
- `schemas/inputs.py`: `DirectorChapterInput` 添加 `feedback` 字段

---

## [1.1.0] - 2026-04-08

### 新增 - WebSocket 实时通信

- `api/routes/websocket.py`: 新增 WebSocket 路由
  - 实时推送生成 token
  - 进度更新推送
  - 状态变化通知
  - 人工干预请求

- `services/event_bus.py`: 新增事件总线
  - 发布-订阅模式
  - 异步事件处理
  - WebSocket 事件转发

### 新增 - 可观测性系统

- `interfaces/observability.py`: 定义可观测性接口
- `implementations/observability/file_backend.py`: 文件日志实现
- `implementations/observability/null_backend.py`: 空实现

**功能**：
- 分布式追踪（start_span/end_span）
- 性能指标收集
- 日志记录
- WebSocket 广播

### 新增 - 性能指标

- 首 Token 延迟 (TTF)
- 生成速度 (TPS)
- API 延迟
- Token 用量统计
- 成本估算

---

## [1.0.0] - 2026-04-01

### 初始版本发布

#### 核心功能

- **多智能体架构**：总导演 → 章节导演 → 角色分配 → 角色扮演 → 自检 → 润色
- **小说生成**：支持长篇小说自动生成
- **记忆系统**：角色记忆和全局记忆管理
- **滑动窗口审查**：动态内容审查机制
- **人工干预**：支持人工介入修改

#### 技术栈

- **后端**：Python + FastAPI
- **前端**：Tauri + React + TypeScript
- **LLM**：Moonshot API / Ollama
- **配置**：YAML

#### 项目结构

```
novel/
├── main.py              # 主入口
├── llm_nodes.py         # LLM 节点（已重构）
├── schemas.py           # 数据模型（已拆分）
├── llm_client.py        # LLM 客户端（已重构）
├── config.yaml          # 配置文件
└── novel_ai/            # 前端应用
```

#### API 端点

- `POST /api/start` - 启动生成
- `GET /api/status` - 查询状态
- `POST /api/pause` - 暂停
- `POST /api/resume` - 恢复
- `POST /api/stop` - 停止
- `POST /api/select_version` - 版本选择
- `POST /api/retry_node` - 重试节点
- `WS /api/stream` - WebSocket 流式通信

---

## 版本说明

### 版本号格式

版本号格式：`主版本号.次版本号.修订号`

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修正

### 版本支持策略

| 版本 | 状态 | 支持截止日期 |
|------|------|-------------|
| 2.0.x | 活跃维护 | 2026-12-31 |
| 1.5.x | 安全更新 | 2026-06-30 |
| 1.0.x | 已停止 | - |

---

## 升级指南

### 从 1.x 升级到 2.0

1. **备份配置**
   ```bash
   cp config.yaml config.yaml.backup
   ```

2. **更新代码**
   ```bash
   git pull origin main
   ```

3. **安装新依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **迁移配置**
   - 检查新的 `config.example.yaml`
   - 更新 `config.yaml` 中的配置项

5. **验证安装**
   ```bash
   python main.py
   ```

### 破坏性变更

#### 2.0.0

- 项目结构完全重构，旧代码不再兼容
- 配置文件格式更新
- API 端点路径调整

#### 1.5.0

- 快照存储格式变更，旧快照需要重新创建

#### 1.2.0

- 节点输出格式变更，添加了 `unit_type` 字段

---

## 贡献者

感谢所有为项目做出贡献的开发者！

### 核心团队

- 架构设计：[@architect]
- 后端开发：[@backend-dev]
- 前端开发：[@frontend-dev]
- 文档维护：[@docs-maintainer]

### 特别感谢

- Moonshot AI 团队提供的 API 支持
- 开源社区的各种工具和库
