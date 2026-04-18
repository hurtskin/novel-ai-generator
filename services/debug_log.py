"""
调试日志服务实现

提供调试日志读取、清除、写入和调试模式管理功能
"""

import logging
import os
import threading
from datetime import datetime
from typing import Optional

from interfaces import ConfigProvider
from services.interfaces import (
    DebugLogService,
    DebugLogResult,
    DebugLogError,
)

logger = logging.getLogger(__name__)


class DebugLogManager(DebugLogService):
    """
    调试日志管理服务实现
    
    职责：
    - 读取调试日志内容
    - 清空调试日志
    - 切换调试模式
    - 写入调试日志
    """
    
    def __init__(
        self,
        config_provider: ConfigProvider,
    ):
        """
        初始化调试日志管理服务
        
        Args:
            config_provider: 配置提供者
        """
        self.config_provider = config_provider
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 调试日志文件路径
        self._debug_log_path = os.path.join(
            os.path.dirname(__file__), "..", "logs", "debug.log"
        )
        self._debug_log_path = os.path.abspath(self._debug_log_path)
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self._debug_log_path), exist_ok=True)
        
        logger.info(f"DebugLogManager initialized, log path: {self._debug_log_path}")
    
    def get_debug_log(self) -> DebugLogResult:
        """
        获取调试日志内容
        
        Returns:
            DebugLogResult: 调试日志内容和状态
            
        Raises:
            DebugLogError: 读取失败时
        """
        with self._lock:
            try:
                # 检查文件是否存在
                if not os.path.exists(self._debug_log_path):
                    return DebugLogResult(
                        success=True,
                        status="success",
                        message="Debug log file does not exist",
                        content="",
                        exists=False,
                    )
                
                # 读取文件内容
                with open(self._debug_log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                logger.debug(f"Debug log read: {len(content)} characters")
                
                return DebugLogResult(
                    success=True,
                    status="success",
                    message="Debug log read successfully",
                    content=content,
                    exists=True,
                )
                
            except Exception as e:
                logger.error(f"Failed to read debug log: {e}", exc_info=True)
                raise DebugLogError(f"Failed to read debug log: {str(e)}")
    
    def clear_debug_log(self) -> DebugLogResult:
        """
        清空调试日志
        
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 清除失败时
        """
        with self._lock:
            try:
                # 检查文件是否存在
                if not os.path.exists(self._debug_log_path):
                    return DebugLogResult(
                        success=True,
                        status="success",
                        message="Debug log file does not exist, nothing to clear",
                        exists=False,
                    )
                
                # 清空文件内容
                with open(self._debug_log_path, "w", encoding="utf-8") as f:
                    f.write("")
                
                logger.info("Debug log cleared successfully")
                
                return DebugLogResult(
                    success=True,
                    status="success",
                    message="Debug log cleared successfully",
                    exists=True,
                )
                
            except Exception as e:
                logger.error(f"Failed to clear debug log: {e}", exc_info=True)
                raise DebugLogError(f"Failed to clear debug log: {str(e)}")
    
    def write_debug_log(self, message: str, level: str = "INFO") -> DebugLogResult:
        """
        写入调试日志
        
        Args:
            message: 日志消息
            level: 日志级别（DEBUG, INFO, WARNING, ERROR）
            
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 写入失败时
        """
        with self._lock:
            try:
                # 验证日志级别
                valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
                if level.upper() not in valid_levels:
                    raise DebugLogError(f"Invalid log level: {level}")
                
                # 构建日志行
                timestamp = datetime.now().isoformat()
                log_line = f"[{timestamp}] [{level.upper()}] {message}\n"
                
                # 写入文件
                with open(self._debug_log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
                
                logger.debug(f"Debug log written: [{level}] {message[:50]}...")
                
                return DebugLogResult(
                    success=True,
                    status="success",
                    message="Debug log written successfully",
                    exists=True,
                )
                
            except DebugLogError:
                raise
            except Exception as e:
                logger.error(f"Failed to write debug log: {e}", exc_info=True)
                raise DebugLogError(f"Failed to write debug log: {str(e)}")
    
    def set_debug_mode(self, enabled: bool) -> DebugLogResult:
        """
        设置调试模式
        
        Args:
            enabled: 是否启用调试模式
            
        Returns:
            DebugLogResult: 操作结果
            
        Raises:
            DebugLogError: 设置失败时
        """
        with self._lock:
            try:
                # 更新配置
                self.config_provider.set("generation.debug", enabled)
                self.config_provider.save()
                
                logger.info(f"Debug mode set to: {enabled}")
                
                return DebugLogResult(
                    success=True,
                    status="success",
                    message=f"Debug mode {'enabled' if enabled else 'disabled'}",
                    exists=True,
                )
                
            except Exception as e:
                logger.error(f"Failed to set debug mode: {e}", exc_info=True)
                raise DebugLogError(f"Failed to set debug mode: {str(e)}")
    
    def get_debug_mode(self) -> bool:
        """
        获取当前调试模式状态
        
        Returns:
            bool: 是否启用调试模式
        """
        with self._lock:
            return self.config_provider.get_bool("generation.debug", False)
