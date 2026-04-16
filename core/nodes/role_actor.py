"""
角色演绎节点

负责根据角色分配器的输出生成具体的角色扮演内容
"""

import json
import logging
import os
import re
from typing import Any, Callable, Dict, Optional

from utils import json_output, validate_schema
from schemas import RoleAssignerOutput, RoleActorOutput, PromptComponents

logger = logging.getLogger(__name__)


# 单元类型指令映射
UNIT_TYPE_INSTRUCTIONS = {
    "narrator": "\n\n重要：你是一个旁白叙事者。以第三人称叙述故事，推进时间线、交代背景。注意：不需要扮演任何角色，只需要以叙述者的口吻描写正在发生的事。",
    "environment": "\n\n重要：你是一个环境描写专家。以第三人称描写场景，包括空间、时间、光线、氛围等。注意：不需要扮演任何角色，只需要客观描写环境。",
    "action": "\n\n重要：你是一个动作描写专家。描写角色的外在表现，包括表情、动作、手势、身体语言。注意：需要基于角色卡片，描写角色的行为。",
    "dialogue": "\n\n重要：你是一个角色扮演AI。不要输出任何JSON、结构化数据或分析。只输出角色在当前情境下的自然对话和行动描述。",
    "psychology": "\n\n重要：你是一个心理描写专家。描写角色的内心世界，包括内心独白、情绪波动、心理活动。注意：需要基于角色卡片，描写角色的心理。",
    "conflict": "\n\n重要：你是一个冲突悬念大师。制造故事张力，包括矛盾冲突、悬念设置、危机升级、意外转折。注意：需要营造紧张氛围。",
}


def _build_actor_prompt(prompt_components: PromptComponents, user_info_section: str = "") -> str:
    """构建场景写作的完整提示词"""
    parts = []
    
    if prompt_components.identity:
        parts.append(f"角色设定：{prompt_components.identity}")
    
    if prompt_components.current_event:
        parts.append(f"## 当前事件\n{prompt_components.current_event}")
    
    if prompt_components.expected_reaction:
        parts.append(f"## 预期反应\n{prompt_components.expected_reaction}")
    
    if prompt_components.long_term_memory:
        parts.append("## 背景记忆\n" + "\n".join(f"- {m}" for m in prompt_components.long_term_memory))
    
    if prompt_components.short_term_memory:
        parts.append("## 本章记忆\n" + "\n".join(f"- {m}" for m in prompt_components.short_term_memory))
    
    if prompt_components.current_situation:
        parts.append(f"## 场景设定\n{prompt_components.current_situation}")
    
    if prompt_components.goals:
        parts.append(f"## 场景目标\n{prompt_components.goals}")
    
    if prompt_components.constraints:
        parts.append("## 注意事项\n" + "\n".join(f"- {c}" for c in prompt_components.constraints))
    
    if prompt_components.rag_context:
        rag_parts = ["## 该角色已经拥有的记忆和经历\n"]
        for i, ctx in enumerate(prompt_components.rag_context, 1):
            rag_parts.append(f"【经历 {i}】来源：{ctx.get('source', 'unknown')}，相似度：{ctx.get('score', 0):.2f}")
            rag_parts.append(f"{ctx.get('content', '')}\n")
        parts.append("\n".join(rag_parts))
    
    if user_info_section:
        parts.append(user_info_section)
    
    prompt = """
请根据以上设定，以指定角色的身份和视角进行角色扮演。
你需要产出符合角色身份的语言和行为，推动剧情发展，展现角色的情感变化。
注意！！！不要输出任何换行符号/n，也不用输出任何的markdown代码块类似```json，只需要将一整段直接输出。

## 输出格式（严格JSON）
你必须输出一个JSON对象，包含以下字段：
- content: 角色扮演的正文内容（小说情节、对白、动作描写等）
- summary: 一句话简述你的生成内容（不超过50字）

示例格式：
{
  "content": "正文内容应该在这里，包含角色对话和行动描写...",
  "summary": "一句话简述你的生成内容（不超过50字）"
}

请开始角色扮演，输出JSON：
""" + "\n\n".join(parts)
    
    return prompt


def _validate_output(content: str) -> bool:
    """验证输出是否有效：非空且长度 >= 50"""
    if not content or not content.strip():
        return False
    return len(content.strip()) >= 50


