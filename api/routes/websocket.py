"""
WebSocket 路由模块 - 事件驱动版本

提供实时通信功能，通过 EventBus 实现业务逻辑与通信层的解耦
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.interfaces import EventBus, Event

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
    TOKEN = "token"
    COMPLETE = "complete"


class WebSocketMessage(BaseModel):
    """WebSocket 消息模型"""
    type: MessageType = Field(..., description="消息类型")
    data: Dict = Field(default={}, description="消息数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")


class WebSocketConnectionManager:
    """
    WebSocket 连接管理器 - 事件驱动版本
    
    职责：
    - 管理 WebSocket 连接生命周期
    - 订阅 EventBus 事件并转发到 WebSocket 客户端
    - 维护客户端频道订阅
    
    Attributes:
        _event_bus: 事件总线
        _connections: 客户端连接映射 {client_id: websocket}
        _subscriptions: 频道订阅映射 {channel: {client_id}}
        _event_queue: 事件队列（用于解耦同步事件发布和异步发送）
        _event_processor_task: 事件处理器后台任务
    """
    
    def __init__(self, event_bus: EventBus):
        """
        初始化连接管理器
        
        Args:
            event_bus: 事件总线实例
        """
        self._event_bus = event_bus
        self._connections: Dict[str, WebSocket] = {}
        self._subscriptions: Dict[str, Set[str]] = {
            "all": set(),
            "progress": set(),
            "logs": set(),
            "metrics": set(),
            "intervention": set(),
        }
        # 事件队列和处理器（用于解耦同步事件发布和异步 WebSocket 发送）
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_processor_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        self._setup_event_forwarding()
        self._start_event_processor()
    
    def _setup_event_forwarding(self):
        """设置事件转发 - 订阅所有事件并转发到 WebSocket 客户端"""
        self._event_bus.subscribe("*", self._on_event)
    
    def _start_event_processor(self):
        """启动事件处理器后台任务"""
        try:
            self._loop = asyncio.get_running_loop()
            self._event_processor_task = self._loop.create_task(self._process_events())
            logger.info("[WebSocket] Event processor started")
        except RuntimeError:
            logger.warning("[WebSocket] No running event loop, event processor will be started on first connection")
    
    async def _process_events(self):
        """后台任务：从队列中取出事件并广播"""
        while True:
            try:
                message = await self._event_queue.get()
                if message is None:  # 停止信号
                    break
                
                event_type = message.get("type")
                channel = self._get_channel_for_event(event_type)
                await self._broadcast_to_channel(channel, message)
            except Exception as e:
                logger.error(f"[WebSocket] Event processing error: {e}")
    
    def _on_event(self, event: Event):
        """
        处理来自 EventBus 的事件（同步方法）
        
        将事件放入队列，由后台任务异步处理，解耦同步事件发布和异步 WebSocket 发送
        
        Args:
            event: 事件对象
        """
        message = {
            "type": event.type,
            "data": event.data,
            "timestamp": event.timestamp,
        }
        
        # 将事件放入队列（线程安全）
        try:
            if self._loop is not None:
                # 使用 call_soon_threadsafe 将事件放入队列
                self._loop.call_soon_threadsafe(self._event_queue.put_nowait, message)
                logger.info(f"[WebSocket] Event '{event.type}' queued for broadcast")
            else:
                # 如果没有事件循环，尝试直接放入（可能在主线程）
                try:
                    self._event_queue.put_nowait(message)
                    logger.info(f"[WebSocket] Event '{event.type}' queued (direct)")
                except Exception as e:
                    logger.warning(f"[WebSocket] Failed to queue event '{event.type}': {e}")
        except Exception as e:
            logger.error(f"[WebSocket] Error queueing event '{event.type}': {e}")
    
    def _get_channel_for_event(self, event_type: str) -> str:
        """
        根据事件类型获取对应的频道
        
        Args:
            event_type: 事件类型
            
        Returns:
            str: 频道名称
        """
        mapping = {
            "log": "logs",
            "progress": "progress",
            "node_metric": "metrics",
            "chapter_metric": "metrics",
            "total_metric": "metrics",
            "need_manual_review": "intervention",
            "status": "all",
            "complete": "all",
            "error": "all",
            "token": "all",
        }
        return mapping.get(event_type, "all")
    
    async def _broadcast_to_channel(self, channel: str, message: dict):
        """
        广播消息到指定频道的所有客户端
        
        Args:
            channel: 频道名称
            message: 消息字典
        """
        if channel not in self._subscriptions:
            logger.warning(f"[WebSocket] Channel '{channel}' not found in subscriptions")
            return
        
        client_ids = self._subscriptions[channel] | self._subscriptions["all"]
        logger.info(f"[WebSocket] Broadcasting '{message.get('type')}' to {len(client_ids)} clients on channel '{channel}'")
        
        if not client_ids:
            logger.warning(f"[WebSocket] No clients subscribed to channel '{channel}' or 'all'")
            return
        
        dead_clients = []
        
        for client_id in client_ids:
            if client_id not in self._connections:
                dead_clients.append(client_id)
                continue
            
            try:
                await self._connections[client_id].send_json(message)
                logger.info(f"[WebSocket] Message '{message.get('type')}' sent to client '{client_id}'")
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send to {client_id}: {e}")
                dead_clients.append(client_id)
        
        for client_id in dead_clients:
            self._disconnect_client(client_id)
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        接受新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端唯一标识
        """
        # 确保事件处理器已启动
        if self._event_processor_task is None or self._event_processor_task.done():
            self._start_event_processor()
        
        await websocket.accept()
        self._connections[client_id] = websocket
        self._subscriptions["all"].add(client_id)
        logger.info(f"WebSocket client {client_id} connected. Total: {len(self._connections)}")
    
    def _disconnect_client(self, client_id: str):
        """
        断开指定客户端
        
        Args:
            client_id: 客户端唯一标识
        """
        if client_id in self._connections:
            del self._connections[client_id]
        for subscribers in self._subscriptions.values():
            subscribers.discard(client_id)
    
    def subscribe(self, client_id: str, channel: str) -> None:
        """
        订阅频道
        
        Args:
            client_id: 客户端唯一标识
            channel: 频道名称
        """
        if channel not in self._subscriptions:
            self._subscriptions[channel] = set()
        self._subscriptions[channel].add(client_id)
        logger.debug(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, client_id: str, channel: str) -> None:
        """
        取消订阅频道
        
        Args:
            client_id: 客户端唯一标识
            channel: 频道名称
        """
        if channel in self._subscriptions:
            self._subscriptions[channel].discard(client_id)
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
    
    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self._connections)


