# 变更日志

## 2026-04-13

### 新增 - RAG 记忆系统

- `rag_memory.py`: 新增 RAG 记忆系统模块
  - EmbeddingClient: 向量化客户端，调用外部 API
  - VectorStore: 本地向量存储，支持余弦相似度检索
  - RagMemorySystem: 主系统类，整合向量化和存储
  - add_chunks(): 添加已分块文本到向量库
  - search(): 检索相关内容

- `config.yaml`: 新增 embedding 配置
  - api_key: Embedding API 密钥
  - base_url: API 地址
  - model: 向量化模型 (bge-m3)

- `docs/rag_memory.md`: 新增 RAG 记忆系统文档

特性：
- 每次启动清空向量库
- 单例模式
- 本地 JSON 持久化

## 2026-04-11

### 功能增强 - 方案B：流式检查提前返回

- `llm_client.py`: 新增 `chat_with_completion_check()` 方法
  - 功能：流式调用API，每100字符检查一次JSON完整性
  - 优势：如果JSON完整则提前返回，减少等待时间和成本
  - 回退逻辑：检测到纯文本格式（非JSON）时，提前返回原始内容
  
- `llm_client.py`: 新增辅助方法
  - `_find_json_object()`: 使用括号匹配提取完整JSON对象
  - `_check_json_complete()`: 检查JSON是否完整且包含非空content字段
  - `_looks_like_plain_text()`: 检测内容是否看起来像纯文本

- `llm_nodes.py`: 修改 `role_actor` 节点调用
  - 从 `client.chat()` 改为 `client.chat_with_completion_check()`
  - max_tokens 从 4096 增加到 8192，减少截断风险
  - 新增 check_interval=100 参数，控制检查频率

- `llm_client.py`: 添加重试逻辑支持
  - 保留 429/500 错误自动重试机制
  - 指数退避策略

**测试验证:**
- 完整JSON：✅ 正确解析并提前返回
- 非JSON格式（纯文本）：✅ 检测并提前返回
- 被截断的JSON：✅ 检测为不完整，等待完整响应
- 缺少content字段：✅ 检测为不完整
- 多余逗号：✅ 自动修复
- 嵌套JSON：✅ 正确解析

### Bug 修复 - JSON 解析多层回退

- `llm_nodes.py`: `_parse_state_change_report` 函数重写
  - 问题：LLM 返回内容格式多样，原有解析逻辑无法处理所有情况
  - 问题根因1：LLM 返回的 JSON 中 content 字段包含未转义的换行符和引号
  - 问题根因2：LLM 输出可能被截断，导致 JSON 不完整
  - 解决方案：实现多层回退解析策略：
    1. 预处理：清理 markdown 代码块标记（只清理开头/结尾）
    2. 预处理：清理无效字符和 HTML 实体
    3. 策略A：直接解析整个内容（以 { 开头 } 结尾）
    4. 策略B：首尾清理后解析
    5. 策略C：括号匹配提取
    6. 策略D：智能括号匹配（忽略字符串内的大括号）
    7. 策略E：查找代码块内的 JSON
    8. 策略F：正则表达式直接提取字段（支持截断的元数据）
    9. 回退：返回原始内容作为 content（保证不为空）

### 功能增强 - 多单元角色系统

- `llm_nodes.py`: `director_chapter` 添加 6 种节点单元类型定义
  - narrator（旁白叙事）：时间推进、背景交代、总结过渡
  - environment（环境描写）：空间场景、时间氛围、光线色彩
  - action（动作描写）：面部表情、肢体动作、手势细节
  - dialogue（角色对话）：台词内容、说话方式、对话节奏
  - psychology（角色心理）：内心独白、情绪波动、心理活动
  - conflict（冲突/悬念）：矛盾冲突、悬念设置、危机升级
- `llm_nodes.py`: `director_chapter` 在 node_sequence 的 JSON Schema 中限制 type 字段为枚举值
- `llm_nodes.py`: `role_assigner` 添加 `unit_type_prompts` 字典，根据节点类型生成不同 prompt 模板
- `llm_nodes.py`: `role_actor` 添加 `node_type` 参数，根据单元类型调整 system prompt
- `llm_nodes.py`: `role_actor` 添加 `unit_type_instructions` 字典，为每种单元类型提供不同指示
- `schemas.py`: `CurrentNodeInfo` 已有 `type` 字段，兼容新的单元类型

