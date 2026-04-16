"""
装饰器模块

提供 LLM 节点的装饰器功能，包括 JSON 输出处理和 Schema 验证
"""

import json
import functools
import logging
import re
from typing import Any, Callable, Optional, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Schema 验证错误"""
    
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Schema validation failed: {errors}")


def _clean_json_string(json_str: str) -> str:
    """
    清理 JSON 字符串，移除 markdown 代码块标记和引号
    
    Args:
        json_str: 原始 JSON 字符串
        
    Returns:
        str: 清理后的 JSON 字符串
    """
    json_str = json_str.strip()
    json_str = re.sub(r'^```json\s*', '', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'^```\s*', '', json_str)
    json_str = re.sub(r'\s*```$', '', json_str)
    json_str = json_str.strip()
    
    if json_str.startswith("'") and json_str.endswith("'"):
        json_str = json_str[1:-1]
    if json_str.startswith('"') and json_str.endswith('"'):
        json_str = json_str[1:-1]
    
    return json_str


def _parse_json(json_str: str) -> dict:
    """
    解析 JSON 字符串，处理各种边界情况
    
    Args:
        json_str: JSON 字符串
        
    Returns:
        dict: 解析后的字典
        
    Raises:
        json.JSONDecodeError: 当解析失败时
    """
    cleaned = _clean_json_string(json_str)
    
    try:
        parsed = json.loads(cleaned)
        # 处理 properties 嵌套的情况
        if isinstance(parsed, dict) and "properties" in parsed:
            parsed = parsed.get("properties", parsed)
        return parsed
    except json.JSONDecodeError as e:
        # 尝试从文本中提取 JSON
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict) and "properties" in parsed:
                    parsed = parsed.get("properties", parsed)
                return parsed
            except json.JSONDecodeError:
                pass
        raise e


def json_output(func: Callable) -> Callable:
    """
    JSON 输出装饰器
    
    将函数输出转换为 JSON 字典格式，处理 Pydantic 模型和字符串
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 包装后的函数
        
    Example:
        >>> @json_output
        ... def my_function():
        ...     return '{"key": "value"}'
        >>> result = my_function()
        >>> print(result)
        {'key': 'value'}
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        raw = func(*args, **kwargs)
        logger.debug(f"[json_output] raw type = {type(raw)}, value = {str(raw)[:300]}")
        
        # 处理 Pydantic 模型
        if hasattr(raw, 'model_dump'):
            parsed = raw.model_dump()
            logger.debug(f"[json_output] converted Pydantic model to dict")
            return parsed
        
        # 处理字符串
        elif isinstance(raw, str):
            try:
                parsed = _parse_json(raw)
                logger.debug(f"[json_output] parsed JSON = {str(parsed)[:200]}")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed: {e}, returning raw string")
                return {"_raw": raw, "_parse_error": str(e)}
        
        # 其他类型直接返回
        else:
            logger.debug(f"[json_output] not string, using raw = {str(raw)[:200]}")
            return raw
    
    return wrapper


def _apply_schema_fixes(result: dict, schema_class: Type[BaseModel]) -> dict:
    """
    根据 Schema 类型应用特定的修复
    
    Args:
        result: 原始结果字典
        schema_class: Schema 类
        
    Returns:
        dict: 修复后的字典
    """
    result = result.copy()
    
    if schema_class.__name__ == "DirectorGeneralOutput":
        if "genre_specific" in result:
            gs = result["genre_specific"]
            if isinstance(gs, str):
                result["genre_specific"] = {
                    "genre": "novel",
                    "specific_fields": {"description": gs}
                }
            elif isinstance(gs, dict) and "genre" not in gs:
                result["genre_specific"] = {
                    "genre": "novel",
                    "specific_fields": gs
                }
    
    elif schema_class.__name__ == "DirectorChapterOutput":
        if "character_presence_plan" in result:
            cpp = result["character_presence_plan"]
            if isinstance(cpp, dict):
                for key, value in cpp.items():
                    if isinstance(value, dict) and "scenes" in value:
                        cpp[key] = value["scenes"]
        
        if "genre_specific" in result:
            gs = result["genre_specific"]
            if isinstance(gs, str):
                result["genre_specific"] = {
                    "genre": "novel",
                    "specific_fields": {"description": gs}
                }
            elif isinstance(gs, dict) and "genre" not in gs:
                result["genre_specific"] = {
                    "genre": "novel",
                    "specific_fields": gs
                }
    
    return result


def validate_schema(schema_class: Optional[Type[BaseModel]] = None, max_retries: int = 3):
    """
    Schema 验证装饰器
    
    验证函数输出是否符合指定的 Pydantic Schema，支持自动重试
    
    Args:
        schema_class: Pydantic 模型类，用于验证
        max_retries: 最大重试次数
        
    Returns:
        Callable: 装饰器函数
        
    Example:
        >>> from pydantic import BaseModel
        >>> class Output(BaseModel):
        ...     name: str
        ...     value: int
        >>> 
        >>> @validate_schema(Output)
        ... def my_function():
        ...     return '{"name": "test", "value": 123}'
        >>> result = my_function()
        >>> print(result)
        {'name': 'test', 'value': 123}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            last_error = None
            
            while retry_count <= max_retries:
                result = func(*args, **kwargs)
                
                # 转换 Pydantic 模型
                if hasattr(result, 'model_dump'):
                    result = result.model_dump()
                
                # 转换字符串
                elif isinstance(result, str):
                    try:
                        result = _parse_json(result)
                    except json.JSONDecodeError:
                        pass
                
                # 应用 Schema 特定的修复
                if schema_class is not None and isinstance(result, dict):
                    result = _apply_schema_fixes(result, schema_class)
                
                # 无 Schema 验证，直接返回
                if schema_class is None:
                    return result
                
                # 验证 Schema
                try:
                    validated = schema_class.model_validate(result)
                    logger.debug(f"[validate_schema] validated successfully")
                    return validated.model_dump()
                except ValidationError as e:
                    logger.warning(f"[validate_schema] ValidationError: {e}")
                    last_error = e
                    retry_count += 1
                    
                    if retry_count <= max_retries:
                        continue
                    else:
                        raise SchemaValidationError(e.errors())
            
            raise SchemaValidationError(last_error.errors() if last_error else [])
        
        return wrapper
    return decorator
