"""
嵌入服务接口定义

定义文本嵌入和向量存储的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    embedding: List[float]
    text: str
    index: int


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


@dataclass
class SearchResult:
    """向量搜索结果"""
    content: str
    chunk_id: str
    score: float
    metadata: ChunkMetadata
    source_type: str


@dataclass
class VectorSearchMetrics:
    """向量搜索指标"""
    query_time_ms: int
    total_hits: int
    returned_results: int


class EmbeddingClient(ABC):
    """
    嵌入客户端抽象基类
    
    职责：
    - 将文本转换为向量嵌入
    - 支持批量处理
    
    实现类：
    - InfiniEmbeddingClient: InfiniAI嵌入服务
    """
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        pass
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        """
        将单个文本转换为嵌入向量
        
        Args:
            text: 文本
            
        Returns:
            List[float]: 嵌入向量
        """
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """获取嵌入维度"""
        pass
    
    @abstractmethod
    def get_model(self) -> str:
        """获取模型名称"""
        pass


class VectorStore(ABC):
    """
    向量存储抽象基类
    
    职责：
    - 存储文本块和对应的嵌入向量
    - 支持相似度搜索
    - 支持元数据过滤
    
    实现类：
    - SimpleVectorStore: 简单的内存向量存储
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def delete(self, chunk_ids: List[str]) -> None:
        """
        删除指定文本块
        
        Args:
            chunk_ids: 文本块ID列表
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有数据"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取存储的文本块数量"""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """保存数据到持久化存储"""
        pass
    
    @abstractmethod
    def load(self) -> None:
        """从持久化存储加载数据"""
        pass
    
    @abstractmethod
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            a: 向量A
            b: 向量B
            
        Returns:
            float: 相似度分数
        """
        pass


class RAGSystem(ABC):
    """
    RAG系统抽象基类
    
    职责：
    - 整合嵌入客户端和向量存储
    - 提供高级的RAG检索功能
    
    实现类：
    - RagMemorySystem: RAG记忆系统
    """
    
    @abstractmethod
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
    ) -> None:
        """
        摄入内容到RAG系统
        
        Args:
            content: 文本内容
            chapter_id: 章节ID
            node_id: 节点ID
            unit_type: 单元类型
            characters: 角色列表
            location: 地点
            timeline: 时间线
            emotions: 情绪列表
            keywords: 关键词列表
        """
        pass
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SearchResult], VectorSearchMetrics]:
        """
        检索相关内容
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            Tuple[List[SearchResult], VectorSearchMetrics]: 搜索结果和指标
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取RAG系统统计信息"""
        pass
