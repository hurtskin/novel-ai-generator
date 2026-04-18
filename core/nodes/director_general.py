"""
总导演节点

负责根据用户输入生成完整的作品大纲，包括世界观、写作风格、章节大纲、角色设定等
"""

import logging
from typing import Any, Dict

from utils import json_output, validate_schema
from schemas import DirectorGeneralInput, DirectorGeneralOutput, CharacterCard, GenreSpecific

logger = logging.getLogger(__name__)

# Mock 数据（DirectorGeneralOutput 对象）
MOCK_DIRECTOR_GENERAL = DirectorGeneralOutput(
    world_building="22世纪末，人类发明了曲速引擎，实现了星际旅行",
    writing_style="科幻现实主义，第三人称全知，中速节奏，文学性语言",
    outline=[
        "第一章：启程 - 星际飞船启航，船员准备离开地球",
        "第二章：危机 - 遭遇未知威胁，能源危机出现",
        "第三章：抵达 - 发现新星球，建立殖民地"
    ],
    chapter_count=3,
    characters=[
        "李明：舰长，退役军人，果敢的性格，目标找到新家园",
        "艾琳：科学家，物理学家，理性思维，目标研究新科技"
    ],
    character_names=["李明", "艾琳"],
    character_cards=[
        CharacterCard(
            name="李明",
            role="舰长",
            background="退役军人",
            personality="果敢、坚毅、有责任心",
            goals="找到新家园，保护船员安全",
            relationships={"艾琳": "同事"},
            speaking_style="简洁有力",
            habits=["每天检查飞船设备", "记录航行日志"],
            strengths=["领导力", "决策果断"],
            weaknesses=["有时过于冒险"],
            fears=["失去船员"],
            secrets=["隐瞒了过去的失败"]
        ),
        CharacterCard(
            name="艾琳",
            role="科学家",
            background="物理学家",
            personality="理性、好奇、冷静",
            goals="研究新科技，解开宇宙奥秘",
            relationships={"李明": "同事"},
            speaking_style="专业术语多",
            habits=["做实验记录", "思考问题"],
            strengths=["专业知识", "分析能力"],
            weaknesses=["不擅长社交"],
            fears=["实验失败"],
            secrets=["偷偷进行私人研究"]
        )
    ],
    conflict_design="寻找新家园与未知威胁的对立，能源短缺，船员矛盾，整个人类的未来",
    foreshadowing=[
        "能源危机的伏笔在第一章埋下",
        "外来信号的来源在第二章揭示"
    ],
    character_arcs=[
        "李明：从保守到冒险精神的转变",
        "艾琳：从理性到接受不确定性的转变"
    ],
    tone="宏大而温情，充满希望",
    genre_specific=GenreSpecific(
        genre="novel",
        specific_fields={"硬科幻": "强调技术细节"}
    )
)