### 功能增强 - 审查反馈传递链路

- `schemas.py`: `RoleAssignerInput` 添加 `feedback` 字段
- `schemas.py`: `RoleAssignerOutput` 添加 `feedback` 字段
- `llm_nodes.py`: `role_assigner` 提示词添加审查反馈部分
- `llm_nodes.py`: `role_actor` 添加 `feedback` 参数，在 system prompt 中加入审查反馈
- `main.py`: 传递审查反馈到 RoleAssigner 和 RoleActor 节点

### 功能增强 - 审查反馈循环

- `config.yaml`: `max_retries` 从 5 增加到 10
- `schemas.py`: `DirectorChapterInput` 添加 `feedback` 字段
- `llm_nodes.py`: `director_chapter` 添加 feedback 参数支持，在提示词中包含"上一轮审查反馈"部分
- `llm_nodes.py`: `self_check` 添加宽松审查条件，减少不必要的重试
- `main.py`: 传递审查反馈 (improvement_suggestions) 给章节导演节点
- `main.py`: 修复 feedback 字段类型转换问题（支持 list/dict/None 转 string）
- `main.py`: 修复章节内容保存逻辑
  - 原因: 重试时内容直接追加到文本，导致重复内容
  - 修改: 只在审查通过 (needs_revision=false) 时才追加到文本，重试时用新内容覆盖

### Schema 调整

- `DirectorGeneralOutput.genre_specific`: 从 `str` 改为 `GenreSpecific` 类型，以匹配 LLM 返回的对象结构
  - 原因: LLM 稳定返回 `{"type": "object", "properties": {...}}` 格式的对象

### 解析器修复

- `decorators.py`: JSON 解析时自动提取 `properties` 字段
  - 原因: LLM 返回的 JSON 包含 `{"type": "object", "properties": {...}}` 结构，需要提取 `properties` 内的实际数据
- `decorators.py`: `DirectorGeneralOutput` 的 `genre_specific` 字段类型兼容处理
  - 原因: LLM 有时返回字符串，有时返回对象，添加自动转换逻辑

### Prompt 优化

- `llm_nodes.py`: `director_chapter` 的 `character_presence_plan` 字段添加严格的格式说明
  - 原因: 原来只声明为 `object`，LLM 自由发挥导致格式不稳定
  - 修改: 明确指定必须是 `{"角色名": [节点索引数字]}` 格式
- `llm_nodes.py`: `role_actor` 的 `relationship_updates` 示例修正
  - 原因: 示例与 Schema 不一致，导致 LLM 输出嵌套对象
  - 修改: 从 `{"角色B": {"trust": 80, "status": "成为朋友"}}` 改为 `{"角色B": "成为朋友"}`
- `llm_nodes.py`: `role_actor` 输出格式重构
  - 原因: LLM 只输出 JSON 状态报告，没有正文内容
  - 修改: 将正文内容也放入 JSON 的 content 字段中，示例：`{"content": "正文...", "new_memories": [], ...}`
  - 同步修改 `_parse_state_change_report` 函数以解析 content 字段

### 功能增强 - Context Caching 支持

**新增 Schema 类:**
- `CacheConfig`: Context Caching 配置
  - `enabled`: 是否启用缓存
  - `cache_type`: 缓存类型（支持 'file'）
  - `cache_id`: 已创建的缓存 ID
  - `cache_content`: 缓存内容（用于创建新缓存）
  - `expires_ttl`: 缓存有效期（秒）
  
- `CacheManifest`: 缓存清单
  - `cache_id`: 缓存 ID
  - `cache_key`: 缓存键名
  - `cached_tokens`: 缓存的 token 数量
  - `created_at`: 创建时间
  - `expires_at`: 过期时间

- `CachedContent`: 可缓存的静态内容
  - `system_prompt`: 系统提示词（静态，可缓存）
  - `static_context`: 静态上下文（如世界观、角色设定）
  - `cache_manifest`: 缓存清单

- `LlmRequestConfig`: LLM 请求配置
  - `enable_cache`: 是否启用缓存
  - `cache_id`: 缓存 ID
  - `cache_ttl`: 缓存 TTL

- `LlmResponseMetadata`: LLM 响应元数据
  - `cache_hit`: 是否命中缓存
  - `cached_tokens`: 缓存的 token 数
  - 及其他性能指标