# 全局连接管理器实例（通过 initialize_connection_manager 初始化）
connection_manager: Optional[WebSocketConnectionManager] = None


def initialize_connection_manager(event_bus: EventBus) -> WebSocketConnectionManager:
    """
    初始化 WebSocket 连接管理器
    
    Args:
        event_bus: 事件总线实例
        
    Returns:
        WebSocketConnectionManager: 连接管理器实例
    """
    global connection_manager
    connection_manager = WebSocketConnectionManager(event_bus)
    logger.info("WebSocketConnectionManager initialized with EventBus")
    return connection_manager


def get_connection_manager() -> Optional[WebSocketConnectionManager]:
    """
    获取连接管理器实例
    
    Returns:
        Optional[WebSocketConnectionManager]: 连接管理器实例（如果已初始化）
    """
    return connection_manager


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接端点
    
    处理客户端连接、消息接收和发送
    
    协议：
    - 连接后自动订阅 "all" 频道
    - 发送 {"type": "subscribe", "data": {"channel": "progress"}} 订阅频道
    - 发送 {"type": "ping"} 保持连接
    """
    import uuid
    client_id = f"ws_{uuid.uuid4().hex[:8]}"
    
    manager = get_connection_manager()
    if manager is None:
        logger.error("WebSocketConnectionManager not initialized")
        await websocket.close(code=1011, reason="Server not ready")
        return
    
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
                    "channels": list(manager._subscriptions.keys()),
                },
            ),
        )
        
        # 消息处理循环
        while True:
            try:
                raw_message = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type", "")
                    msg_data = data.get("data", {})
                    
                    # 处理 ping
                    if msg_type == MessageType.PING:
                        await manager.send_to_client(
                            client_id,
                            WebSocketMessage(
                                type=MessageType.PONG,
                                data={"timestamp": datetime.now().isoformat()}
                            ),
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
        manager._disconnect_client(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")


@router.get("/status")
async def get_websocket_status() -> Dict:
    """
    获取 WebSocket 状态
    
    Returns:
        连接状态和统计信息
    """
    manager = get_connection_manager()
    if manager is None:
        return {
            "connected_clients": 0,
            "channels": {},
            "initialized": False,
        }
    
    return {
        "connected_clients": manager.get_connection_count(),
        "channels": {
            channel: len(subscribers)
            for channel, subscribers in manager._subscriptions.items()
        },
        "initialized": True,
    }


# 导出供其他模块使用
__all__ = [
    "router",
    "connection_manager",
    "WebSocketConnectionManager",
    "initialize_connection_manager",
    "get_connection_manager",
    "MessageType",
    "WebSocketMessage",
]
