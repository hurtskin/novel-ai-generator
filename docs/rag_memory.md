# RAG 记忆系统

## 概述

RAG（Retrieval-Augmented Generation）记忆系统用于实时保存每个单元生成的内容，并通过向量检索增强角色分配的上下文理解。

## 配置

### config.yaml

```yaml
embedding:
  api_key: <your-api-key>
  base_url: https://cloud.infini-ai.com/maas
  model: bge-m3
  dimensions: 1024
  batch_size: 32
```

| 配置项 | 说明 |
|--------|------|
| api_key | Embedding API 密钥 |
| base_url | Embedding API 地址 |
| model | 向量化模型名称 |
| dimensions | 向量维度 |
| batch_size | 批量大小 |

## 核心类

### EmbeddingClient

向量化客户端，负责调用外部 API 将文本转换为向量。

```python
from rag_memory import EmbeddingClient

client = EmbeddingClient()
embeddings = client.embed(["文本内容"])
```

### VectorStore

向量存储类，负责本地向量数据的存储和检索。

```python
from rag_memory import VectorStore

store = VectorStore("./vector_store")
store.add(chunks, embeddings, metadatas)
results = store.search(query_embedding, top_k=5)
```

### RagMemorySystem

RAG 记忆系统主类，整合 EmbeddingClient 和 VectorStore。

```python
from rag_memory import RagMemorySystem, get_rag_memory_system

rag = get_rag_memory_system()
```

## 外部调用方法

### add_chunks

添加已分块的文本到向量库。

```python
from rag_memory import add_chunks

result = add_chunks(
    chunks=["文本块1", "文本块2"],
    metadata={
        "chapter_id": 1,
        "node_id": "ch1_node1",
        "unit_type": "narrator",
        "characters": ["角色A"],
        "location": "地点",
        "timeline": "时间",
        "emotions": ["情感"],
        "keywords": ["关键词"]
    }
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| chunks | list[str] | 已分块的文本列表 |
| metadata | dict | 元数据字典 |

返回：
```python
{"index_status": True, "chunk_count": 2}
```

### search

检索相关内容。

```python
from rag_memory import search

results = search(query="检索内容", chapter_id=1, top_k=5)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| query | str | 检索语句 |
| chapter_id | int (可选) | 过滤章节 |
| top_k | int | 返回结果数，默认 5 |

返回 `RetrievalResult` 列表：
```python
results[0].content      # 检索到的内容
results[0].score        # 相似度分数
results[0].metadata    # 元数据 (ChunkMetadata)
```

## 数据结构

### ChunkMetadata

```python
@dataclass
class ChunkMetadata:
    chapter_id: int          # 章节ID
    node_id: str            # 节点ID
    unit_type: str         # 单元类型
    characters: list[str]  # 涉及角色
    location: str          # 地点
    timeline: str          # 时间线
    emotions: list[str]    # 情感标签
    keywords: list[str]    # 关键词
    timestamp: str        # 时间戳
```

### RetrievalResult

```python
@dataclass
class RetrievalResult:
    content: str            # 检索内容
    chunk_id: str          # 向量ID
    score: float           # 相似度分数
    metadata: ChunkMetadata
    source_type: str       # 来源类型
```

## 特性

1. **每次启动清空**：新进程启动时向量库为空，不加载历史数据
2. **单例模式**：EmbeddingClient、RagMemorySystem 采用单例模式
3. **本地持久化**：向量数据保存在 `./vector_store/index.json`
4. **相似度检索**：使用余弦相似度计算

## 使用流程

1. **索引阶段**：每个单元生成后，调用 `add_chunks()` 存入向量库
2. **检索阶段**：角色分配前，调用 `search()` 检索相关历史内容
3. **组装提示词**：将检索结果融入角色分配的 prompt 中
