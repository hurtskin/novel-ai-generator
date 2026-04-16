"""
通用辅助函数模块

提供项目中使用的各类通用辅助函数
"""

import json
import re
import os
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析 JSON 字符串
    
    Args:
        json_str: JSON 字符串
        default: 解析失败时的默认值
        
    Returns:
        Any: 解析后的数据或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, ensure_ascii: bool = False, indent: int = 2) -> str:
    """
    安全地将数据转换为 JSON 字符串
    
    Args:
        data: 要转换的数据
        ensure_ascii: 是否确保 ASCII 编码
        indent: 缩进空格数
        
    Returns:
        str: JSON 字符串
    """
    try:
        return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, default=str)
    except (TypeError, ValueError) as e:
        return json.dumps({"_error": str(e), "_raw": str(data)})


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串到指定长度
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    清理文本，移除多余空白和特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    text = text.strip()
    return text


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中提取 JSON 对象
    
    Args:
        text: 包含 JSON 的文本
        
    Returns:
        Optional[Dict[str, Any]]: 提取的 JSON 字典或 None
    """
    # 尝试匹配 markdown 代码块
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    return None


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归合并两个字典
    
    Args:
        base: 基础字典
        override: 覆盖字典
        
    Returns:
        Dict[str, Any]: 合并后的字典
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5, sha256, sha512）
        
    Returns:
        str: 哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def get_string_hash(text: str, algorithm: str = "md5") -> str:
    """
    计算字符串哈希值
    
    Args:
        text: 字符串
        algorithm: 哈希算法
        
    Returns:
        str: 哈希值
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        List[List[Any]]: 分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    扁平化嵌套列表
    
    Args:
        nested_list: 嵌套列表
        
    Returns:
        List[Any]: 扁平化后的列表
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的文件大小
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def parse_bool(value: Any) -> bool:
    """
    解析布尔值
    
    Args:
        value: 任意值
        
    Returns:
        bool: 布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on', 't', 'y')
    return bool(value)


def deep_get(d: Dict[str, Any], path: str, default: Any = None, separator: str = ".") -> Any:
    """
    深度获取字典值
    
    Args:
        d: 字典
        path: 路径（如 "a.b.c"）
        default: 默认值
        separator: 路径分隔符
        
    Returns:
        Any: 值或默认值
    """
    keys = path.split(separator)
    current = d
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def deep_set(d: Dict[str, Any], path: str, value: Any, separator: str = ".") -> None:
    """
    深度设置字典值
    
    Args:
        d: 字典
        path: 路径（如 "a.b.c"）
        value: 值
        separator: 路径分隔符
    """
    keys = path.split(separator)
    current = d
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
