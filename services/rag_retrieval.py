"""
RAG 检索服务实现

实现 RAGRetrievalService 接口，提供基于向量相似度的记忆检索功能
"""

import logging
from typing import Any, Dict, List, Optional

from services.interfaces import RAGRetrievalService, RAGSearchResult
from interfaces.memory import MemoryStore

logger = logging.getLogger(__name__)


class RAGRetrievalManager(RAGRetrievalService):
    """
    RAG 检索管理器
    
    职责：
    - 执行向量相似度检索
    - 管理检索上下文
    - 支持批量查询
    
    Attributes:
        memory_store: 记忆存储实例
    """
    
    def __init__(self, memory_store: Optional[MemoryStore] = None):
        """
        初始化 RAG 检索管理器
        
        Args:
            memory_store: 记忆存储实例，可选
        """
        self.memory_store = memory_store
        logger.info("RAGRetrievalManager initialized")
    
    async def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RAGSearchResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            List[RAGSearchResult]: 检索结果
        """
        if not self.memory_store:
            logger.warning("Memory store not configured, returning empty results")
            return []
        
        try:
            # 调用 memory_store 的检索方法
            results = await self.memory_store.retrieve(
                query=query,
                top_k=top_k,
                filters=filters or {},
            )
            
            # 转换为 RAGSearchResult
            search_results = []
            for result in results:
                search_results.append(
                    RAGSearchResult(
                        content=result.content,
                        score=result.score,
                        metadata=result.metadata,
                    )
                )
            
            logger.debug(f"RAG search returned {len(search_results)} results for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []
    
    async def search_multiple(
        self,
        queries: List[str],
        top_k: int = 3,
    ) -> List[List[RAGSearchResult]]:
        """
        批量检索
        
        Args:
            queries: 查询列表
            top_k: 每个查询返回结果数量
            
        Returns:
            List[List[RAGSearchResult]]: 批量检索结果
        """
        if not self.memory_store:
            logger.warning("Memory store not configured, returning empty results")
            return [[] for _ in queries]
        
        results = []
        for query in queries:
            result = await self.search(query, top_k=top_k)
            results.append(result)
        
        logger.debug(f"RAG batch search completed for {len(queries)} queries")
        return results
    
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        添加文档到向量存储
        
        Args:
            content: 文档内容
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        if not self.memory_store:
            logger.warning("Memory store not configured, cannot add document")
            return False
        
        try:
            # 调用 memory_store 的添加方法（同步方法，不使用 await）
            self.memory_store.add_memory(
                content=content,
                metadata=metadata,
            )
            logger.debug(f"Added document to RAG store: {content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def set_memory_store(self, memory_store: MemoryStore) -> None:
        """
        设置记忆存储实例
        
        Args:
            memory_store: 记忆存储实例
        """
        self.memory_store = memory_store
        logger.info("Memory store updated")

    async def clear(self) -> bool:
        """
        清空所有检索数据
        
        Returns:
            bool: 是否成功清空
        """
        if not self.memory_store:
            logger.warning("Memory store not configured, cannot clear")
            return False
        
        try:
            # 检查 memory_store 是否有 clear 方法
            if hasattr(self.memory_store, 'clear'):
                self.memory_store.clear()
                logger.info("RAG retrieval data cleared")
                return True
            else:
                logger.warning("Memory store does not support clear operation")
                return False
        except Exception as e:
            logger.error(f"Failed to clear RAG data: {e}")
            return False
