"""
Infini 嵌入客户端实现

实现 EmbeddingClient 接口，提供与 Infini 嵌入服务的交互功能
支持文本向量化、嵌入模型加载和嵌入向量计算
"""

import hashlib
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from interfaces.embedding import (
    EmbeddingClient,
    VectorStore,
    SearchResult,
    ChunkMetadata,
)

logger = logging.getLogger(__name__)


class InfiniEmbeddingClient(EmbeddingClient):
    """
    Infini 嵌入客户端实现
    
    功能特性：
    - 文本向量化
    - 支持批量处理
    - 可配置的嵌入维度
    - 支持多种嵌入模型
    
    注意：当前使用模拟实现，实际使用时需要替换为真实的 Infini API 调用
    """

    def __init__(
        self,
        model: str = "infini-embedding-v1",
        dimensions: int = 768,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化 Infini 嵌入客户端
        
        Args:
            model: 嵌入模型名称
            dimensions: 嵌入维度
            api_key: API 密钥
            base_url: API 基础 URL
        """
        self._model = model
        self._dimensions = dimensions
        self._api_key = api_key or os.getenv("INFINI_API_KEY", "")
        self._base_url = base_url or "https://api.infini-ai.com/v1"
        
        logger.info(f"Initialized InfiniEmbeddingClient with model: {model}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
            
        注意：当前使用模拟实现，基于文本哈希生成确定性向量
        """
        return [self.embed_single(text) for text in texts]

    def embed_single(self, text: str) -> List[float]:
        """
        将单个文本转换为嵌入向量
        
        Args:
            text: 文本
            
        Returns:
            List[float]: 嵌入向量
            
        注意：当前使用模拟实现，基于文本哈希生成确定性向量
        """
        # 使用文本哈希生成确定性向量（模拟实现）
        # 实际使用时替换为真实的 API 调用
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        # 基于哈希生成向量
        vector = []
        for i in range(self._dimensions):
            # 使用哈希字节生成 [-1, 1] 范围内的值
            byte_val = hash_bytes[i % len(hash_bytes)]
            # 添加一些随机性但保持确定性
            seed = (byte_val + i * 31) % 256
            val = (seed / 128.0) - 1.0
            vector.append(val)
        
        # 归一化向量
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector

    def get_dimensions(self) -> int:
        """获取嵌入维度"""
        return self._dimensions

    def get_model(self) -> str:
        """获取模型名称"""
        return self._model


class SimpleVectorStore(VectorStore):
    """
    简单向量存储实现
    
    功能特性：
    - 内存中存储文本块和嵌入向量
    - 支持余弦相似度搜索
    - 支持元数据过滤
    - 持久化到 JSON 文件
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化向量存储
        
        Args:
            storage_path: 存储文件路径，None 则不持久化
        """
        self._storage_path = storage_path
        self._chunks: List[str] = []
        self._embeddings: List[List[float]] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._chunk_ids: List[str] = []
        
        # 加载已有数据
        if storage_path and os.path.exists(storage_path):
            self.load()

    def add(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        添加文本块到存储
        
        Args:
            chunks: 文本块列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列表
        """
        if not (len(chunks) == len(embeddings) == len(metadatas)):
            raise ValueError("chunks, embeddings, and metadatas must have the same length")
        
        for i, (chunk, embedding, metadata) in enumerate(zip(chunks, embeddings, metadatas)):
            chunk_id = metadata.get("chunk_id") or f"chunk_{len(self._chunks)}"
            
            self._chunks.append(chunk)
            self._embeddings.append(embedding)
            self._metadatas.append(metadata)
            self._chunk_ids.append(chunk_id)
        
        logger.debug(f"Added {len(chunks)} chunks to vector store")

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
            List[Tuple[int, float]]: (索引, 相似度分数)列表
        """
        if not self._embeddings:
            return []
        
        scores = []
        for i, embedding in enumerate(self._embeddings):
            # 应用元数据过滤
            if filter_metadata:
                metadata = self._metadatas[i]
                if not self._match_filter(metadata, filter_metadata):
                    continue
            
            # 计算相似度
            similarity = self.cosine_similarity(query_embedding, embedding)
            scores.append((i, similarity))
        
        # 按相似度排序并返回 top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def search_with_content(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索并返回完整内容
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        results = self.search(query_embedding, top_k, filter_metadata)
        
        search_results = []
        for idx, score in results:
            metadata = self._metadatas[idx]
            chunk_metadata = ChunkMetadata(
                chapter_id=metadata.get("chapter_id", 0),
                node_id=metadata.get("node_id", ""),
                unit_type=metadata.get("unit_type", ""),
                characters=metadata.get("characters", []),
                location=metadata.get("location", ""),
                timeline=metadata.get("timeline", ""),
                emotions=metadata.get("emotions", []),
                keywords=metadata.get("keywords", []),
                timestamp=metadata.get("timestamp", ""),
            )
            
            search_results.append(SearchResult(
                content=self._chunks[idx],
                chunk_id=self._chunk_ids[idx],
                score=score,
                metadata=chunk_metadata,
                source_type=metadata.get("source_type", "memory"),
            ))
        
        return search_results

    def delete(self, chunk_ids: List[str]) -> None:
        """
        删除指定文本块
        
        Args:
            chunk_ids: 文本块ID列表
        """
        indices_to_delete = []
        for chunk_id in chunk_ids:
            if chunk_id in self._chunk_ids:
                indices_to_delete.append(self._chunk_ids.index(chunk_id))
        
        # 从后往前删除，避免索引变化
        for idx in sorted(indices_to_delete, reverse=True):
            del self._chunks[idx]
            del self._embeddings[idx]
            del self._metadatas[idx]
            del self._chunk_ids[idx]
        
        logger.debug(f"Deleted {len(indices_to_delete)} chunks from vector store")

    def clear(self) -> None:
        """清空所有数据"""
        self._chunks.clear()
        self._embeddings.clear()
        self._metadatas.clear()
        self._chunk_ids.clear()
        logger.info("Cleared vector store")

    def count(self) -> int:
        """获取存储的文本块数量"""
        return len(self._chunks)

    def save(self) -> None:
        """保存数据到持久化存储"""
        if not self._storage_path:
            logger.warning("No storage path set, skipping save")
            return
        
        data = {
            "chunks": self._chunks,
            "embeddings": self._embeddings,
            "metadatas": self._metadatas,
            "chunk_ids": self._chunk_ids,
        }
        
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved vector store to {self._storage_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise

    def load(self) -> None:
        """从持久化存储加载数据"""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._chunks = data.get("chunks", [])
            self._embeddings = data.get("embeddings", [])
            self._metadatas = data.get("metadatas", [])
            self._chunk_ids = data.get("chunk_ids", [])
            
            logger.info(f"Loaded vector store from {self._storage_path}")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            a: 向量A
            b: 向量B
            
        Returns:
            float: 相似度分数
        """
        if len(a) != len(b):
            raise ValueError("Vectors must have the same dimension")
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    def _match_filter(
        self,
        metadata: Dict[str, Any],
        filter_metadata: Dict[str, Any]
    ) -> bool:
        """
        检查元数据是否匹配过滤条件
        
        Args:
            metadata: 元数据
            filter_metadata: 过滤条件
            
        Returns:
            bool: 是否匹配
        """
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
