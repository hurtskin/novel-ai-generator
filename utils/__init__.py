"""
工具模块

提供项目中使用的装饰器和通用辅助函数

模块结构：
- decorators: 装饰器（@json_output, @validate_schema）
- helpers: 通用辅助函数

使用示例：
    from utils import json_output, validate_schema
    from utils import safe_json_loads, truncate_string
    
    # 使用装饰器
    @json_output
    @validate_schema(MySchema)
    def my_function():
        return '{"key": "value"}'
    
    # 使用辅助函数
    data = safe_json_loads(json_str, default={})
    short_text = truncate_string(long_text, 100)
"""

from utils.decorators import (
    json_output,
    validate_schema,
    SchemaValidationError,
)

from utils.helpers import (
    safe_json_loads,
    safe_json_dumps,
    truncate_string,
    clean_text,
    extract_json_from_text,
    merge_dicts,
    ensure_dir,
    get_file_hash,
    get_string_hash,
    chunk_list,
    flatten_list,
    format_file_size,
    parse_bool,
    deep_get,
    deep_set,
)

__all__ = [
    # decorators
    "json_output",
    "validate_schema",
    "SchemaValidationError",
    # helpers
    "safe_json_loads",
    "safe_json_dumps",
    "truncate_string",
    "clean_text",
    "extract_json_from_text",
    "merge_dicts",
    "ensure_dir",
    "get_file_hash",
    "get_string_hash",
    "chunk_list",
    "flatten_list",
    "format_file_size",
    "parse_bool",
    "deep_get",
    "deep_set",
]
