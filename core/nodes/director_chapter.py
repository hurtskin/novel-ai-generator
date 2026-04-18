"""
章节导演节点

负责根据总导演大纲生成单个章节的详细执行计划
"""

import logging
from typing import Any, Dict

from utils import json_output, validate_schema
from schemas import DirectorChapterInput, DirectorChapterOutput

logger = logging.getLogger(__name__)


# 模拟数据：章节导演输出
MOCK_DIRECTOR_CHAPTER = {
    "chapter_outline": {
        "chapter_id": 1,
        "title": "初入修仙界",
        "summary": "主角林风意外获得祖传玉佩中的修仙传承，从此踏上修仙之路。在初次修炼中，他感受到天地灵气的存在，并成功引气入体，正式成为炼气期修士。",
        "key_events": ["发现玉佩秘密", "获得修仙传承", "初次引气入体", "成为炼气期修士"],
        "characters_involved": ["林风"]
    },
    "node_sequence": [
        {
            "node_id": 1,
            "type": "narrator",
            "priority": 1,
            "description": "林风在整理祖传遗物时，意外发现玉佩中隐藏的修仙功法",
            "character": "旁白"
        },
        {
            "node_id": 2,
            "type": "environment",
            "priority": 2,
            "description": "古朴的房间里，阳光透过窗棂洒在陈旧的木桌上，玉佩在光芒中泛着温润的光泽",
            "character": "环境"
        },
        {
            "node_id": 3,
            "type": "action",
            "priority": 3,
            "description": "林风颤抖着双手捧起玉佩，指尖轻轻抚过玉佩表面那些看似普通却暗藏玄机的纹路",
            "character": "林风"
        },
        {
            "node_id": 4,
            "type": "psychology",
            "priority": 4,
            "description": "林风心中既惊又喜，脑海中闪过无数念头：这是传说中的修仙机缘吗？父母是否也是修仙者？",
            "character": "林风"
        },
        {
            "node_id": 5,
            "type": "dialogue",
            "priority": 5,
            "description": "『原来如此...这就是修仙之道』林风喃喃自语，眼中闪烁着前所未有的光芒",
            "character": "林风"
        },
        {
            "node_id": 6,
            "type": "conflict",
            "priority": 6,
            "description": "就在林风沉浸在获得传承的喜悦中时，窗外突然传来一阵异样的灵气波动，似乎有修士正在附近斗法",
            "character": "旁白"
        }
    ],
    "node_count": 6,
    "character_presence_plan": {
        "林风": [1, 2, 3, 4, 5, 6]
    },
    "genre_specific": {
        "genre": "novel",
        "cultivation_stage": "炼气期",
        "realm": "凡人界"
    }
}