**修改的 Schema:**
- `DirectorGeneralInput`: 新增 `cache_config` 和 `cached_static_context` 字段
- `RoleAssignerInput`: 新增 `cache_config` 和 `cached_static_context` 字段
- `PromptComponents`: 新增 `cache_config` 和 `cached_static_context` 字段

**修改的代码:**
- [llm_client.py] `LlmClient.chat()` 方法新增 `cache_id` 参数
- [llm_client.py] `_chat_moonshot()` 方法支持 `cache` 参数，支持 Context Caching
- [llm_client.py] 响应结果新增 `cache` 信息（cache_hit, cache_id）
- [llm_client.py] `usage` 新增 `cached_tokens` 字段
- [llm_client.py] `_calculate_cost()` 支持缓存折扣计算

**Kimi API Context Caching 机制:**
根据 Kimi 官方 API 文档，Context Caching 工作流程如下：
1. 首次请求：发送完整内容（包含静态前缀），API 返回 `cache_id`
2. 后续请求：使用 `cache_id`，只需发送动态内容，静态前缀从缓存读取，享受缓存折扣价

**接入方式:**
```python
from llm_client import get_llm_client

client = get_llm_client()

# 首次请求 - 创建缓存
result = client.chat(
    messages=[...],
    cache_id=None  # 不传或传 None，创建新缓存
)

# 后续请求 - 复用缓存
result = client.chat(
    messages=[...],
    cache_id="上一步返回的cache_id"
)

# 检查缓存命中
if result.get("cache", {}).get("cache_hit"):
    print("缓存命中!")
```

---

## 2026-04-10

### 重构 - LLM 客户端重命名

**修改内容:**
- 重命名 `kimi_client.py` 为 `llm_client.py`
- 类名 `KimiApiClient` 改为 `LlmClient`
- 函数 `get_kimi_client()` 改为 `get_llm_client()`（保留 `get_kimi_client()` 别名以兼容）
- 更新所有引用：main.py, llm_nodes.py

---

### 功能增强 - Ollama 本地模型支持

**新增内容:**
- [config.yaml] 添加 `ollama` 配置节，支持本地 Ollama 服务
  - `enabled`: 是否启用 Ollama（true/false）
  - `base_url`: Ollama 服务地址（默认 http://localhost:11434）
  - `model`: 本地模型名称（默认 llama3）
  - `timeout`: 请求超时时间（默认 180 秒）
- [config.yaml] 添加 `api.provider` 配置项，支持 `moonshot` 和 `ollama` 切换
- [llm_client.py] 重构 `LlmClient.chat()` 方法
  - 根据 `provider` 和 `ollama.enabled` 配置自动选择调用 Moonshot API 或 Ollama
  - 只有当 `provider=ollama` 且 `ollama.enabled=true` 时才使用 Ollama
  - 新增 `_chat_moonshot()` 方法封装原 Moonshot API 调用逻辑
  - 新增 `_chat_ollama()` 方法实现 Ollama API 调用
  - Ollama 调用使用 OpenAI 兼容格式 `/api/chat`
  - Ollama 模式下成本固定为 0（本地模型无 API 费用）

**切换方式:**
```yaml
# 使用 Moonshot API（默认）
api:
  provider: moonshot

# 使用本地 Ollama
api:
  provider: ollama
ollama:
  enabled: true
  base_url: http://localhost:11434
  model: llama3
```

---

## 2026-04-09 (续)

### 功能增强 - WebSocket 实时推送与文件输出

**修复内容:**
- [main.py] 实现直接异步 WebSocket 广播机制 `broadcast_ws()`
  - 添加全局 `ws_clients` 列表追踪连接客户端
  - 在 `generate_task` 内部定义异步广播函数
  - 替换所有 `observability.broadcast()` 调用为 `broadcast_ws()`
  - 修复 `observability.broadcast()` 在异步上下文中不工作的问题
- [main.py] 添加小说文本文件输出功能
  - 生成完成后自动保存到 `output/novel_{timestamp}.txt`
  - WebSocket 推送 `complete` 事件包含输出文件路径
- [main.py] 端口统一：默认使用 8000 端口
- [main.py] 添加模拟模式配置支持
  - 新增 `apply_mock_mode()` 函数从配置文件读取 `generation.mock_mode`
  - 支持通过 API `/api/config` 动态切换模拟模式
