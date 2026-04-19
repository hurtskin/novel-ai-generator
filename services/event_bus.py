"""
事件总线实现

提供内存中的事件发布和订阅机制，实现业务逻辑与通信层的解耦
"""

import logging
import uuid
from typing import Dict, Callable
from collections import defaultdict

from services.interfaces import EventBus, Event

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """
    内存事件总线实现
    
    职责：
    - 管理事件订阅者
    - 分发事件到所有订阅者
    - 支持通配符订阅
    - 单进程部署使用
    
    Attributes:
        _handlers: 事件处理器映射 {event_type: {subscription_id: handler}}
    """
    
    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[str, Dict[str, Callable[[Event], None]]] = defaultdict(dict)
        logger.info("InMemoryEventBus initialized")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型，使用 "*" 订阅所有事件
            handler: 事件处理函数
            
        Returns:
            str: 订阅ID
        """
        subscription_id = f"{event_type}_{uuid.uuid4().hex[:8]}"
        self._handlers[event_type][subscription_id] = handler
        logger.debug(f"Subscribed to {event_type}, id: {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 是否成功取消
        """
        for event_type, handlers in self._handlers.items():
            if subscription_id in handlers:
                del handlers[subscription_id]
                logger.debug(f"Unsubscribed {subscription_id} from {event_type}")
                return True
        return False
    
    def publish(self, event: Event) -> int:
        """
        发布事件
        
        Args:
            event: 事件对象
            
        Returns:
            int: 通知的订阅者数量
        """
        handlers = self._handlers.get(event.type, {})
        wildcard_handlers = self._handlers.get("*", {})
        
        notified = 0
        all_handlers = {**handlers, **wildcard_handlers}
        
        for handler in all_handlers.values():
            try:
                handler(event)
                notified += 1
            except Exception as e:
                logger.error(f"Event handler failed for {event.type}: {e}")
        
        return notified
