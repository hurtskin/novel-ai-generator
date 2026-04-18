"""
RAG 增强型记忆存储实现

实现 MemoryStore 接口，提供基于向量检索的记忆存储功能
支持嵌入向量、相似度检索、上下文增强等 RAG 特性
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

from interfaces.memory import (
    MemoryStore,
    MemoryUpdate,
    CharacterMemory,
    RetrievalResult,
    RetrievalMetrics,
)

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """文本块元数据"""
    chapter_id: int
    node_id: str
    unit_type: str
    characters: List[str]
    location: str
    timeline: str
    emotions: List[str]
    keywords: List[str]
    timestamp: str


class EmbeddingClient:
    """
    嵌入服务客户端
    
    职责：
    - 调用嵌入 API 获取文本向量
    - 支持批量处理
    """

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        embedding_config = self._config.get("embedding", {})
        
        self.base_url = embedding_config.get("base_url", "https://cloud.infini-ai.com/maas")
        self.api_key = embedding_config.get("api_key", "")
        self.model = embedding_config.get("model", "bge-m3")
        self.dimensions = embedding_config.get("dimensions", 1024)
        self.batch_size = embedding_config.get("batch_size", 32)
        self.timeout = self._config.get("api", {}).get("timeout", 60)

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本的嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if isinstance(texts, str):
            texts = [texts]

        endpoint = f"{self.base_url}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": texts,
        }

        logger.info(f"[Embedding] Calling API: model={self.model}, texts_count={len(texts)}")

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"[Embedding] HTTP Error: {e}")
            raise

        result = response.json()
        embeddings = [item["embedding"] for item in result["data"]]
        return embeddings


class VectorStore:
    """
    向量存储
    
    职责：
    - 存储文本块和对应的嵌入向量
    - 支持相似度检索
    - 持久化到 JSON 文件
    """

    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = persist_directory
        self.chunks: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadatas: List[Dict[str, Any]] = []
        self._load()

    def _get_index_path(self) -> str:
        """获取索引文件路径"""
        return os.path.join(self.persist_directory, "index.json")

    def _load(self) -> None:
        """从文件加载向量数据"""
        index_file = self._get_index_path()
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.embeddings = data.get("embeddings", [])
                    self.metadatas = data.get("metadatas", [])
                logger.info(f"Loaded vector store from {index_file}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")

    def save(self) -> None:
        """保存向量数据到文件"""
        os.makedirs(self.persist_directory, exist_ok=True)
        index_file = self._get_index_path()
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": self.chunks,
                    "embeddings": self.embeddings,
                    "metadatas": self.metadatas,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def add(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        添加文本块和嵌入向量
        
        Args:
            chunks: 文本块列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列表
        """
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)
        self.save()

    def clear(self) -> None:
        """清空所有数据"""
        self.chunks = []
        self.embeddings = []
        self.metadatas = []
        self.save()

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[int, float]]:
        """
        搜索相似向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            List[Tuple[int, float]]: (索引, 相似度) 列表
        """
        if not self.embeddings:
            return []

        scores = []
        for i, emb in enumerate(self.embeddings):
            # 元数据过滤
            if filter_metadata:
                meta = self.metadatas[i]
                match = all(meta.get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue
            
            # 计算余弦相似度
            score = self._cosine_similarity(query_embedding, emb)
            scores.append((i, score))

        # 按相似度排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def count(self) -> int:
        """获取存储的文本块数量"""
        return len(self.chunks)


class RAGMemoryStore(MemoryStore):
    """
    RAG 增强型记忆存储实现
    
    功能特性：
    - 基于向量相似度的记忆检索
    - 支持文本嵌入和语义搜索
    - 自动文本分块
    - 支持元数据过滤
    - 与 SimpleMemoryStore 兼容的 API
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 RAG 记忆存储
        
        Args:
            config_path: 配置文件路径
        """
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        
        # 初始化组件
        self._embedding_client = EmbeddingClient(self._config_path)
        vector_store_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "vector_store"
        )
        self._vector_store = VectorStore(vector_store_path)
        
        # 分块配置
        self._chunk_size = 500
        self._chunk_overlap = 50
        self._max_results = 5
        self._similarity_threshold = 0.5
        
        # 基础记忆存储（用于兼容非 RAG 功能）
        self._base_memory: Dict[str, Any] = {}
        self._global_memory_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "global_memory.json"
        )
        self._load_base_memory()

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_base_memory(self) -> None:
        """加载基础记忆数据"""
        if os.path.exists(self._global_memory_path):
            try:
                with open(self._global_memory_path, "r", encoding="utf-8") as f:
                    self._base_memory = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load base memory: {e}")
                self._base_memory = {}

    def _save_base_memory(self) -> None:
        """保存基础记忆数据"""
        try:
            with open(self._global_memory_path, "w", encoding="utf-8") as f:
                json.dump(self._base_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save base memory: {e}")

    def _chunk_text(self, text: str) -> List[str]:
        """
        将文本分块
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 文本块列表
        """
        if len(text) <= self._chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            if end < len(text):
                # 在句子边界处分割
                last_period = text.rfind("。", start, end)
                last_newline = text.rfind("\n", start, end)
                split_pos = max(last_period, last_newline)
                if split_pos > start:
                    end = split_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self._chunk_overlap if end - self._chunk_overlap > start else end

        return chunks

    def ingest(
        self,
        content: str,
        chapter_id: int,
        node_id: str,
        unit_type: str,
        characters: List[str],
        location: str = "",
        timeline: str = "",
        emotions: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        将内容添加到 RAG 存储
        
        Args:
            content: 文本内容
            chapter_id: 章节 ID
            node_id: 节点 ID
            unit_type: 单元类型
            characters: 相关角色列表
            location: 地点
            timeline: 时间线
            emotions: 情感标签
            keywords: 关键词
            
        Returns:
            Dict[str, Any]: 索引状态信息
        """
        if emotions is None:
            emotions = []
        if keywords is None:
            keywords = []

        # 分块
        chunks = self._chunk_text(content)
        
        # 生成元数据
        metadatas = [
            {
                "chapter_id": chapter_id,
                "node_id": node_id,
                "unit_type": unit_type,
                "characters": characters,
                "location": location,
                "timeline": timeline,
                "emotions": emotions,
                "keywords": keywords,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for _ in chunks
        ]

        if not chunks:
            return {"index_status": False, "chunk_id": "", "chunk_size": 0}

        # 获取嵌入向量
        embeddings = self._embedding_client.embed(chunks)
        
        # 添加到向量存储
        self._vector_store.add(chunks, embeddings, metadatas)

        chunk_id = f"{node_id}_0"
        return {
            "index_status": True,
            "chunk_id": chunk_id,
            "chunk_size": len(chunks),
        }

    def retrieve(
        self,
        queries: List[str],
        chapter_id: Optional[int] = None,
        top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        基于向量相似度检索记忆
        
        Args:
            queries: 查询文本列表
            chapter_id: 章节 ID 过滤
            top_k: 返回结果数量
            
        Returns:
            Tuple[List[Dict], Dict]: (检索结果, 指标)
        """
        start_time = time.time()
        all_results: Dict[int, float] = {}

        for query in queries:
            query_embedding = self._embedding_client.embed([query])[0]
            
            # 元数据过滤
            filter_meta = {}
            if chapter_id is not None:
                filter_meta["chapter_id"] = chapter_id

            # 搜索
            raw_results = self._vector_store.search(
                query_embedding,
                top_k=self._max_results * 2,
                filter_metadata=filter_meta if filter_meta else None,
            )

            # 合并结果（取最高相似度）
            for idx, score in raw_results:
                if score < self._similarity_threshold:
                    continue
                if idx in all_results:
                    all_results[idx] = max(all_results[idx], score)
                else:
                    all_results[idx] = score

        # 排序并构建结果
        sorted_indices = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in sorted_indices[:top_k]:
            meta = self._vector_store.metadatas[idx]
            results.append({
                "content": self._vector_store.chunks[idx],
                "chunk_id": f"{meta.get('node_id', '')}_{idx}",
                "score": score,
                "metadata": ChunkMetadata(
                    chapter_id=meta.get("chapter_id", 0),
                    node_id=meta.get("node_id", ""),
                    unit_type=meta.get("unit_type", ""),
                    characters=meta.get("characters", []),
                    location=meta.get("location", ""),
                    timeline=meta.get("timeline", ""),
                    emotions=meta.get("emotions", []),
                    keywords=meta.get("keywords", []),
                    timestamp=meta.get("timestamp", ""),
                ),
                "source_type": meta.get("unit_type", ""),
            })

        query_time_ms = int((time.time() - start_time) * 1000)
        metrics = {
            "query_time_ms": query_time_ms,
            "total_hits": len(all_results),
            "returned_results": len(results),
        }

        return results, metrics

    def generate_queries(
        self,
        current_node: Dict[str, Any],
        character_profile: Dict[str, Any],
        scene_context: str,
    ) -> List[str]:
        """
        生成检索查询
        
        Args:
            current_node: 当前节点信息
            character_profile: 角色档案
            scene_context: 场景上下文
            
        Returns:
            List[str]: 查询列表
        """
        node_type = current_node.get("type", "narrator")
        character_name = character_profile.get("name", "")
        character_role = character_profile.get("role", "")

        queries = []

        # 语义查询
        semantic_query = f"{scene_context}"
        if character_name:
            semantic_query += f" {character_name}"
        queries.append(semantic_query)

        # 关键词查询
        if character_name:
            keyword_query = f"{character_name} {node_type}"
            queries.append(keyword_query)

        if scene_context:
            queries.append(scene_context)

        return queries

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_chunks": self._vector_store.count(),
            "persist_directory": self._vector_store.persist_directory,
        }

    # MemoryStore 接口实现

    def get_character_memory(self, character_name: str) -> Optional[CharacterMemory]:
        """获取角色记忆"""
        characters = self._base_memory.get("characters", {})
        char_data = characters.get(character_name)
        
        if char_data is None:
            return None
        
        return CharacterMemory(
            character_name=character_name,
            memories=char_data.get("memories", []),
            emotions=char_data.get("emotions", []),
            relationships=char_data.get("relationships", {}),
        )

    def update_memory(self, memory_update: MemoryUpdate) -> None:
        """更新记忆"""
        target_character = memory_update.target_character
        if not target_character:
            return

        if "characters" not in self._base_memory:
            self._base_memory["characters"] = {}

        if target_character not in self._base_memory["characters"]:
            self._base_memory["characters"][target_character] = {
                "memories": [],
                "emotions": [],
                "relationships": {},
            }

        char_data = self._base_memory["characters"][target_character]

        for memory_text in memory_update.new_memories:
            memory_entry = {
                "chapter_id": memory_update.chapter_id,
                "node_id": memory_update.node_id,
                "content": memory_text,
                "timestamp": f"chapter_{memory_update.chapter_id}_node_{memory_update.node_id}",
            }
            char_data["memories"].append(memory_entry)

        if memory_update.emotion_shift:
            char_data["emotions"].append({
                "chapter_id": memory_update.chapter_id,
                "node_id": memory_update.node_id,
                "shift": memory_update.emotion_shift,
            })

        if memory_update.relationship_updates:
            for other_char, updates in memory_update.relationship_updates.items():
                if "relationships" not in char_data:
                    char_data["relationships"] = {}
                if other_char not in char_data["relationships"]:
                    char_data["relationships"][other_char] = {}
                char_data["relationships"][other_char].update(updates)

        self._save_base_memory()

    def get_global_memory(self) -> Dict[str, Any]:
        """获取全局记忆"""
        return self._base_memory

    def save_global_memory(self, memory: Dict[str, Any]) -> None:
        """保存全局记忆"""
        self._base_memory = memory
        self._save_base_memory()

    def get_chapter_memory(self, chapter_id: int) -> Dict[str, Any]:
        """获取章节记忆"""
        # RAG 存储通过元数据过滤实现章节隔离
        return {"chapter_id": chapter_id, "vector_store": self._vector_store.count()}

    def save_chapter_memory(self, chapter_id: int, memory: Dict[str, Any]) -> None:
        """保存章节记忆"""
        # RAG 存储通过 ingest 方法添加内容
        pass

    def clear_character_memory(self, character_name: str) -> None:
        """清空角色记忆"""
        if "characters" in self._base_memory:
            if character_name in self._base_memory["characters"]:
                del self._base_memory["characters"][character_name]
                self._save_base_memory()

    def clear(self) -> None:
        """清空所有记忆数据"""
        self._base_memory = {}
        self._save_base_memory()
        if self._vector_store:
            self._vector_store.clear()
        logger.info("RAG memory store cleared")

    def add_memory(self, content: str, metadata: Dict[str, Any]) -> None:
        """添加记忆（兼容 RAG 接口）"""
        # 将内容分块并添加到向量存储
        chunks = self._chunk_text(content)
        if not chunks:
            return
        
        # 获取嵌入向量
        embeddings = self._embedding_client.embed(chunks)
        
        # 构建元数据列表
        metadatas = [
            {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for i in range(len(chunks))
        ]
        
        # 添加到向量存储
        self._vector_store.add(chunks, embeddings, metadatas)
        logger.debug(f"Added memory to RAG: {content[:50]}...")

    def get_all_characters(self) -> List[str]:
        """获取所有角色名称列表"""
        characters = self._base_memory.get("characters", {})
        return list(characters.keys())

    def truncate_memories(
        self,
        memories: List[Dict[str, Any]],
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """截断记忆列表"""
        if max_chars <= 0:
            return []

        result = []
        total_chars = 0

        for card in memories:
            card_str = json.dumps(card, ensure_ascii=False)
            card_chars = len(card_str)

            if total_chars + card_chars <= max_chars:
                result.append(card)
                total_chars += card_chars
            else:
                break

        return result

    def deduplicate_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重记忆列表"""
        seen_ids = set()
        result = []
        for card in memories:
            event_id = card.get("event_id", "") or card.get("chunk_id", "")
            if event_id not in seen_ids:
                seen_ids.add(event_id)
                result.append(card)
        return result