def _find_json_object(text: str, start_pos: int = 0) -> str:
    """使用括号匹配找到从start_pos开始的完整JSON对象"""
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if in_string:
            continue
            
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return text[start_pos:i+1]
    
    return ""


def _parse_state_change_report(content: str) -> Dict[str, Any]:
    """从生成内容中解析JSON，获取正文和状态变更报告"""
    default_report = {
        "content": "",
        "summary": "...",
    }
    
    if not content:
        return default_report
    
    original_content = content.strip()
    content = original_content
    
    def extract_fields(parsed: dict) -> dict:
        return {
            "content": parsed.get("content", ""),
            "summary": parsed.get("summary", "")
        }
    
    # ========== 预处理：清理 markdown 代码块标记 ==========
    content = re.sub(r'^```json\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^```\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    content = content.strip()
    
    # ========== 预处理：清理无效字符和 HTML 实体 ==========
    content = re.sub(r'&#\d+;', '', content)
    content = re.sub(r'&\w+;', '', content)
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
    content = content.strip()
    
    # ========== 策略A：直接解析整个内容 ==========
    if content.startswith('{') and content.endswith('}'):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "content" in parsed:
                logger.debug("[_parse_state_change_report] Strategy A: direct parse success")
                return extract_fields(parsed)
        except json.JSONDecodeError:
            pass
    
    # ========== 策略B：首尾清理后解析 ==========
    cleaned = content.strip()
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "content" in parsed:
                logger.debug("[_parse_state_change_report] Strategy B: cleaned parse success")
                return extract_fields(parsed)
        except json.JSONDecodeError:
            pass
    
    # ========== 策略C：括号匹配提取 ==========
    json_start = content.find('{')
    if json_start != -1:
        json_str = _find_json_object(content, json_start)
        if json_str:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and "content" in parsed:
                    logger.debug("[_parse_state_change_report] Strategy C: bracket match success")
                    return extract_fields(parsed)
            except json.JSONDecodeError:
                pass
    
    # ========== 策略D：正则表达式提取 ==========
    brace_count = 0
    in_string = False
    escape_next = False
    json_start = -1
    
    for i, char in enumerate(content):
        if escape_next:
            escape_next = False
            continue
        if char == '\\' and in_string:
            escape_next = True
            continue
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                if brace_count == 0:
                    json_start = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and json_start != -1:
                    json_str = content[json_start:i+1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and "content" in parsed:
                            logger.debug("[_parse_state_change_report] Strategy D: smart brace match success")
                            return extract_fields(parsed)
                    except json.JSONDecodeError:
                        pass
    
    # ========== 策略E：查找代码块内的 JSON ==========
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict) and "content" in parsed:
                logger.debug("[_parse_state_change_report] Strategy E: code block parse success")
                return extract_fields(parsed)
        except json.JSONDecodeError:
            pass
    
    # ========== 策略F：正则表达式直接提取字段 ==========
    content_match = re.search(
        r'"content"\s*:\s*"(.+?)"(?=\s*,|\s*})',
        content,
        re.DOTALL
    )
    
    if content_match:
        extracted_content = content_match.group(1)
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', content)
        if not summary_match:
            summary_match = re.search(r'"summary"\s*:\s*"(.+?)(?:"|$)', content)
        
        logger.debug("[_parse_state_change_report] Strategy F: regex extract success")
        return {
            "content": extracted_content,
            "summary": summary_match.group(1) if summary_match else "",
        }
    
    # ========== 回退：返回原始内容作为 content ==========
    logger.debug("[_parse_state_change_report] All strategies failed, using original content")
    return {
        "content": original_content,
        "summary": ""
    }


@json_output
@validate_schema(RoleActorOutput)
def role_actor(
    role_assigner_output: RoleAssignerOutput,
    chapter_id: int,
    node_id: int,
    node_type: str = "dialogue",
    feedback: str = "",
    stream_callback: Optional[Callable[[str], None]] = None,
    update_memory_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    user_theme: str = "",
    user_style: str = "",
    user_total_words: int = 0,
    user_character_count: int = 0,
    llm_client: Any = None,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    角色扮演 LLM 节点
    
    输入：RoleAssignerOutput（包含 generation_prompt）
    输出：RoleActorOutput（包含生成内容和状态变更报告）
    
    Args:
        role_assigner_output: 角色分配器输出
        chapter_id: 当前章节 ID
        node_id: 当前节点 ID
        node_type: 节点类型
        feedback: 审查反馈
        stream_callback: 流式回调函数，用于推送 token 到 UI
        update_memory_callback: 记忆更新回调函数
        user_theme: 用户主题
        user_style: 用户风格
        user_total_words: 用户总字数
        user_character_count: 用户角色数
        llm_client: LLM 客户端实例（依赖注入）
        mock_mode: 是否使用模拟模式
        
    Returns:
        Dict[str, Any]: 包含生成内容和状态变更报告的输出
    """
    if mock_mode:
        content = f"[第{chapter_id}章 - {node_id}] 这是一个模拟生成的内容，展示了角色的对话和行动。节点类型: {node_type}"
        if feedback:
            content = f"[第{chapter_id}章 - {node_id}] 【根据审查反馈修改】{feedback} 节点类型: {node_type}"
        if stream_callback:
            for char in content:
                stream_callback(char)
        return {
            "generated_content": content,
            "state_change_report": {
                "summary": ""
            }
        }
    
    generation_prompt = role_assigner_output.generation_prompt
    
    user_info_section = ""
    if user_theme:
        user_info_section = f"""
## 用户输入信息
- 主题: {user_theme}
- 风格: {user_style}
- 总字数: {user_total_words}
- 角色数: {user_character_count}
"""
    
    system_content_parts = []
    if generation_prompt.identity:
        system_content_parts.append(generation_prompt.identity)
    if generation_prompt.current_event:
        system_content_parts.append(f"\n## 当前事件\n{generation_prompt.current_event}")
    if generation_prompt.expected_reaction:
        system_content_parts.append(f"\n## 预期反应\n{generation_prompt.expected_reaction}")
    
    system_content = "\n".join(system_content_parts)
    
    system_content += UNIT_TYPE_INSTRUCTIONS.get(node_type, UNIT_TYPE_INSTRUCTIONS["dialogue"])
    
    if feedback:
        system_content += f"\n\n## 审查反馈\n请务必遵循以下要求：\n{feedback}"
    
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": _build_actor_prompt(generation_prompt, user_info_section)}
    ]
    
    max_retries = 3
    retry_count = 0
    
    while retry_count <= max_retries:
        result = llm_client.chat_with_completion_check(
            messages=messages,
            temperature=0.8,
            top_p=0.9,
            max_tokens=8192,
            stream_callback=stream_callback,
            check_interval=800,
        )
        
        content = result.get("content", "")
        
        # 检测内容是否被截断
        is_truncated = False
        if content:
            stripped = content.strip()
            if stripped and not stripped.endswith('}') and not stripped.endswith('"]'):
                is_truncated = True
                logger.warning(f"[C{chapter_id}/N{node_id}] Content appears truncated, length={len(content)}")
        
        if _validate_output(content) and not is_truncated:
            break
        
        retry_count += 1
        if retry_count <= max_retries:
            logger.warning(
                f"[C{chapter_id}/N{node_id}] Validation failed, retry {retry_count}/{max_retries}"
            )
            if stream_callback:
                stream_callback(f"\n[重试 {retry_count}/{max_retries}]\n")
        else:
            logger.error(
                f"[C{chapter_id}/N{node_id}] Validation failed after {max_retries} retries"
            )
            content = content[:50] if content else "内容生成失败"
    
    state_change_report = _parse_state_change_report(content)
    
    generated_content = state_change_report.get("content", content)
    
    if update_memory_callback:
        memory_update = {
            "chapter_id": chapter_id,
            "node_id": node_id,
            "target_character": role_assigner_output.target_character,
            "new_memories": state_change_report.get("new_memories", []),
            "emotion_shift": state_change_report.get("emotion_shift", ""),
            "new_discoveries": state_change_report.get("new_discoveries", []),
            "relationship_updates": state_change_report.get("relationship_updates", {}),
        }
        update_memory_callback(memory_update)
    
    return {
        "generated_content": generated_content,
        "state_change_report": state_change_report,
    }
