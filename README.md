# Novel AI Generator

基于多智能体协作的小说生成系统，采用面向接口架构设计，支持多种 LLM 后端、RAG 记忆检索和实时流式输出。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Tauri + React)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  ChatPanel  │ │ ProgressPanel│ │ SettingsPanel│ │ DebugPanel ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket / HTTP
┌─────────────────────────────────────────────────────────────────┐
│                          API 层 (FastAPI)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ /api/start  │ │ /api/stream │ │/api/regenerate│ │ /api/snapshots│
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        服务层 (Services)                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │ NovelGenerator  │ │  StateManager   │ │ SnapshotManager │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        核心层 (Core)                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Nodes     │ │  Iterators  │ │   Context   │ │  Container  ││
│  │(LLM 节点)   │ │(章节/节点迭代)│ │ (章节上下文) │ │ (依赖注入)  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ 依赖接口
┌─────────────────────────────────────────────────────────────────┐
│                      接口层 (Interfaces)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │LLMClient │ │MemoryStore│ │Observability│ │Storage │ │Embedding│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    实现层 (Implementations)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Moonshot │ │  Ollama  │ │  RAG     │ │  File    │ │ Infini │ │
│  │  Client  │ │  Client  │ │ Memory   │ │ Backend  │ │Embedding│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 核心特性

### 多智能体协作架构
- **总导演节点** (DirectorGeneral): 生成完整作品大纲、世界观、角色设定
- **章节导演节点** (DirectorChapter): 规划章节结构和节点序列
- **角色分配器** (RoleAssigner): 根据上下文组装角色扮演提示词
- **角色演员节点** (RoleActor): 生成具体文本内容
- **自检节点** (SelfCheck): 内容质量审查
- **文本润色节点** (TextPolisher): 章节最终润色

### 六种单元类型
| 类型 | 职责 |
|------|------|
| narrator | 旁白叙事、时间推进、背景交代 |
| environment | 环境描写、空间场景、氛围渲染 |
| action | 动作描写、表情细节、肢体语言 |
| dialogue | 角色对话、台词内容、说话方式 |
| psychology | 角色心理、内心独白、情绪波动 |
| conflict | 冲突悬念、矛盾升级、危机设置 |

### 技术特性
- **依赖注入容器**: 完整的 DI 容器，支持生命周期管理、自动注入
- **面向接口编程**: 业务逻辑与具体实现解耦，易于测试和扩展
- **RAG 记忆检索**: 基于向量相似度的历史内容检索
- **实时流式输出**: WebSocket 实时推送生成进度
- **可观测性**: 分布式追踪、性能指标、成本统计
- **多后端支持**: Moonshot、Ollama 等多种 LLM 后端

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+ (前端开发)
- Rust (Tauri 桌面应用)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd novel

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd novel_ai
npm install
```

### 配置

复制示例配置文件并修改：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：

```yaml
api:
  provider: moonshot              # 或 ollama
  model: kimi-k2
  api_key: your-api-key
  base_url: https://api.moonshot.cn/v1
  max_retries: 5
  timeout: 180

generation:
  mock_mode: false                # 设为 true 启用模拟模式
  temperature: 0.8
  max_tokens: 8192
  debug: true

embedding:
  api_key: your-embedding-key
  base_url: https://cloud.infini-ai.com/maas
  model: bge-m3
  dimensions: 1024
```

### 启动服务

```bash
# 启动后端服务
python main.py

# 启动前端开发服务器
cd novel_ai
npm run dev

# 构建桌面应用
npm run tauri build
```

## 项目结构

```
novel/
├── main.py                      # 应用入口
├── config.yaml                  # 配置文件
├── config.example.yaml          # 配置示例
├── interfaces/                  # 抽象接口层
│   ├── llm_client.py           # LLM 客户端接口
│   ├── memory.py               # 记忆存储接口
│   ├── observability.py        # 可观测性接口
│   ├── config.py               # 配置接口
│   ├── storage.py              # 存储接口
│   └── embedding.py            # 嵌入服务接口
├── implementations/             # 接口实现层
│   ├── llm/                    # LLM 实现
│   ├── memory/                 # 记忆实现
│   ├── observability/          # 可观测性实现
│   ├── storage/                # 存储实现
│   ├── embedding/              # 嵌入实现
│   └── config/                 # 配置实现
├── core/                        # 核心业务逻辑
│   ├── container.py            # 依赖注入容器
│   ├── container_config.py     # 容器配置
│   ├── nodes/                  # LLM 节点
│   ├── iterators/              # 迭代器
│   └── context/                # 上下文管理
├── services/                    # 应用服务层
│   ├── novel_generator.py      # 小说生成服务
│   ├── state_manager.py        # 状态管理
│   └── snapshot_manager.py     # 快照管理
├── api/                         # API 层
│   ├── app.py                  # FastAPI 应用
│   ├── dependencies.py         # 依赖注入
│   └── routes/                 # 路由
├── schemas/                     # 数据模型
├── utils/                       # 工具函数
├── docs/                        # 文档
└── novel_ai/                    # Tauri + React 前端
    ├── src/                    # React 源码
    └── src-tauri/              # Tauri 后端
