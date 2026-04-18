"""
配置管理服务实现

提供配置保存、更新、验证和重新加载功能
"""

import logging
import threading
from typing import Any, Dict, List

from interfaces import ConfigProvider
from services.interfaces import (
    ConfigManagerService,
    ConfigSaveResult,
    ConfigManagerError,
)

logger = logging.getLogger(__name__)


class ConfigManager(ConfigManagerService):
    """
    配置管理服务实现
    
    职责：
    - 管理配置保存和更新
    - 支持部分配置更新（深度合并）
    - 配置验证
    - 动态重新加载
    """
    
    def __init__(
        self,
        config_provider: ConfigProvider,
    ):
        """
        初始化配置管理服务
        
        Args:
            config_provider: 配置提供者
        """
        self.config_provider = config_provider
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info("ConfigManager initialized")
    
    async def save_config(self, config_updates: Dict[str, Any]) -> ConfigSaveResult:
        """
        保存配置更新
        
        Args:
            config_updates: 配置更新字典（支持部分更新）
            
        Returns:
            ConfigSaveResult: 保存结果
            
        Raises:
            ConfigManagerError: 保存失败时
        """
        with self._lock:
            try:
                # 验证配置
                if not self.validate_config(config_updates):
                    raise ConfigManagerError("Invalid configuration")
                
                # 获取当前配置
                current_config = self.config_provider.get_all()
                
                # 深度合并配置
                updated_keys = self._deep_update(current_config, config_updates)
                
                # 更新配置提供者中的配置
                for key, value in config_updates.items():
                    if isinstance(value, dict):
                        # 对于嵌套字典，需要逐层设置
                        self._set_nested_config(key, value)
                    else:
                        self.config_provider.set(key, value)
                
                # 保存到文件
                self.config_provider.save()
                
                # 重新加载配置使其生效
                self.config_provider.reload()
                
                logger.info(
                    f"Config saved successfully: updated {len(updated_keys)} keys"
                )
                
                return ConfigSaveResult(
                    success=True,
                    status="saved",
                    message="Configuration saved successfully",
                    updated_keys=updated_keys,
                )
                
            except ConfigManagerError:
                raise
            except Exception as e:
                logger.error(f"Failed to save config: {e}", exc_info=True)
                raise ConfigManagerError(f"Failed to save configuration: {str(e)}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        获取当前完整配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        with self._lock:
            return self.config_provider.get_all()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置是否有效
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 是否有效
        """
        with self._lock:
            # 基本验证：必须是字典
            if not isinstance(config, dict):
                logger.error("Config must be a dictionary")
                return False
            
            # 验证已知的配置项
            valid_sections = {
                "api", "generation", "memory", "ui", "performance",
                "pricing", "rag", "output", "genre", "style"
            }
            
            for key in config.keys():
                if key not in valid_sections:
                    logger.warning(f"Unknown config section: {key}")
                    # 不返回 False，只是警告，允许扩展配置
            
            # 验证特定配置项的类型
            if "api" in config:
                api_config = config["api"]
                if not isinstance(api_config, dict):
                    logger.error("api config must be a dictionary")
                    return False
                
                # 验证 timeout 和 max_retries 是正整数
                if "timeout" in api_config:
                    timeout = api_config["timeout"]
                    if not isinstance(timeout, int) or timeout < 1:
                        logger.error("api.timeout must be a positive integer")
                        return False
                
                if "max_retries" in api_config:
                    max_retries = api_config["max_retries"]
                    if not isinstance(max_retries, int) or max_retries < 0:
                        logger.error("api.max_retries must be a non-negative integer")
                        return False
            
            if "generation" in config:
                gen_config = config["generation"]
                if not isinstance(gen_config, dict):
                    logger.error("generation config must be a dictionary")
                    return False
                
                # 验证 temperature 范围
                if "temperature" in gen_config:
                    temp = gen_config["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        logger.error("generation.temperature must be between 0 and 2")
                        return False
                
                # 验证 top_p 范围
                if "top_p" in gen_config:
                    top_p = gen_config["top_p"]
                    if not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1:
                        logger.error("generation.top_p must be between 0 and 1")
                        return False
                
                # 验证 max_tokens
                if "max_tokens" in gen_config:
                    max_tokens = gen_config["max_tokens"]
                    if not isinstance(max_tokens, int) or max_tokens < 1:
                        logger.error("generation.max_tokens must be a positive integer")
                        return False
            
            return True
    
    def reload_config(self) -> bool:
        """
        重新加载配置
        
        Returns:
            bool: 是否成功
        """
        with self._lock:
            try:
                self.config_provider.reload()
                logger.info("Config reloaded successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to reload config: {e}")
                return False
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> List[str]:
        """
        深度更新字典
        
        Args:
            base: 基础字典
            updates: 更新字典
            
        Returns:
            List[str]: 更新的键列表
        """
        updated_keys = []
        
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                # 递归更新嵌套字典
                nested_updates = self._deep_update(base[key], value)
                updated_keys.extend([f"{key}.{k}" for k in nested_updates])
            else:
                base[key] = value
                updated_keys.append(key)
        
        return updated_keys
    
    def _set_nested_config(self, prefix: str, config_dict: Dict[str, Any]) -> None:
        """
        设置嵌套配置
        
        Args:
            prefix: 配置前缀
            config_dict: 配置字典
        """
        for key, value in config_dict.items():
            full_key = f"{prefix}.{key}"
            if isinstance(value, dict):
                self._set_nested_config(full_key, value)
            else:
                self.config_provider.set(full_key, value)
