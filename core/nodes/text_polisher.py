"""
文本润色节点

负责对生成的章节文本进行润色，提升文学性和可读性
"""

import logging
from typing import Any, Callable, Dict, Optional

from utils import json_output, validate_schema
from schemas import TextPolisherInput, TextPolisherOutput

logger = logging.getLogger(__name__)


@json_output
@validate_schema(TextPolisherOutput)
def text_polisher(
    input_data: TextPolisherInput,
    llm_client: Any,
    stream_callback: Optional[Callable[[str], None]] = None,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    文本润色 LLM 节点

    输入：TextPolisherInput（包含当前章节的文本）
    输出：TextPolisherOutput（包含润色后的文本）

    Args:
        input_data: 包含需要润色的章节文本
        llm_client: LLM 客户端实例（依赖注入）
        stream_callback: 流式回调函数，用于推送 token 到 UI
        mock_mode: 是否使用模拟模式
        
    Returns:
        Dict[str, Any]: 包含润色后文本的输出
    """
    if mock_mode:
        polished = f"[润色后] {input_data.chapter_text[:100]}..."
        if stream_callback:
            for char in polished:
                stream_callback(char)
        return {"polished_text": polished}

    system_content = """你是一位专业的文本润色专家。你的任务是对输入的文本进行润色，提升其文学性和可读性。

润色要求：
1. 保持原文的核心意思和情节不变
2. 优化语言表达，使其更加流畅自然
3. 增强描写细节，提升画面感
4. 修正语法错误和不通顺的表达
5. 保持原有的文体风格
6. 将原文啰嗦部分进行删改
7. 将原文衔接突兀处进行添加细节
8. 将原文不一致的物体等名称保持一致性

注意：
- 不要改变故事情节
- 不要增减角色
- 不要改变人物性格
- 只优化文字表达"""

    user_content = f"""请对以下章节文本进行润色：

## 原始文本
{input_data.chapter_text}

## 输出要求
请直接输出润色后的文本，不要添加任何解释、说明或额外的格式标记。"""

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

    response = llm_client.chat_with_completion_check(
        messages=messages,
        temperature=0.7,
        top_p=0.9,
        max_tokens=16384,
        stream_callback=stream_callback,
        check_interval=800,
    )

    polished_text = response.content

    return {"polished_text": polished_text}