- [config.yaml] 添加 `generation.mock_mode` 配置项
- [main.py] 清理调试代码：移除所有 `[DEBUG]` 日志输出

**测试验证:**
- WebSocket 实时推送每章进度状态 ✅
- 生成完成后收到 `complete` 事件 ✅
- 状态 API `/api/status` 返回完整信息 ✅
- 性能 API `/api/performance` 返回指标 ✅
- 小说文本文件正确输出到 `output/` 目录 ✅

---

## 2026-04-09 (续)

### Bug 修复 - 系统集成问题

**修复内容:**
- [main.py] 修复 ChapterContext 调用参数：从字典对象改为文件路径字符串
- [observability.py] 修复 start_span 方法：改为 @contextmanager 上下文管理器以支持 with 语法
- [docs/tool_reference.md] 更新 start_span 文档：标注为上下文管理器并添加用法示例

### Bug 修复 - API 参数问题

**修复内容:**
- [config.yaml] temperature 从 0.7 改为 1：kimi-k2.5 模型只支持 temperature=1
- [kimi_client.py] 默认 temperature 从 0.7 改为 1
- [config.yaml] top_p 从 0.9 改为 0.95：kimi-k2.5 模型只支持 top_p=0.95
- [kimi_client.py] 默认 top_p 从 0.9 改为 0.95

**问题原因:**
- kimi-k2.5 模型 API 返回错误：invalid temperature: only 1 is allowed for this model

---

## 2026-04-09 (续)

### 动态配置加载

**修复内容:**
- 添加 `load_config_from_file()` 函数：每次从文件动态加载配置
- 在 `KimiApiClient` 中添加 `reload_config()` 方法：保存配置后重新加载
- 修改 `GET /api/config` 端点：使用 `load_config_from_file()` 实时读取
- 修改 `POST /api/config` 端点：
  - 使用 `deep_update()` 深度更新嵌套配置
  - 保存后自动调用 `reload_config()` 重新加载 API 客户端配置
  - 添加异常处理避免崩溃

**测试验证:**
- GET /api/config 每次返回最新配置文件内容
- POST /api/config 修改配置后立即生效
- KimiApiClient 单例自动更新配置

---

**修复内容:**
- 添加 `POST /api/config` 端点：保存配置到 config.yaml
- 修复 `GET /api/config` 端点：返回完整配置（api_key, ui, performance, genre）
- 修复 WebSocket 消息解析：`data.payload` → `data.data || data.payload`

### T14 - 前端界面实现

**新增功能:**
- Tauri + React 前端项目

**项目结构 (novel_ai/):**
- `src-tauri/`: Tauri Rust 后端配置
- `src/App.tsx`: React 主应用组件
- `src/api/client.ts`: API 客户端和 WebSocket 通信
- `src/stores/appStore.ts`: Zustand 状态管理

**五个核心面板:**
1. **调试面板 (DebugPanel)**
   - 实时日志流：WebSocket 接收，自动滚动
   - 清空日志按钮

2. **性能面板 (PerformancePanel)**
   - 实时速度仪表盘 (tokens/sec)
   - Token 消耗柱状图（按章节）
   - API 延迟折线图
   - 成本预估实时显示
   - 导出性能报告按钮

3. **对话面板 (ChatPanel)**
   - Chat 式消息气泡界面
   - 角色切换下拉框
   - 记忆片段侧边栏
   - 编辑重生成功能

4. **设置面板 (SettingsPanel)**
   - API 配置：api_key（密码输入）、base_url、model 下拉框
   - 生成参数：temperature/top_p/max_tokens
   - 界面设置：主题、语言、字号
   - 性能阈值：成本告警线
   - 文体选择：novel/script/game_story/dialogue/article

5. **进度面板 (ProgressPanel)**
   - 创作主题输入 + 开始按钮
   - 章节级进度条
   - 节点级进度条
   - 预估剩余时间/成本
   - 暂停/继续/终止按钮

**WebSocket 消息类型:**
- `log`: 日志流
- `node_metric`: 节点性能指标
- `chapter_metric`: 章节性能指标
- `total_metric`: 总性能指标
- `progress`: 进度更新
- `chat`: 对话消息
- `memory`: 记忆片段
- `error`: 错误通知

**全局功能:**
- 连接状态指示器
- 错误 Toast 通知

**文档更新:**
- docs/file_index.md: 新增前端文件条目

