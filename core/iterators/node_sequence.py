"""
节点序列迭代器

实现节点序列的迭代功能，支持重试机制
"""

from typing import List, Any, Optional


class NodeSequence:
    """
    节点序列迭代器
    
    用于遍历章节中的节点序列，支持重试机制
    
    Attributes:
        node_sequence: 节点序列列表
        current_index: 当前索引
        retry_count: 重试计数
        retry_index: 重试索引
    
    Example:
        >>> nodes = NodeSequence([{"id": 1}, {"id": 2}, {"id": 3}])
        >>> for node in nodes:
        ...     print(node)
        >>> # 重试上一个节点
        >>> nodes.send("retry")
    """
    
    def __init__(self, node_sequence: List[Any]):
        """
        初始化节点序列迭代器
        
        Args:
            node_sequence: 节点序列列表
        """
        self.node_sequence = list(node_sequence)
        self.current_index: int = 0
        self.retry_count: int = 0
        self.retry_index: Optional[int] = None
    
    def __iter__(self) -> "NodeSequence":
        """返回迭代器对象"""
        return self
    
    def __next__(self) -> Any:
        """
        获取下一个节点
        
        Returns:
            Any: 下一个节点
            
        Raises:
            StopIteration: 当遍历结束时
        """
        # 如果有重试索引，优先返回重试节点
        if self.retry_index is not None:
            idx = self.retry_index
            self.retry_index = None
            return self.node_sequence[idx]
        
        # 检查是否遍历结束
        if self.current_index >= len(self.node_sequence):
            raise StopIteration
        
        # 返回当前节点并递增索引
        result = self.node_sequence[self.current_index]
        self.current_index += 1
        return result
    
    def send(self, feedback: str) -> str:
        """
        发送反馈并触发重试
        
        当节点需要重试时调用此方法，会将当前索引回退到上一个节点
        
        Args:
            feedback: 反馈信息
            
        Returns:
            str: 操作结果，"retry_node" 表示重试节点
        """
        self.retry_count += 1
        if self.current_index > 0:
            self.retry_index = self.current_index - 1
        return "retry_node"
    
    def get_current_index(self) -> int:
        """获取当前索引"""
        return self.current_index
    
    def get_retry_count(self) -> int:
        """获取重试计数"""
        return self.retry_count

    def reset_retry_count(self) -> None:
        """重置重试计数"""
        self.retry_count = 0

    def get_total_nodes(self) -> int:
        """获取节点总数"""
        return len(self.node_sequence)
    
    def is_finished(self) -> bool:
        """检查是否遍历完成"""
        return self.current_index >= len(self.node_sequence) and self.retry_index is None
    
    def reset(self) -> None:
        """重置迭代器状态"""
        self.current_index = 0
        self.retry_count = 0
        self.retry_index = None