```

## API 参考

### HTTP 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/start` | POST | 启动生成任务 |
| `/api/status` | GET | 获取生成状态 |
| `/api/pause` | POST | 暂停生成 |
| `/api/resume` | POST | 恢复生成 |
| `/api/stop` | POST | 停止生成 |
| `/api/regenerate` | POST | 重新生成指定节点 |
| `/api/retry_node` | POST | 重试当前节点 |
| `/api/snapshots` | GET/POST | 快照管理 |

### WebSocket 端点

| 端点 | 描述 |
|------|------|
| `/api/stream` | 实时流式通信 |

**消息类型**:
- `token`: 流式 token
- `progress`: 进度更新
- `status`: 状态变化
- `need_manual_review`: 需要人工干预
- `complete`: 生成完成

## 生成流程

```
用户输入
    ↓
DirectorGeneral (总导演规划)
    ↓
ChapterIterator (章节循环)
    ↓
DirectorChapter (章节导演)
    ↓
NodeSequence (节点循环)
    ↓
RoleAssigner → RAG Search → RoleActor
    ↓
SelfCheck (质量审查)
    ↓
[通过] → 保存 → 下一节点
[失败] → 重试 / 人工干预
    ↓
TextPolisher (章节润色)
    ↓
输出文件
```

## 配置说明

### API 配置
```yaml
api:
  provider: moonshot              # LLM 提供商
  model: kimi-k2                  # 模型名称
  api_key: your-key               # API 密钥
  base_url: https://api.moonshot.cn/v1
  max_retries: 5                  # 最大重试次数
  timeout: 180                    # 超时时间（秒）
```

### 生成配置
```yaml
generation:
  mock_mode: false                # 模拟模式
  temperature: 0.8               # 温度参数
  top_p: 0.95                    # Top-p 采样
  max_tokens: 8192               # 最大 token 数
  debug: true                    # 调试模式
```

### 记忆配置
```yaml
memory:
  per_chapter: 5000              # 每章节记忆上限
  max_total: 20000               # 总记忆上限
  truncation_strategy: keep_first # 截断策略
```

### 性能配置
```yaml
performance:
  cost_alert_usd: 5              # 成本告警阈值（美元）
```

## 文档索引

- [API 规范](docs/api_spec.md) - HTTP API 和 Pydantic 模型详细说明
- [接口规范](docs/interface_spec.md) - 抽象接口层设计规范
- [容器指南](docs/container_guide.md) - 依赖注入容器使用指南
- [LLM 节点索引](docs/llm_node_index.md) - 所有 LLM 节点的提示词和 Schema
- [RAG 记忆系统](docs/rag_memory.md) - 向量检索记忆系统说明
- [文件索引](docs/file_index.md) - 项目文件结构说明
- [变量字典](docs/variable_dict.md) - 系统变量参考
- [工具参考](docs/tool_reference.md) - 工具类使用手册
- [变更日志](docs/change_log.md) - 版本更新记录
- [重构报告](docs/refactor_completion_report.md) - 面向接口重构完成报告

## 开发指南

### 添加新的 LLM 后端

1. 在 `interfaces/llm_client.py` 中定义接口（已存在）
2. 在 `implementations/llm/` 中创建实现类
3. 在 `implementations/llm/factory.py` 中注册工厂

示例：

```python
# implementations/llm/my_llm.py
from interfaces.llm_client import LLMClient, ChatMessage, ChatResponse

class MyLLMClient(LLMClient):
    def chat(self, messages, **kwargs) -> ChatResponse:
        # 实现 LLM 调用逻辑
        pass
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_container.py
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至 <your-email@example.com>
