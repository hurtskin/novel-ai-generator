# RAG 记忆系统

> 本文档介绍 Novel AI Generator 的 RAG（Retrieval-Augmented Generation）记忆系统
> 版本: 2.0.0
> 更新日期: 2026-04-19

---

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [配置说明](#配置说明)
4. [核心组件](#核心组件)
5. [使用方法](#使用方法)
6. [数据结构](#数据结构)
7. [最佳实践](#最佳实践)

---

## 概述

RAG 记忆系统用于实时保存每个单元生成的内容，并通过向量相似度检索增强角色分配的上下文理解。

### 核心功能

- **文本向量化**: 使用 Embedding API 将文本转换为高维向量
- **向量存储**: 本地 JSON 文件持久化存储
- **相似度检索**: 基于余弦相似度的相关内容检索
- **元数据管理**: 支持丰富的元数据过滤

### 工作流程

```
生成内容
    ↓
文本分块 (Chunking)
    ↓
向量化 (Embedding)
    ↓
存储到向量库 (Vector Store)
    ↓
角色分配时检索 (Search)
    ↓
组装到 Prompt (Context Enhancement)
```

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    RAG Memory System                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Embedding  │  │ VectorStore  │  │   Search     │  │
│  │   Client     │  │              │  │   Engine     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│              External Services / Storage                 │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │ InfiniAI API     │  │ Local JSON File Storage    │  │
│  │ (bge-m3 model)   │  │ ./vector_store/index.json  │  │
│  └──────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 配置说明

### config.yaml

```yaml
embedding:
  api_key: your-embedding-api-key
  base_url: https://cloud.infini-ai.com/maas
  model: bge-m3
  dimensions: 1024
  batch_size: 32
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| api_key | string | - | Embedding API 密钥 |
| base_url | string | - | Embedding API 地址 |
| model | string | bge-m3 | 向量化模型名称 |
| dimensions | integer | 1024 | 向量维度 |
| batch_size | integer | 32 | 批量处理大小 |

### 模型说明

**bge-m3** (BAAI General Embedding - Multi-lingual, Multi-function, Multi-granularity)

- 支持多语言（100+ 语言）
- 向量维度: 1024
- 支持长文本（最大 8192 tokens）
- 适用于语义检索和 RAG 应用

---

## 核心组件

### EmbeddingClient

向量化客户端，负责调用外部 API 将文本转换为向量。

```python
from interfaces.embedding import EmbeddingClient

class InfiniEmbeddingClient(EmbeddingClient):
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表，每个向量是 1024 维浮点数数组
        """
        pass
    
    def embed_single(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        pass
```

### VectorStore

向量存储类，负责本地向量数据的存储和检索。

```python
from interfaces.embedding import VectorStore, RetrievalResult

class SimpleVectorStore(VectorStore):
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """添加向量数据"""
        pass
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        相似度检索
        
        使用余弦相似度计算查询向量与存储向量的相似度
        """
        pass
    
    def clear(self) -> None:
        """清空所有数据"""
        pass
```

### RAGMemorySystem

RAG 记忆系统主类，整合 EmbeddingClient 和 VectorStore。

```python
from implementations.memory.rag_memory_store import RAGMemorySystem

# 获取单例实例
rag_system = container.resolve(MemoryStore)  # 返回 RAGMemoryStore
```

---

## 使用方法

### 添加内容到向量库

```python
from implementations.memory.rag_memory_store import add_chunks

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

**参数说明**:

| 参数 | 类型 | 说明 |
|------|------|------|
| chunks | List[str] | 已分块的文本列表 |
| metadata | Dict | 元数据字典 |

**返回**:

```python
{
    "index_status": True,
    "chunk_count": 2
}
```

### 检索相关内容

```python
from implementations.memory.rag_memory_store import search

results = search(
    query="角色A的心理活动",
    chapter_id=1,
    top_k=5
)
```

**参数说明**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| query | str | - | 检索查询语句 |
| chapter_id | int | None | 过滤章节ID |
| top_k | int | 5 | 返回结果数量 |

**返回** `List[RetrievalResult]`:

```python
[
    RetrievalResult(
        content="检索到的文本内容",
        chunk_id="chunk_001",
        score=0.89,  # 相似度分数 0-1
        metadata=ChunkMetadata(
            chapter_id=1,
            node_id="ch1_node1",
            unit_type="psychology",
            characters=["角色A"],
            location="教室",
            timeline="上午",
            emotions=["紧张"],
            keywords=["考试", "压力"]
        ),
        source_type="rag"
    )
]
```

### 在角色分配中使用

```python
# 在 role_assigner 节点中
from implementations.memory.rag_memory_store import search

# 检索相关历史内容
retrieval_results = search(
    query=f"{target_character} 的情感和经历",
    chapter_id=current_chapter,
    top_k=3
)

# 组装到 prompt
context_parts = []
for result in retrieval_results:
    context_parts.append(f"[{result.metadata.unit_type}] {result.content}")

long_term_memory = "\n".join(context_parts)
```

---

## 数据结构

### ChunkMetadata

```python
@dataclass
class ChunkMetadata:
    chapter_id: int          # 章节ID
    node_id: str            # 节点ID
    unit_type: str         # 单元类型 (narrator/environment/action/dialogue/psychology/conflict)
    characters: List[str]  # 涉及角色
    location: str          # 地点
    timeline: str          # 时间线
    emotions: List[str]    # 情感标签
    keywords: List[str]    # 关键词
    timestamp: str        # 时间戳 ISO格式
```

### RetrievalResult

```python
@dataclass
class RetrievalResult:
    content: str            # 检索内容
    chunk_id: str          # 向量ID
    score: float           # 相似度分数 (0-1)
    metadata: ChunkMetadata
    source_type: str       # 来源类型 (rag/memory)
```

### VectorRecord

```python
@dataclass
class VectorRecord:
    id: str                # 唯一ID
    text: str             # 原始文本
    embedding: List[float] # 向量
    metadata: ChunkMetadata
    created_at: str       # 创建时间
```

---

## 最佳实践

### 1. 分块策略

```python
# 根据单元类型选择合适的分块大小
CHUNK_SIZES = {
    "narrator": 500,      # 旁白可以较长
    "dialogue": 200,      # 对话保持完整
    "psychology": 300,    # 心理活动适中
    "action": 250,        # 动作描写
    "environment": 400,   # 环境描写
    "conflict": 350       # 冲突场景
}

def chunk_text(text: str, unit_type: str) -> List[str]:
    size = CHUNK_SIZES.get(unit_type, 300)
    # 实现分块逻辑
    return chunks
```

### 2. 元数据丰富度

```python
# 尽可能丰富元数据，便于后续过滤
metadata = {
    "chapter_id": chapter_id,
    "node_id": node_id,
    "unit_type": unit_type,
    "characters": extract_characters(content),  # 提取涉及角色
    "location": extract_location(content),      # 提取地点
    "timeline": extract_timeline(content),      # 提取时间
    "emotions": extract_emotions(content),      # 提取情感
    "keywords": extract_keywords(content)       # 提取关键词
}
```

### 3. 检索优化

```python
# 组合多个检索条件
def enhanced_search(character: str, situation: str, chapter_id: int):
    # 1. 角色相关检索
    char_results = search(
        query=f"{character} 的经历",
        chapter_id=chapter_id,
        top_k=3
    )
    
    # 2. 情境相关检索
    sit_results = search(
        query=situation,
        chapter_id=chapter_id,
        top_k=2
    )
    
    # 3. 合并去重
    all_results = char_results + sit_results
    seen = set()
    unique_results = []
    for r in all_results:
        if r.chunk_id not in seen:
            seen.add(r.chunk_id)
            unique_results.append(r)
    
    return sorted(unique_results, key=lambda x: x.score, reverse=True)[:5]
```

### 4. 相似度阈值

```python
# 设置相似度阈值过滤低质量结果
SIMILARITY_THRESHOLD = 0.6

def filtered_search(query: str, **kwargs) -> List[RetrievalResult]:
    results = search(query, **kwargs)
    return [r for r in results if r.score >= SIMILARITY_THRESHOLD]
```

---

## 存储格式

向量数据以 JSON 格式存储在 `./vector_store/index.json`：

```json
{
  "vectors": [
    {
      "id": "chunk_001",
      "text": "文本内容...",
      "embedding": [0.1, 0.2, 0.3, ...],
      "metadata": {
        "chapter_id": 1,
        "node_id": "ch1_node1",
        "unit_type": "dialogue",
        "characters": ["角色A"],
        "location": "教室",
        "timeline": "上午",
        "emotions": ["紧张"],
        "keywords": ["考试"],
        "timestamp": "2026-04-19T10:00:00Z"
      },
      "created_at": "2026-04-19T10:00:00Z"
    }
  ],
  "metadata": {
    "version": "2.0.0",
    "total_vectors": 100,
    "last_updated": "2026-04-19T10:00:00Z"
  }
}
```

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2026-04-19 | 重构后更新，实现接口抽象 |
| 1.1.0 | 2026-04-13 | 添加元数据过滤功能 |
| 1.0.0 | 2026-04-10 | 初始版本 |
