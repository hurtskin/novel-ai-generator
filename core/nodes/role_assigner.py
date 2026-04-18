"""
角色分配节点

负责为当前节点生成角色扮演提示，根据角色档案、记忆、关系和物品状态生成 generation_prompt
"""

import json
import logging
import re
from typing import Any, Dict

from utils import validate_schema
from schemas import RoleAssignerInput, RoleAssignerOutput, PromptComponents

logger = logging.getLogger(__name__)


def _get_role_assigner_genre_instructions(genre: str) -> str:
    """获取角色分配器的文体指令"""
    genre_map = {
        "novel": "novel：第三人称有限视角，心理描写丰富，注重角色内心变化",
        "script": "script：场景镜头和对白格式，动作指示清晰，每场戏有明确目的",
        "game_story": "game_story：分支选择和状态机影响，预留触发条件，考虑玩家体验",
        "dialogue": "dialogue：多轮对话和记忆累积，对话体现关系演变，关键节点清晰",
        "article": "article：论点论据结构，中心论点明确，逻辑递进清晰",
    }
    return genre_map.get(genre, "")


@validate_schema(schema_class=RoleAssignerOutput)
def role_assigner(
    input_data: RoleAssignerInput,
    llm_client: Any,
    mock_mode: bool = False
) -> RoleAssignerOutput:
    """
    角色分配节点
    
    为当前节点生成角色扮演提示
    
    Args:
        input_data: 包含角色档案、当前节点、记忆等信息的输入数据
        llm_client: LLM 客户端实例（依赖注入）
        mock_mode: 是否使用模拟模式
        
    Returns:
        RoleAssignerOutput: 包含目标角色和生成提示的输出
    """
    if mock_mode:
        return RoleAssignerOutput(
            target_character=input_data.character_profile.name,
            generation_prompt=PromptComponents(
                identity=f"你是{input_data.character_profile.name}",
                long_term_memory=input_data.generated_summaries if input_data.generated_summaries else [],
                short_term_memory=[],
                summary=input_data.generated_summaries if input_data.generated_summaries else [],
                recent_events="",
                current_situation=input_data.current_situation,
                relationships={},
                items=[],
                goals="完成章节内容",
                constraints=["不偏离主线"],
                genre_hints="小说风格"
            )
        )
    
    genre_hints = _get_role_assigner_genre_instructions(input_data.genre)
    node_type = input_data.current_node.type if input_data.current_node else "dialogue"

    unit_type_prompts = {
        "narrator": """
## 单元类型：旁白叙事（Narrator）
你是旁白叙事者，负责推进故事时间线、交代背景信息、进行场景切换。
你不需要扮演任何角色，而是以第三人称视角叙述故事。

职责：
- 时间推进：三天后、傍晚时分、夜幕降临
- 背景交代：地点变换、人物关系变化
- 总结过渡：承上启下、场景切换
- 叙述氛围：奠定基调、情绪铺垫

示例输出：
"三天后，城里的局势变得更加紧张。街头的士兵越来越多，每个人的脸上都写着不安。"

请根据以下信息生成旁白叙事内容。
""",
        "environment": """
## 单元类型：环境描写（Environment）
你是环境描写专家，负责构建故事发生的场景、营造氛围。
你不需要扮演任何角色，而是以第三人称视角描写环境。

职责：
- 空间场景：室内/室外、地点特征
- 时间氛围：早晨/夜晚、季节特征
- 光线色彩：明亮/昏暗、颜色描写
- 环境细节：声音、气味、温度

示例输出：
"雨后的青石板路泛着湿润的光泽，远处传来教堂的钟声。街边的灯笼在微风中轻轻摇晃，投下摇曳的影子。"

请根据以下信息生成环境描写内容。
""",
        "action": """
## 单元类型：动作描写（Action）
你是动作描写专家，负责刻画角色的外在表现。
你需要根据角色卡片，描写角色的表情、动作、手势、身体语言。

职责：
- 面部表情：皱眉、微笑、瞪眼、脸红
- 肢体动作：挥手、转身、鞠躬、点头
- 身体语言：紧张、放松、僵硬、颤抖
- 手势细节：搓手、抱臂、捂脸、叉腰

示例输出：
"他皱起眉头，右手不自觉地摩挲着茶杯边缘，嘴唇微微张开却什么也没说。"

请根据以下角色信息生成动作描写内容。
""",
        "dialogue": """
## 单元类型：角色对话（Dialogue）
你是对话写作专家，负责编写角色之间的对话。
你需要根据角色卡片，生成符合角色性格的对话内容。

职责：
- 台词内容：角色说的话
- 说话方式：语气、语速、口头禅
- 对话节奏：谁先开口、如何接话
- 潜台词：言外之意

示例输出：
"『我们真的没有别的选择了吗？』她低声问道，眼中闪过一丝不安。
『没有。』他回答，声音里带着一丝决绝，『这是我们唯一的机会。』"

请根据以下角色信息生成对话内容。
""",
        "psychology": """
## 单元类型：角色心理（Psychology）
你是心理描写专家，负责刻画角色的内心世界。
你需要根据角色卡片，描写角色的内心独白、情绪波动、心理活动。

职责：
- 内心独白：角色在想什么
- 情绪波动：喜怒哀乐的变化
- 心理活动：犹豫、决定、挣扎
- 感觉感受：紧张、恐惧、温暖

示例输出：
"她心里涌起一股不安，那个念头挥之不去。理智告诉她应该离开，但情感却让她无法挪动脚步。"

请根据以下角色信息生成心理描写内容。
""",
        "conflict": """
## 单元类型：冲突/悬念（Conflict）
你是冲突悬念大师，负责制造故事张力、推动情节发展。
你需要设置矛盾冲突、悬念、危机升级或意外转折。

职责：
- 矛盾冲突：人物之间的对立、冲突
- 悬念设置：埋下伏笔、制造疑问
- 危机升级：危险逼近、紧张加剧
- 意外转折：出人意料的情节

示例输出：
"『站住别动！』一个低沉的声音从黑暗中传来。她猛地转身，却只看到一片漆黑的巷子。脚步声越来越近..."

请根据以下信息生成冲突悬念内容。
"""
    }

    unit_type_prompt = unit_type_prompts.get(node_type, unit_type_prompts["dialogue"])

    identity = f"你是{input_data.character_profile.name}，{input_data.character_profile.background}，{input_data.character_profile.personality}"

    system_prompt = f"""你是角色分配器，负责为当前节点生成角色扮演提示。
根据角色档案、记忆、关系和物品状态，生成适合该节点的角色 generation_prompt。

你必须输出一个完整的 generation_prompt，包含所有必要信息让下一个节点能够准确扮演该角色。

STRICT RULES:
1. 只输出JSON，不要输出任何其他内容
2. 不要输出markdown代码块标记
3. 不要输出任何解释、说明或分析
4. 直接输出纯JSON对象"""

    user_prompt = f"""请根据以下信息生成 generation_prompt：

{unit_type_prompt}

## 审查反馈（如有，请根据反馈调整生成内容）
{f"如有审查反馈，请务必遵循以下要求改进生成内容：\n{input_data.feedback}" if input_data.feedback else "无审查反馈"}

## 固定角色姓名列表（必须严格使用这些姓名，禁止使用其他姓名）
{', '.join(input_data.character_names) if input_data.character_names else '无'}

## 所有角色卡片（每个角色的详细信息，生成提示时必须严格遵循）
{json.dumps(input_data.character_cards, ensure_ascii=False, indent=2) if input_data.character_cards else '无'}

## 当前节点信息
- 节点ID: {input_data.current_node.node_id}
- 节点类型: {input_data.current_node.type}
- 本节点场景描述: {input_data.current_node.description}
- 指定扮演角色: {input_data.current_node.target_character or input_data.character_profile.name}

## 当前角色档案（必须使用上述固定角色姓名）
- 姓名: {input_data.character_profile.name}
- 角色: {input_data.character_profile.role}
- 背景: {input_data.character_profile.background}
- 性格特点: {input_data.character_profile.personality}
- 目标: {input_data.character_profile.goals}
- 与其他角色的关系: {json.dumps(input_data.character_profile.relationships, ensure_ascii=False)}


## 当前情境（这是当前场景正在发生的事）
{input_data.current_situation}
## 当前已经完成的内容
{input_data.generated_summaries}

## 你需要做的事情
根据上述单元类型的职责说明，生成对应的 generation_prompt。

## RAG 检索指令
如果是角色身份（不是则留空），你需要生成检索语句，用于查找该角色历史记忆的相关信息。检索语句应该：
1. 描述当前场景中需要回顾的相关记忆内容
2. 包含关键角色名、场景地点、情感状态等
3. 最多生成 3 个检索语句

例如：
- "角色A在书房思考"
- "角色B与角色C的对话"
- "夜晚书房烛光场景"

请生成 JSON 格式的 generation_prompt：
{{
    "identity": "你是[角色身份/narrator: 你是旁白叙事者，以第三人称叙述故事]",
    "current_event": "当前场景中正在发生的事件: [详细描述]",
    "expected_reaction": "[根据单元类型填写：dialogue-对话内容，action-动作描写，psychology-心理描写，environment-环境描写，narrator-旁白叙述，conflict-冲突悬念]",
    "long_term_memory": ["长期记忆片段列表"],
    "short_term_memory": ["短期记忆片段列表"],
    "recent_events": "最近事件描述",
    "current_situation": "当前情境描述",
    "relationships": {{"其他角色": "关系描述"}},
    "items": ["当前持有的物品"],
    "goals": "当前目标",
    "constraints": ["行为约束列表"],
    "genre_hints": "文体特定提示",
    "rag_queries": ["检索语句1", "检索语句2"]
}}

**重要约束**：
1. **根据单元类型调整 identity 字段**：
   - narrator: "你是旁白叙事者，以第三人称叙述故事"
   - environment: "你是环境描写专家，以第三人称描写场景"
   - action: "你是动作描写专家，描写角色的外在表现"
   - dialogue: "identity 字段必须以"你是XXX"开头，明确角色姓名"
   - psychology: "你是心理描写专家，刻画角色的内心世界"
   - conflict: "你是冲突悬念大师，制造故事张力"
2. current_event 必须详细描述当前场景正在发生的事
3. expected_reaction 必须根据单元类型的职责生成对应内容
4. 所有内容必须严格使用固定角色姓名列表中的姓名，禁止使用"主角1"、"主角2"、"主角A"等代称
5. 可以创造新龙套角色，但龙套角色必须有意义，且只能由旁白叙事者进行诉说，不需要给龙套角色生成角色卡片
6. **必须遵循角色卡片**：所有行为和对话必须符合角色卡片的性格设定
7. **查看当前节点的进度，不要生成不属于当前节点的内容，更不要重复生成已经生成过的节点的内容"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = llm_client.chat(messages)
    content = response.content
    
    logger.debug(f"[role_assigner] raw content: {content[:200]}")
    
    json_str = content.strip()
    json_str = re.sub(r'^```json\s*', '', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'^```\s*', '', json_str)
    json_str = re.sub(r'\s*```$', '', json_str)
    json_str = json_str.strip()
    
    logger.debug(f"[role_assigner] parsed json_str: {json_str[:200]}")
    
    try:
        generation_prompt_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"[role_assigner] JSON parse error: {e}")
        match = re.search(r'\{[^{}]*\}', json_str, re.DOTALL)
        if match:
            try:
                generation_prompt_dict = json.loads(match.group())
            except:
                generation_prompt_dict = {}
        else:
            generation_prompt_dict = {}
    
    logger.debug(f"[role_assigner] generation_prompt_dict: {generation_prompt_dict}")
    
    try:
        prompt_components = PromptComponents(**generation_prompt_dict)
    except Exception as e:
        logger.warning(f"[role_assigner] PromptComponents validation error: {e}, using default")
        prompt_components = PromptComponents(
            identity=f"你是{input_data.character_profile.name}",
            long_term_memory=input_data.generated_summaries if input_data.generated_summaries else [],
            short_term_memory=[],
            summary=input_data.generated_summaries if input_data.generated_summaries else [],
            recent_events="",
            current_situation=input_data.current_situation if hasattr(input_data, 'current_situation') else "",
            relationships={},
            items=[],
            goals="完成章节内容",
            constraints=["不偏离主线"],
            genre_hints="小说风格"
        )
    
    rag_queries = generation_prompt_dict.get("rag_queries", [])
    
    output_data = RoleAssignerOutput(
        target_character=input_data.character_profile.name,
        generation_prompt=prompt_components,
        feedback=input_data.feedback,
        rag_queries=rag_queries
    )

    return output_data