**打包命令:**
```bash
cd novel_ai
npm install
npm run tauri build
```

### T14 续 - 前端界面优化

**UI 优化:**
- 进度面板布局重构：简洁美观的卡片式设计
- 状态指示器：右上角显示运行状态（空闲/生成中/已暂停/已完成），带脉冲动画
- 按钮逻辑优化：
  - 空闲状态：只显示主题输入框和"开始生成"按钮
  - 运行中：显示进度条、实时数据、暂停/继续/终止按钮
  - 完成后：显示"新建任务"按钮

**主题支持:**
- 深色/浅色主题自动跟随 config.yaml 配置
- 主题切换实时生效，无需刷新页面

**输入框优化:**
- 主题输入框改为 textarea（多行文本域）
- 默认显示 3 行，支持拖拽调整大小

**后端连接:**
- 连接失败自动重试 3 次
- 错误提示：`无法连接到后端服务 (端口 8000)。请确保后端正在运行: python main.py`
- 前端端口改为 8002（client.ts 中配置）

**进度同步:**
- WebSocket 实时接收后端 progress 事件
- 切换标签页不丢失进度数据（Zustand 全局状态）
- 成本超限时显示红色警告

**文档更新:**
- docs/file_index.md: 更新前端相关文件条目

### T13 - 后端 API 实现

**新增功能:**
- FastAPI 后端 HTTP 端点
- WebSocket 实时推送

**HTTP 端点:**
- `POST /api/start`: 启动生成任务，接收 user_input，返回 task_id
- `GET /api/status`: 查询当前状态（章节/节点/进度百分比）
- `POST /api/pause`: 暂停（设置全局标志位）
- `POST /api/resume`: 继续（清除标志位）
- `POST /api/stop`: 终止（设置终止标志位）
- `GET /api/snapshot/{name}`: 加载状态快照
- `POST /api/snapshot/{name}`: 保存状态快照
- `GET /api/snapshots`: 获取快照列表
- `POST /api/regenerate`: 指定节点重新生成
- `GET /api/performance`: 获取性能指标
- `GET /api/config`: 获取配置信息

**WebSocket 端点:**
- `WS /api/stream`: 实时推送日志流/进度/性能/Token

**状态管理:**
- 全局状态对象：current_task, current_chapter, current_node, is_paused, is_stopped
- 线程安全：asyncio.Lock 用于状态修改

**快照系统:**
- `observability.save_snapshot(name)`: 保存性能指标快照
- `observability.load_snapshot(name)`: 加载性能指标快照
- `observability.list_snapshots()`: 列出所有快照

**文档更新:**
- docs/api_spec.md: 新增 HTTP API 和 WebSocket API 端点详细说明
- docs/file_index.md: 更新 main.py 和 observability.py 修改历史

### T10 - 角色扮演器实现

**新增功能:**
- `role_actor()` 函数：角色扮演 LLM 节点

**功能:**
- `@json_output + @validate_schema` 双重装饰器
- 输入：role_assigner_output（包含 generation_prompt）
- 构造 messages：system 为 identity，user 为完整 prompt
- 调用 KimiApiClient.chat()，流式模式，stream_callback 实时推送 token
- 输出：generated_content + state_change_report
- 验证失败处理：空输出或长度不足 50 字则重试（最多 3 次）
- 流式回调集成：stream_callback(token) → WebSocket 广播到 UI

**装饰器:**
- `@json_output`: 自动解析 JSON 输出
- `@validate_schema(schema_class=RoleActorOutput)`: 自动验证输出格式

**输入参数:**
- `role_assigner_output` (RoleAssignerOutput): 角色分配器输出
- `chapter_id` (int): 当前章节 ID
- `node_id` (str): 当前节点 ID
- `stream_callback` (Callable, optional): 流式回调函数
- `update_memory_callback` (Callable, optional): 记忆更新回调函数

**state_change_report 结构:**
```python
{
    "new_memories": ["试探陈默，发现其防御姿态"],
    "emotion_shift": "从警觉压抑到确认怀疑",
    "new_discoveries": ["照片裁剪痕迹", "陈默右手挡抽屉"],
    "relationship_updates": {
        "陈默": {"trust": -15, "status": "表面朋友实际怀疑"}
    }
}
```

**后处理:**
- 自动调用 memory_updater 更新章节记忆库
- 触发 validation.output_non_empty 检查

