"""
记忆总结节点

负责将原始记忆片段压缩为结构化的记忆卡片
"""

import json
import logging
from typing import Any, Dict, List

from utils import json_output
from schemas import RawMemory

logger = logging.getLogger(__name__)


@json_output
def memory_summarizer(
    raw_memories: List[RawMemory],
    llm_client: Any
) -> List[Dict[str, Any]]:
    """
    记忆总结节点
    
    将原始记忆片段压缩为结构化的记忆卡片
    
    Args:
        raw_memories: 原始记忆片段列表
        llm_client: LLM 客户端实例（依赖注入）
        
    Returns:
        List[Dict[str, Any]]: 结构化的记忆卡片列表
    """
    prompt = _build_summarization_prompt(raw_memories)
    
    messages = [
        {"role": "system", "content": "你是一个记忆压缩专家。你的任务是将原始记忆片段压缩为结构化的记忆卡片。"},
        {"role": "user", "content": prompt}
    ]
    
    response = llm_client.chat(
        messages=messages,
        temperature=0.3,
        top_p=0.9,
        max_tokens=4096
    )

    content = response.content
    
    try:
        cards = json.loads(content)
        if isinstance(cards, dict) and "summary_cards" in cards:
            cards = cards["summary_cards"]
        if not isinstance(cards, list):
            cards = [cards]
    except json.JSONDecodeError:
        cards = []
    
    return cards


def _build_summarization_prompt(raw_memories: List[RawMemory]) -> str:
    """
    构建记忆总结提示词
    
    Args:
        raw_memories: 原始记忆片段列表
        
    Returns:
        str: 提示词
    """
    memories_text = []
    for i, mem in enumerate(raw_memories):
        mem_dict = {
            "character": mem.character,
            "content": mem.content,
            "emotion": mem.emotion
        }
        memories_text.append(f"--- 记忆 {i+1} ---\n{json.dumps(mem_dict, ensure_ascii=False)}")
    
    memories_section = "\n".join(memories_text)
    
    prompt = f"""请将以下原始记忆片段压缩为结构化的记忆卡片。

## 原始记忆
{memories_section}

## 输出要求
请生成 JSON 数组，每个卡片包含以下字段：
- event_id: 事件ID，格式如 E-章节-序号
- timestamp: 时间戳，描述性如"案发后第3天雨夜"
- location: 发生地点
- core_action: 核心动作/发现，简短描述
- emotion_marks: 情感标记，dict格式如{{"角色名": "情感描述"}}
- relationship_changes: 关系变化，dict格式如{{"角色A→角色B": "变化描述"}}
- key_quote: 关键引言/台词
- future_impacts: 未来影响，关联的事件ID列表
- source_index: 来源索引，格式如"章5/节点2/字数"

请仅返回JSON数组，不要包含其他文字。
"""
    return prompt