@json_output
@validate_schema(DirectorChapterOutput)
def director_chapter(
    input_data: DirectorChapterInput,
    llm_client: Any,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    章节导演节点
    
    根据总导演大纲生成指定章节的详细执行计划
    
    Args:
        input_data: 包含章节ID、总导演输出、文体等信息的输入数据
        llm_client: LLM 客户端实例（依赖注入）
        
    Returns:
        Dict[str, Any]: 包含章节大纲、节点序列、角色出场计划等的输出
    """
    if mock_mode:
        return MOCK_DIRECTOR_CHAPTER
    
    director_general_output = input_data.director_general_output
    if hasattr(director_general_output, 'model_dump'):
        director_general_output = director_general_output.model_dump()
    elif hasattr(director_general_output, 'dict'):
        director_general_output = director_general_output.dict()
    
    if isinstance(director_general_output, dict) and 'character_cards' in director_general_output:
        character_cards = director_general_output.get('character_cards', [])
        if character_cards and hasattr(character_cards[0], 'model_dump'):
            director_general_output['character_cards'] = [
                card.model_dump() if hasattr(card, 'model_dump') else card
                for card in character_cards
            ]
    
    logger.debug(f"[director_chapter] director_general_output type = {type(director_general_output)}")
    
    chapter_outline = None
    outline_list = director_general_output.get("outline", [])
    for ch in outline_list:
        if isinstance(ch, dict) and ch.get("chapter_id") == input_data.chapter_id:
            chapter_outline = ch
            break

    if not chapter_outline:
        chapter_outline = {
            "chapter_id": input_data.chapter_id,
            "title": f"第{input_data.chapter_id}章",
            "summary": "自动生成的章节大纲",
            "key_events": ["情节发展", "角色互动"],
            "characters_involved": [],
        }

    genre_instructions = {
        "novel": "本章为小说文体，注重情节推进和心理描写。",
        "script": "本章为剧本格式，包含场景指示和对白。",
        "game_story": "本章为游戏叙事，包含分支选项提示。",
        "dialogue": "本章为对话文体，强调多轮交互。",
        "article": "本章为文章文体，逻辑清晰，论证有力。",
    }
    genre_hint = genre_instructions.get(input_data.genre, genre_instructions["novel"])

    unit_type_definitions = """
## 节点单元类型定义（必须严格遵循）
本章的每个节点必须属于以下6种单元类型之一，生成节点序列时必须包含所有类型：

1. **narrator（旁白叙事）**：时间推进、背景交代、总结过渡、场景切换
   - 职责：推进故事时间线、交代背景信息、以第三人称叙述
   - 示例：三天后、傍晚时分、夜幕降临、场景从室内转到室外

2. **environment（环境描写）**：空间场景、时间氛围、光线色彩、环境细节
   - 职责：构建故事发生的场景、营造氛围
   - 示例：雨后的街道、昏暗的灯光、远处传来钟声

3. **action（动作描写）**：面部表情、肢体动作、身体语言、手势细节
   - 职责：刻画角色的外在表现
   - 示例：皱起眉头、缓缓站起身、双手不自觉地颤抖

4. **dialogue（角色对话）**：台词内容、说话方式、对话节奏、潜台词
   - 职责：编写角色之间的对话
   - 示例： 『我们必须离开这里。』她低声说道。

5. **psychology（角色心理）**：内心独白、情绪波动、心理活动、感觉感受
   - 职责：刻画角色的内心世界
   - 示例：她心里涌起一股不安，那个念头挥之不去

6. **conflict（冲突/悬念）**：矛盾冲突、悬念设置、危机升级、意外转折
   - 职责：制造故事张力、推动情节发展
   - 示例：就在这时，门后传来脚步声...
"""

    user_info_section = ""
    if input_data.user_theme:
        user_info_section = f"""
## 用户输入信息
- 主题: {input_data.user_theme}
- 风格: {input_data.user_style}
- 总字数: {input_data.user_total_words}
- 角色数: {input_data.user_character_count}
"""

    feedback_section = ""
    if input_data.feedback:
        feedback_section = f"""
## 上一轮审查反馈（请根据此反馈调整内容）
{input_data.feedback}
"""

    prompt = f"""作为章节导演，请根据总导演大纲生成第 {input_data.chapter_id} 章的详细执行计划。

## 总大纲中的章节列表
{outline_list}

## 章节信息
- 章节ID: {input_data.chapter_id}
- 标题: {chapter_outline.get('title', '')}
- 摘要: {chapter_outline.get('summary', '')}
- 关键事件: {', '.join(chapter_outline.get('key_events', []))}
- 涉及角色: {', '.join(chapter_outline.get('characters_involved', []))}
- 固定角色姓名: {', '.join(director_general_output.get('character_names', []))}

## 角色卡片（每个角色的详细信息，后续节点必须严格遵循）
{director_general_output.get('character_cards', [])}

## 文体要求
{genre_hint}
{user_info_section}
{feedback_section}

## 节点单元类型定义（必须严格遵循）
{unit_type_definitions}

## 重要规则
1. **必须使用固定角色姓名**：必须严格使用上述 character_names 中的姓名，禁止使用"主角1"、"主角2"、"主角A"等代称
2. **必须遵循角色卡片**：所有角色行为、对话必须符合角色卡片的性格设定
3. 必须输出真实的章节内容，禁止使用"描述"、"示例"、"..."等占位符
4. 每个JSON字段的值都必须是具体的、真实的描述
5. **查看当前章节进度，请不要生成不属于当前章节的内容
6. 例如：summary应该是"描述一个阳光明媚的下午，主角在咖啡馆遇到了改变他一生的人"，不是"章节摘要"
7. **重要**：node_sequence 必须包含所有6种单元类型（narrator, environment, action, dialogue, psychology, conflict），不能只有 dialogue
8. node_id：应该是阿拉伯数字（1、2、3）

## 输出格式（直接输出JSON，不要包含其他文字）
你必须严格遵循以下JSON Schema输出，不允许任何解释、说明或JSON以外的内容：

```json
{{
  "type": "object",
  "properties": {{
    "chapter_outline": {{
      "type": "object",
      "properties": {{
        "chapter_id": {{"type": "integer"}},
        "title": {{"type": "string"}},
        "summary": {{"type": "string"}},
        "key_events": {{"type": "array", "items": {{"type": "string"}}}},
        "characters_involved": {{"type": "array", "items": {{"type": "string"}}}}
      }},
      "required": ["chapter_id", "title", "summary", "key_events", "characters_involved"]
    }},
    "node_sequence": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "node_id": {{"type": "int"}},
          "type": {{"type": "string", "enum": ["narrator", "environment", "action", "dialogue", "psychology", "conflict"]}},
          "priority": {{"type": "integer"}},
          "description": {{"type": "string"}},
          "character": {{"type": "string"}}
        }},
        "required": ["node_id", "type", "priority", "description", "character"]
      }}
    }},
    "node_count": {{"type": "integer"}},
    "character_presence_plan": {{
      "type": "object",
      "additionalProperties": {{
        "type": "array",
        "items": {{"type": "integer"}}
      }}
    }},
    "genre_specific": {{"type": "object"}}
  }},
  "required": ["chapter_outline", "node_sequence", "node_count", "character_presence_plan", "genre_specific"]
}}

STRICT RULES:
1. 只输出JSON，不要输出任何其他内容
2. 不要输出markdown代码块标记
3. 不要输出任何解释、说明或分析
4. 直接输出纯JSON对象
"""

    messages = [
        {"role": "system", "content": "你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。"},
        {"role": "user", "content": prompt}
    ]

    result = llm_client.chat(messages=messages)

    return result.get("content", "{}")