@json_output
@validate_schema(DirectorGeneralOutput)
def director_general(
    input_data: DirectorGeneralInput,
    llm_client: Any,
    mock_mode: bool = False
) -> Dict[str, Any]:
    """
    总导演节点
    
    根据用户输入的主题、风格、字数等信息，生成完整的作品大纲
    
    Args:
        input_data: 包含主题、风格、字数、角色数、文体等信息的输入数据
        llm_client: LLM 客户端实例（依赖注入）
        mock_mode: 是否使用模拟模式
        
    Returns:
        Dict[str, Any]: 包含世界观、写作风格、章节大纲、角色设定等的输出
    """
    if mock_mode:
        return MOCK_DIRECTOR_GENERAL
    
    genre_instructions = {
        "novel": "强调章节结构和角色弧光，注重心理描写和情节推进。",
        "script": "强调场景镜头和对白格式，每个场景包含舞台指示。",
        "game_story": "强调分支选择和状态机，考虑玩家决策影响。",
        "dialogue": "强调多轮对话和记忆累积，对话要自然流畅。",
        "article": "强调论点论据结构，逻辑清晰，论证有力。"
    }
    
    genre_hint = genre_instructions.get(input_data.genre, genre_instructions["novel"])
    
    prompt = f"""作为小说总导演，请根据以下信息创作完整的作品大纲。

## 基本信息
- 主题: {input_data.theme}
- 风格: {input_data.style}
- 总字数: {input_data.total_words}
- 角色数: {input_data.character_count}
- 文体: {input_data.genre}

## 文体要求
{genre_hint}

## 重要输出规则
1. 你必须输出真实的内容，禁止使用"描述"、"示例"、"..."等占位符
2. 每个JSON字段的值都必须是具体的、真实的描述
3. 例如：world_building应该是"1990年代的北京，改革开放初期，胡同文化与现代都市的碰撞"
4. 例如：characters应该是["林晓：25岁，从南方来北京打工的程序员，性格内向但执着"]，不是["角色1描述"]
5. **重要**：character_names 必须列出所有角色的具体姓名，后续所有章节必须使用这些固定姓名，不能自行创造新姓名
6. **重要**：character_cards 必须为每个角色生成详细的角色卡片，包含性格特点、说话风格、习惯、优点、缺点、恐惧、秘密等

## 输出格式
你必须严格遵循以下JSON Schema输出，不允许任何解释、说明或JSON以外的内容：

'''json
{{
  "type": "object",
  "properties": {{
    "world_building": {{"type": "string"}},
    "writing_style": {{"type": "string"}},
    "outline": {{"type": "array", "items": {{"type": "string"}}}},
    "characters": {{"type": "array", "items": {{"type": "string"}}}},
    "character_names": {{"type": "array", "items": {{"type": "string"}}}},
    "character_cards": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "name": {{"type": "string"}},
          "role": {{"type": "string"}},
          "background": {{"type": "string"}},
          "personality": {{"type": "string"}},
          "goals": {{"type": "string"}},
          "relationships": {{"type": "object", "additionalProperties": {{"type": "string"}}}},
          "speaking_style": {{"type": "string"}},
          "habits": {{"type": "array", "items": {{"type": "string"}}}},
          "strengths": {{"type": "array", "items": {{"type": "string"}}}},
          "weaknesses": {{"type": "array", "items": {{"type": "string"}}}},
          "fears": {{"type": "array", "items": {{"type": "string"}}}},
          "secrets": {{"type": "array", "items": {{"type": "string"}}}}
        }},
        "required": ["name", "role", "background", "personality", "goals", "relationships"]
      }}
    }},
    "conflict_design": {{"type": "string"}},
    "foreshadowing": {{"type": "array", "items": {{"type": "string"}}}},
    "character_arcs": {{"type": "array", "items": {{"type": "string"}}}},
    "tone": {{"type": "string"}},
    "genre_specific": {{"type": "string"}},
    "chapter_count": {{"type": "integer"}}
  }},
  "required": ["world_building", "writing_style", "outline", "chapter_count", "characters", "character_names", "character_cards", "conflict_design", "foreshadowing", "character_arcs", "tone", "genre_specific"]
}}
'''

STRICT RULES:
1. character_names 必须包含所有角色的具体姓名，如 ["林晓", "陈思"]
2. character_cards 必须为每个角色生成详细卡片，包括：
   - name: 角色姓名
   - role: 角色身份（如"程序员"、"作家"等）
   - background: 角色背景故事
   - personality: 详细性格描述
   - goals: 角色目标
   - relationships: 与其他角色的关系
   - speaking_style: 说话风格（如"幽默风趣"、"沉默寡言"等）
   - habits: 习惯动作
   - strengths: 优点
   - weaknesses: 缺点
   - fears: 恐惧
   - secrets: 秘密
3. 后续所有章节必须严格使用 character_names 中的姓名，不能使用"主角1"、"主角2"等代称
4. 只输出JSON，不要输出任何其他内容
5. 不要输出markdown代码块标记
6. 不要输出任何解释、说明或分析
7. 不要输出"让我分析一下"之类的文字
8. 直接输出纯JSON对象
"""
    
    messages = [
        {"role": "system", "content": "你是一个JSON输出机器。你的唯一任务是输出符合Schema的JSON，不要输出任何其他内容。禁止：解释、分析、markdown代码块、任何JSON之外的文字。只输出纯JSON。"},
        {"role": "user", "content": prompt}
    ]
    
    result = llm_client.chat(messages=messages)
    content = result.get("content", "{}")
    
    logger.debug(f"Director general raw content: {content[:500]}")
    
    return content