**验证失败处理:**
- 空输出或长度不足 50 字：重试该节点，记录 warning
- 3 次重试后仍失败：返回截断内容（50字）

**文档更新:**
- `file_index.md`: 更新 llm_nodes.py 条目（添加 T10）
- `variable_dict.md`: 新增 role_actor 变量文档
- `tool_reference.md`: 新增 role_actor 工具文档

---

### T12 - 观测机制实现

**新增文件:**
- `observability.py`: 运行时追踪、日志、性能收集、WebSocket广播模块

**功能:**
- 日志系统：DEBUG/INFO/WARNING/ERROR 四级日志，输出到 logs/novel_{timestamp}.log
- 结构化追踪：JSONL 格式，输出到 logs/trace_{timestamp}.jsonl
- 性能收集：每节点 → 每章 → 总汇总三级指标
- WebSocket 广播：log/progress/performance 三种消息类型

**类方法:**
- `log_event(level, chapter, node, message)` - 写入日志
- `start_span(chapter, node) -> span_id` - 开始追踪
- `end_span(span_id, usage, performance)` - 结束追踪并收集性能
- `broadcast(type, data)` - WebSocket广播
- `get_performance_summary() -> dict` - 获取性能汇总
- `register_ws(ws_connection)` - 注册WebSocket连接
- `set_progress(current, total, current_node)` - 广播进度
- `get_node_metrics() / get_chapter_metrics() / get_total_metrics()` - 查询指标

**工具函数:**
- `log_event()`, `start_span()`, `end_span()`, `broadcast()`, `get_performance_summary()`

**成本计算公式:**
```
cost_usd = (prompt_tokens * input_price_per_million + completion_tokens * output_price_per_million) / 1_000_000
```

**文档更新:**
- `file_index.md`: 新增 observability.py 条目
- `tool_reference.md`: 新增 Observability 类完整文档

---# 变更日志

## 2026-04-09

### T8 - 记忆检索器实现

**新增文件:**
- `memory_store.py`: 记忆检索器

**功能:**
- 实现 `memory_retriever()` 纯 Python 检索函数（无 LLM 调用）
- 实现 `extract_keywords()` 简单分词函数
- 实现 `deduplicate()` 按 event_id 去重函数
- 实现 `truncate()` 按字符数截断函数
- 实现 `validate_token_overflow()` token 溢出验证函数
- 实现 `RetrievalMetrics` 性能指标收集类

**检索算法:**
1. 取 `global_memory["recent_detailed"]` 最近 `config.memory.recent_chapters` 章（默认 3）
2. 标签匹配：场景关键词 vs emotion_marks
3. 关系过滤：涉及场景中其他角色的记忆优先
4. 去重：按 event_id 去重
5. 硬截断到 `config.memory.truncation`（默认 2000 字符）

**输出 (AssembledContext):**
```python
{
    "character": "张三",
    "current_scene": {...},
    "retrieved_memories": [...],
    "memory_count": 3,
    "total_chars": 1500,
    "retrieval_time_ms": 12.5,
    "config_used": {"recent_chapters": 3, "truncation_limit": 2000}
}
```

**性能收集:**
- 检索耗时（retrieval_time_ms）
- 卡片数量（cards_retrieved）
- 返回字符数（chars_returned）

**触发 validation.token_overflow:**
- 当 estimated_tokens > max_tokens 时返回 True

**配置依赖 (config.yaml):**
```yaml
memory:
  truncation: 2000
  recent_chapters: 3
```

**文档更新:**
- `docs/file_index.md`: 新增 memory_store.py 条目
- `docs/tool_reference.md`: 新增 memory_retriever 使用说明

---# 变更日志

## 2026-04-09

### T9 - 角色分配器 LLM 节点实现

**新增函数:**
- `llm_nodes.py`: 新增 `role_assigner()` 函数
- `llm_nodes.py`: 新增 `_get_role_assigner_genre_instructions()` 辅助函数

**新增模型 (schemas.py):**
- `CurrentNodeInfo`: 当前节点信息
- `CharacterProfileData`: 角色档案数据
- `AssembledMemoryData`: 组装后的记忆数据
- `RelationshipMatrixData`: 关系矩阵数据
- `ItemStatusData`: 物品状态数据
- `RoleAssignerInput`: 角色分配器输入模型

