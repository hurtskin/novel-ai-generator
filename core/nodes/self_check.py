"""
自检节点

负责审阅当前节点的内容，判断是否与总导演的标准有矛盾冲突
"""

import json
import logging
import random
from typing import Any, Dict, List

from utils import json_output
from schemas import SelfCheckOutput

logger = logging.getLogger(__name__)


@json_output
def self_check(
    director_general_standards: Dict[str, Any],
    current_chapter_content: str,
    summary: List[str],
    previous_feedback: str = "",
    chapter_id: int = 0,
    node_id: int = 0,
    llm_client: Any = None,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    自检节点
    
    审阅当前节点的内容，判断是否与总导演的标准有矛盾冲突
    
    Args:
        director_general_standards: 总导演标准
        current_chapter_content: 当前章节内容
        summary: 全局记忆摘要
        previous_feedback: 上一轮审查反馈
        chapter_id: 章节ID
        node_id: 节点ID
        llm_client: LLM 客户端实例（依赖注入）
        mock_mode: 是否使用模拟模式
        
    Returns:
        Dict[str, Any]: 包含是否需要修改、问题类型、具体问题、改进建议的输出
    """
    if mock_mode:
        should_pass = random.random() > 0.5
        
        if should_pass:
            return {
                "needs_revision": False,
                "issue_types": [],
                "specific_issues": [],
                "improvement_suggestions": "模拟通过检查"
            }
        else:
            issues = [
                {
                    "type": "角色",
                    "issue": "角色行为与设定不一致",
                    "suggestion": "请加强角色行为的描写，确保角色行为符合其设定性格"
                },
                {
                    "type": "情节",
                    "issue": "情节发展过于突兀",
                    "suggestion": "请增加情节过渡，使故事发展更自然流畅"
                },
                {
                    "type": "情感",
                    "issue": "情感转折不够自然",
                    "suggestion": "请铺垫情感变化的前因后果，使情感转折更真实"
                },
                {
                    "type": "情节",
                    "issue": "场景衔接不流畅",
                    "suggestion": "请增加场景之间的过渡描写"
                },
                {
                    "type": "角色",
                    "issue": "对话缺乏张力",
                    "suggestion": "请增加对话中的冲突和悬念"
                }
            ]
            selected = random.choice(issues)
            return {
                "needs_revision": True,
                "issue_types": [selected["type"]],
                "specific_issues": [selected["issue"]],
                "improvement_suggestions": selected["suggestion"]
            }
    
    standards_summary = json.dumps(director_general_standards, ensure_ascii=False, indent=2)
    memory_summary = json.dumps(summary, ensure_ascii=False, indent=2)
    
    prompt = f"""作为文章编辑，请审阅当前节点的内容，判断文中和总导演的标准是否有较大的矛盾冲突处。

## 当前审查位置
当前处于第 {chapter_id} 章节的第 {node_id} 节点

## 总导演标准
{standards_summary}

## 全局记忆（已生成的内容）
{memory_summary}

## 当前节点内容
{current_chapter_content}

## 上一轮审查反馈（如有）
{previous_feedback}

## 判断标准
请判断以下各项是否满足：
1. 内容完整性：内容是否完整、有无被截断（段落是否突然中断、情节是否突兀结束）
2. 角色一致性：角色行为是否与角色设定一致，角色前后名称是否一致
3. 情节符合度：情节发展是否符合章节大纲
4. 记忆一致性：角色关系变化是否与记忆一致
5. 情感合理性：情感转折是否合理

请输出 JSON 格式的检查结果：
{{
    "needs_revision": true/false,
    "issue_types": ["一致性", "记忆", "角色", "情节", "伏笔", "内容完整性"] 中的一项或多项,
    "specific_issues": ["具体问题描述1", "具体问题描述2"],
    "improvement_suggestions": "改进建议，需要详细说明如何修复问题"
}}

注意：内容长度足够且无严重问题时返回 needs_revision: false
"""
    
    messages = [
        {"role": "system", "content": "你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。"},
        {"role": "user", "content": prompt}
    ]
    
    result = llm_client.chat(messages=messages)
    
    return result.get("content", "{}")


def validate_loop_guard(retry_count: int, max_retries: int) -> bool:
    """
    验证循环守卫
    
    Args:
        retry_count: 当前重试次数
        max_retries: 最大重试次数
        
    Returns:
        bool: 是否允许继续重试
    """
    return retry_count <= max_retries


def handle_revision_needed(
    improvement_suggestions: str,
    retry_count: int,
    max_retries: int
) -> Dict[str, Any]:
    """
    处理需要修改的情况
    
    Args:
        improvement_suggestions: 改进建议
        retry_count: 当前重试次数
        max_retries: 最大重试次数
        
    Returns:
        Dict[str, Any]: 包含处理动作的字典
    """
    if validate_loop_guard(retry_count, max_retries):
        return {
            "action": "retry",
            "target": "DIRECTOR_CHAPTER",
            "feedback": improvement_suggestions,
            "retry_count": retry_count + 1
        }
    else:
        return {
            "action": "terminate",
            "reason": "max_retries_exceeded",
            "message": f"已达到最大重试次数 ({max_retries})，请人工介入处理。"
        }
