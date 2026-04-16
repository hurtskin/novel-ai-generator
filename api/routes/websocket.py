"""
WebSocket 路由模块

提供实时通信功能，支持双向数据传输
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field

from api.dependencies import get_generation_state, GenerationState

logger = logging.getLogger(__name__)

router = APIRouter()


class MessageType(str, Enum):
    """WebSocket 消息类型"""
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PROGRESS = "progress"
    LOG = "log"
    METRICS = "metrics"
    ERROR = "error"
    STATUS = "status"
    INTERVENTION = "intervention"


class WebSocketMessage(BaseModel):
    """WebSocket 消息模型"""
    type: MessageType = Field(..., description="消息类型")
    data: Dict = Field(default={}, description="消息数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    管理所有 WebSocket 连接，提供广播和点对点通信功能
    """
    
    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._subscribers: Dict[str, Set[str]] = {
            "progress": set(),
            "logs": set(),
            "metrics": set(),
            "all": set(),
        }
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        接受新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端唯一标识
        """
        await websocket.accept()
        self._connections[client_id] = websocket
        self._subscribers["all"].add(client_id)
        logger.info(f"WebSocket client {client_id} connected. Total: {len(self._connections)}")
    
    def disconnect(self, client_id: str) -> None:
        """
        断开 WebSocket 连接
        
        Args:
            client_id: 客户端唯一标识
        """
        if client_id in self._connections:
            del self._connections[client_id]
        
        # 从所有订阅中移除
        for subscribers in self._subscribers.values():
            subscribers.discard(client_id)
        
        logger.info(f"WebSocket client {client_id} disconnected. Total: {len(self._connections)}")
    
    def subscribe(self, client_id: str, channel: str) -> None:
        """
        订阅频道
        
        Args:
            client_id: 客户端唯一标识
            channel: 频道名称
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        self._subscribers[channel].add(client_id)
        logger.debug(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, client_id: str, channel: str) -> None:
        """
        取消订阅频道
        
        Args:
            client_id: 客户端唯一标识
            channel: 频道名称
        """
        if channel in self._subscribers:
            self._subscribers[channel].discard(client_id)
        logger.debug(f"Client {client_id} unsubscribed from {channel}")
    
    async def send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """
        发送消息给指定客户端
        
        Args:
            client_id: 客户端唯一标识
            message: 消息对象
            
        Returns:
            bool: 发送是否成功
        """
        if client_id not in self._connections:
            return False
        
        try:
            await self._connections[client_id].send_json(message.model_dump())
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            return False
    
    async def broadcast(
        self,
        message: WebSocketMessage,
        channel: str = "all",
    ) -> int:
        """
        广播消息到指定频道
        
        Args:
            message: 消息对象
            channel: 频道名称
            
        Returns:
            int: 成功发送的客户端数量
        """
        if channel not in self._subscribers:
            return 0
        
        sent_count = 0
        dead_clients = []
        
        for client_id in list(self._subscribers[channel]):
            if await self.send_to_client(client_id, message):
                sent_count += 1
            else:
                dead_clients.append(client_id)
        
        # 清理失效连接
        for client_id in dead_clients:
            self.disconnect(client_id)
        
        return sent_count
    
    async def broadcast_progress(
        self,
        current: int,
        total: int,
        current_node: str,
        estimated_remaining_cost: float = 0.0,
    ) -> int:
        """
        广播进度更新
        
        Args:
            current: 当前进度
            total: 总进度
            current_node: 当前节点
            estimated_remaining_cost: 预估剩余成本
            
        Returns:
            int: 成功发送的客户端数量
        """
        message = WebSocketMessage(
            type=MessageType.PROGRESS,
            data={
                "current": current,
                "total": total,
                "percentage": round(current / total * 100, 1) if total > 0 else 0,
                "current_node": current_node,
                "estimated_remaining_cost": estimated_remaining_cost,
            },
        )
        return await self.broadcast(message, "progress")
    
    async def broadcast_log(
        self,
        level: str,
        chapter: int,
        node: str,
        message: str,
    ) -> int:
        """
        广播日志消息
        
        Args:
            level: 日志级别
            chapter: 章节号
            node: 节点名称
            message: 日志内容
            
        Returns:
            int: 成功发送的客户端数量
        """
        ws_message = WebSocketMessage(
            type=MessageType.LOG,
            data={
                "level": level,
                "chapter": chapter,
                "node": node,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        )
        return await self.broadcast(ws_message, "logs")
    
    async def broadcast_metrics(self, metrics: Dict) -> int:
        """
        广播性能指标
        
        Args:
            metrics: 性能指标数据
            
        Returns:
            int: 成功发送的客户端数量
        """
        message = WebSocketMessage(
            type=MessageType.METRICS,
            data=metrics,
        )
        return await self.broadcast(message, "metrics")
    
    async def broadcast_status(self, status: Dict) -> int:
        """
        广播状态更新
        
        Args:
            status: 状态数据
            
        Returns:
            int: 成功发送的客户端数量
        """
        message = WebSocketMessage(
            type=MessageType.STATUS,
            data=status,
        )
        return await self.broadcast(message, "all")
    
    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self._connections)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接端点
    
    处理客户端连接、消息接收和发送
    
    协议：
    - 连接后自动订阅 "all" 频道
    - 发送 {"type": "subscribe", "data": {"channel": "progress"}} 订阅频道
    - 发送 {"type": "ping"} 保持连接
    - 服务端会定期发送心跳
    """
    import uuid
    client_id = f"ws_{uuid.uuid4().hex[:8]}"
    
    await manager.connect(websocket, client_id)
    
    try:
        # 发送欢迎消息
        await manager.send_to_client(
            client_id,
            WebSocketMessage(
                type=MessageType.STATUS,
                data={
                    "client_id": client_id,
                    "message": "Connected to Novel AI Generator",
                    "channels": list(manager._subscribers.keys()),
                },
            ),
        )
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                raw_message = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type", "")
                    msg_data = data.get("data", {})
                    
                    # 处理 ping
                    if msg_type == MessageType.PING:
                        await manager.send_to_client(
                            client_id,
                            WebSocketMessage(type=MessageType.PONG, data={"timestamp": datetime.now().isoformat()}),
                        )
                    
                    # 处理订阅
                    elif msg_type == MessageType.SUBSCRIBE:
                        channel = msg_data.get("channel", "all")
                        manager.subscribe(client_id, channel)
                        await manager.send_to_client(
                            client_id,
                            WebSocketMessage(
                                type=MessageType.STATUS,
                                data={"message": f"Subscribed to {channel}"},
                            ),
                        )
                    
                    # 处理取消订阅
                    elif msg_type == MessageType.UNSUBSCRIBE:
                        channel = msg_data.get("channel", "all")
                        manager.unsubscribe(client_id, channel)
                        await manager.send_to_client(
                            client_id,
                            WebSocketMessage(
                                type=MessageType.STATUS,
                                data={"message": f"Unsubscribed from {channel}"},
                            ),
                        )
                    
                    # 处理其他消息类型
                    else:
                        logger.debug(f"Received message from {client_id}: {msg_type}")
                
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {client_id}: {raw_message[:100]}")
                    await manager.send_to_client(
                        client_id,
                        WebSocketMessage(
                            type=MessageType.ERROR,
                            data={"error": "Invalid JSON format"},
                        ),
                    )
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                break
    
    finally:
        manager.disconnect(client_id)


@router.get("/status")
async def get_websocket_status() -> Dict:
    """
    获取 WebSocket 状态
    
    Returns:
        连接状态和统计信息
    """
    return {
        "connected_clients": manager.get_connection_count(),
        "channels": {
            channel: len(subscribers)
            for channel, subscribers in manager._subscribers.items()
        },
    }


# 导出管理器供其他模块使用
__all__ = ["router", "manager", "ConnectionManager", "MessageType", "WebSocketMessage"]