**装饰器:**
- `@json_output`: 自动解析 JSON 输出
- `@validate_schema(schema_class=RoleAssignerOutput)`: 自动验证输出格式

**输入 (RoleAssignerInput):**
- `current_node`: 当前节点信息 (node_id, type, description, target_character)
- `character_profile`: 角色档案 (name, role, background, personality, goals, relationships)
- `assembled_memory`: 记忆信息 (long_term, short_term, recent_events)
- `relationship_matrix`: 关系矩阵
- `item_status`: 物品状态 (items, item_details)
- `genre`: 文体类型 (novel/script/game_story/dialogue/article)
- `current_situation`: 当前情境描述
- `goals`: 角色目标
- `constraints`: 行为约束列表

**输出 (RoleAssignerOutput):**
```json
{
    "target_character": "林深",
    "generation_prompt": {
        "identity": "你是林深，28岁侦探...",
        "long_term_memory": ["第3章被救", "第4章发现打火机"],
        "short_term_memory": ["本章试探陈默"],
        "recent_events": "你刚说完'这雨下得跟那天一样'",
        "current_situation": "陈默正在倒茶，右手挡在抽屉方向",
        "relationships": {"陈默": "信任45↓，表面朋友实际怀疑"},
        "items": ["父亲的怀表"],
        "goals": "获取信任假象，寻找证据",
        "constraints": ["禁止直接质问", "禁止表现出审问姿态"],
        "genre_hints": "novel：第三人称有限视角，心理描写丰富"
    }
}
```

**generation_prompt 结构说明:**
- `identity`: 角色身份描述，整合姓名、背景、性格
- `long_term_memory`: 长期记忆片段列表
- `short_term_memory`: 短期记忆片段列表
- `recent_events`: 最近事件描述
- `current_situation`: 当前情境描述
- `relationships`: 关系字典
- `items`: 当前持有的物品列表
- `goals`: 当前目标
- `constraints`: 行为约束列表
- `genre_hints`: 文体特定提示

**Genre 处理:**
- novel: 第三人称有限视角，心理描写丰富
- script: 场景镜头和对白格式
- game_story: 分支选择和状态机影响
- dialogue: 多轮对话和记忆累积
- article: 论点论据结构

**依赖:**
- KimiApiClient 单例
- @json_output 装饰器
- @validate_schema 装饰器
- RoleAssignerOutput 模型（schemas.py）
- MEMORY_RETRIEVER (用于获取记忆数据)

---

## 2026-04-09

### T11 - 自检 LLM 节点实现

**新增函数:**
- `llm_nodes.py`: 新增 `self_check()` 函数

**功能:**
- 实现 `self_check()` 自检函数
- 实现 `validate_loop_guard()` 重试次数验证函数
- 实现 `handle_revision_needed()` 分支处理函数

**装饰器:**
- `@json_output`: 自动解析 JSON 输出

**输入:**
- `director_general_standards`: 总导演标准（大纲/角色/伏笔等）
- `current_chapter_content`: 当前章节内容
- `global_memory_consistency`: 全局记忆一致性数据

**输出 (SelfCheckOutput):**
```json
{
    "needs_revision": true,
    "issue_types": ["一致性", "记忆"],
    "specific_issues": ["林深第5章已知照片裁剪，但反应过于平静"],
    "improvement_suggestions": "加强林深发现痕迹时的内心挣扎，增加回忆第3章被救的对比"
}
```

**分支逻辑:**
1. `needs_revision = True`:
   - 调用 `validate_loop_guard(retry_count, max_retries)` 检查重试次数
   - 未超限：返回 `{"action": "retry", "target": "DIRECTOR_CHAPTER", "feedback": improvement_suggestions}`
   - 已超限：返回 `{"action": "terminate", "reason": "max_retries_exceeded", "message": "请人工介入处理"}`
2. `needs_revision = False`: 继续下一章

**检查要点:**
1. 角色行为与角色设定一致性
2. 情节发展与章节大纲一致性
3. 角色关系变化与记忆一致性
4. 伏笔埋设和呼应
5. 情感转折合理性

**依赖:**
- KimiApiClient 单例
- @json_output 装饰器
- SelfCheckOutput 模型（schemas.py）
- DirectorChapterInput, DirectorChapterOutput（新增导入）

**文档更新:**
- `docs/file_index.md`: 更新 llm_nodes.py 条目

## 2026-04-09

### T6 - 总导演 LLM 节点实现

