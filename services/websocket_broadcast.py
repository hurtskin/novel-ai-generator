"""
WebSocket 广播服务实现

实现 WebSocketBroadcastService 接口，管理客户端连接和消息广播
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from services.interfaces import WebSocketBroadcastService, WebSocketMessage

logger = logging.getLogger(__name__)


class WebSocketBroadcastManager(WebSocketBroadcastService):
    """
    WebSocket 广播管理器
    
    职责：
    - 管理 WebSocket 客户端连接
    - 广播各类消息到所有客户端
    - 支持消息类型路由
    - 处理客户端断开
    
    Attributes:
        _clients: 客户端列表，存储 WebSocket 对象
        _client_ids: 客户端ID映射
    """
    
    def __init__(self):
        """初始化广播管理器"""
        self._clients: List[Any] = []
        self._client_ids: Dict[str, Any] = {}
        self._id_counter = 0
        logger.info("WebSocketBroadcastManager initialized")
    
    def register_client(self, client: Any) -> str:
        """
        注册客户端
        
        Args:
            client: WebSocket 客户端对象
            
        Returns:
            str: 客户端ID
        """
        self._id_counter += 1
        client_id = f"ws_client_{self._id_counter}"
        self._clients.append(client)
        self._client_ids[client_id] = client
        logger.info(f"Client registered: {client_id}, total clients: {len(self._clients)}")
        return client_id
    
    def unregister_client(self, client_id: str) -> bool:
        """
        注销客户端
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        if client_id not in self._client_ids:
            return False
        
        client = self._client_ids[client_id]
        try:
            self._clients.remove(client)
            del self._client_ids[client_id]
            logger.info(f"Client unregistered: {client_id}, remaining clients: {len(self._clients)}")
            return True
        except ValueError:
            return False
    
    async def broadcast(self, message: WebSocketMessage) -> int:
        """
        广播消息到所有客户端
        
        Args:
            message: 消息对象
            
        Returns:
            int: 成功发送的客户端数量
        """
        if not self._clients:
            return 0
        
        msg_data = {
            "type": message.type,
            "data": message.data,
            "timestamp": message.timestamp or datetime.now().isoformat(),
        }
        
        dead_clients = []
        success_count = 0
        
        for client in self._clients:
            try:
                await client.send_json(msg_data)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                dead_clients.append(client)
        
        # 清理断开的客户端
        for dead in dead_clients:
            if dead in self._clients:
                self._clients.remove(dead)
                # 从ID映射中移除
                for cid, c in list(self._client_ids.items()):
                    if c == dead:
                        del self._client_ids[cid]
                        break
        
        return success_count
    
    async def broadcast_token(
        self,
        chapter: int,
        node: str,
        token: str,
    ) -> int:
        """广播 token 流"""
        message = WebSocketMessage(
            type="token",
            data={
                "chapter": chapter,
                "node": node,
                "token": token,
            },
        )
        return await self.broadcast(message)
    
    async def broadcast_progress(
        self,
        current: int,
        total: int,
        percentage: float,
        current_node: str,
        estimated_remaining_cost: float = 0,
    ) -> int:
        """广播进度更新"""
        message = WebSocketMessage(
            type="progress",
            data={
                "current": current,
                "total": total,
                "percentage": percentage,
                "current_node": current_node,
                "estimated_remaining_cost": estimated_remaining_cost,
            },
        )
        logger.debug(f"Broadcasting progress: {current}/{total} ({percentage:.1f}%) - {current_node}")
        return await self.broadcast(message)
    
    async def broadcast_status(self, status: Dict[str, Any]) -> int:
        """广播状态更新"""
        message = WebSocketMessage(
            type="status",
            data=status,
        )
        return await self.broadcast(message)
    
    async def broadcast_log(
        self,
        level: str,
        chapter: int,
        node: str,
        message: str,
    ) -> int:
        """广播日志"""
        ws_message = WebSocketMessage(
            type="log",
            data={
                "level": level,
                "chapter": chapter,
                "node": node,
                "message": message,
            },
        )
        return await self.broadcast(ws_message)
    
    async def broadcast_complete(self, result: Dict[str, Any]) -> int:
        """广播完成消息"""
        message = WebSocketMessage(
            type="complete",
            data=result,
        )
        logger.info(f"Broadcasting completion: {result.get('total_word_count', 0)} words generated")
        return await self.broadcast(message)
    
    async def broadcast_error(self, error: str) -> int:
        """广播错误"""
        message = WebSocketMessage(
            type="error",
            data={"error": error},
        )
        logger.error(f"Broadcasting error: {error}")
        return await self.broadcast(message)
    
    async def broadcast_intervention(self, data: Dict[str, Any]) -> int:
        """广播人工干预请求"""
        message = WebSocketMessage(
            type="need_manual_review",
            data=data,
        )
        logger.warning(f"Broadcasting intervention request for chapter {data.get('chapter')}, node {data.get('node_id')}")
        return await self.broadcast(message)
    
    def get_client_count(self) -> int:
        """获取当前连接的客户端数量"""
        return len(self._clients)