**新增文件:**
- `llm_nodes.py`: LLM 节点实现

**功能:**
- 实现 `director_general()` 函数
- 实现 `_get_genre_instructions()` 辅助函数（5种文体处理）
- 实现 `_save_global_memory()` 持久化函数

**装饰器:**
- `@json_output`: 自动解析 JSON 输出
- `@validate_schema(schema_class=DirectorGeneralOutput)`: 自动验证 schema

**输入 (DirectorGeneralInput):**
- theme: 小说主题
- style: 写作风格
- total_words: 目标总字数
- character_count: 角色数量
- genre: 文体类型

**Genre 类型处理:**

| genre | 处理指令 |
|-------|----------|
| novel | 强调章节结构和角色弧光 |
| script | 强调场景镜头和对白格式 |
| game_story | 强调分支选择和状态机 |
| dialogue | 强调多轮对话和记忆累积 |
| article | 强调论点论据结构 |

**性能指标:**
- ttf_ms: 首次响应时间
- tps: tokens per second
- api_latency_ms: API 延迟
- cost_usd: 预估成本

**持久化:**
- 自动保存到 `output/global_memory.json`
- 包含 _metadata.performance 和 _metadata.usage

**依赖:**
- KimiApiClient 单例（从 config.yaml 读取配置）
- decorators: json_output, validate_schema
- schemas: DirectorGeneralInput, DirectorGeneralOutput

**文档更新:**
- `docs/file_index.md`: 新增 llm_nodes.py 条目
- `docs/tool_reference.md`: 新增 director_general 使用说明

## 2026-04-09

### T7 - 记忆摘要器实现

**新增文件:**
- `llm_nodes.py`: LLM 节点实现

**功能:**
- 实现 `memory_summarizer()` 函数
- 实现 `_build_summarization_prompt()` 辅助函数
- 使用轻量模型 `kimi-k2-0905-preview` 降低成本

**输入:**
- `raw_memories`: List[RawMemory]，每个含 character, content, emotion

**输出:**
- `List[MemoryCard]`: 结构化记忆卡片数组

**MemoryCard 结构:**
- event_id: 事件ID（如 "E-5-1"）
- timestamp: 时间戳（如 "案发后第3天雨夜"）
- location: 发生地点
- core_action: 核心动作描述
- emotion_marks: 情感标记字典
- relationship_changes: 关系变化字典
- key_quote: 关键引言
- future_impacts: 未来影响事件ID列表
- source_index: 来源索引

**依赖:**
- KimiApiClient 单例
- @json_output 装饰器（无 @validate_schema，输出较灵活）
- RawMemory 模型（新增于 schemas.py）

**轻量模型切换:**
- 使用 `kimi-k2-0905-preview` 模型
- 在 config.yaml 中配置定价: input=1元/百万, output=5元/百万
- kimi_client.py 支持动态模型定价

**TODO:**
- 触发逻辑由 ChapterContext.exit 调用（T4 中预留）

**文档更新:**
- `schemas.py`: 新增 RawMemory 模型
- `config.yaml`: 新增 kimi-k2-0905-preview 定价
- `kimi_client.py`: 支持动态模型定价

### T5 - NodeSequence 迭代器实现

**新增文件:**
- `iterators.py`: 节点序列迭代器

**功能:**
- 实现 `NodeSequence` 迭代器类
- 支持 `__iter__`、`__next__` 协议
- 实现 `send(feedback)` 方法接收改进建议
- 重置 `current_index=0` 并递增 `retry_count`

**属性:**
- `current_index`: 当前迭代位置
- `retry_count`: 重试次数统计
- `node_sequence`: 存储的节点序列

**文档更新:**
- `docs/file_index.md`: 新增 iterators.py 条目
- `docs/tool_reference.md`: 新增 NodeSequence 使用说明

### T4 - ChapterContext 实现

**新增文件:**
- `context_managers.py`: 章节上下文管理器

**功能:**
- 实现 `ChapterContext` 上下文管理器
- 加载配置文件和全局记忆
- 管理章节临时目录
- 确保异常时资源清理

**TODO:**
- `context_managers.py` 第 45-47 行: memory_summarizer 调用预留接口，待 T7 实现

**文档更新:**
- `docs/file_index.md`: 新增 context_managers.py 条目
- `docs/tool_reference.md`: 新增 ChapterContext 使用说明
