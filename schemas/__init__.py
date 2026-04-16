"""
数据模型模块

提供 Pydantic 数据模型，用于数据验证、序列化和文档生成。

模块结构：
- common: 通用数据结构和基础模型
- inputs: 输入数据模型（API 请求参数、用户输入验证）
- outputs: 输出数据模型（API 响应、数据返回格式）
- memory: 记忆相关数据模型

使用示例：
    from schemas import DirectorGeneralInput, DirectorGeneralOutput
    from schemas import RoleAssignerInput, RoleAssignerOutput
    from schemas import MemoryCard, RawMemory
    
    # 创建输入数据
    input_data = DirectorGeneralInput(
        theme="科幻冒险",
        style="悬疑",
        total_words=50000,
        character_count=5,
        genre="novel"
    )
    
    # 验证输出数据
    output = DirectorGeneralOutput(**json_data)
"""

# 从 common 模块导入
from schemas.common import (
    CacheConfig,
    CacheManifest,
    CachedContent,
    WorldBuilding,
    WritingStyle,
    ChapterOutline,
    CharacterProfile,
    ConflictDesign,
    HookDesign,
    ArcDesign,
    GenreSpecific,
    CharacterCard,
    ChapterOutlineRef,
    NodeConfig,
    CharacterPresencePlan,
    CurrentNodeInfo,
    CharacterProfileData,
    PerformanceMetrics,
    LlmRequestConfig,
    LlmResponseMetadata,
)

# 从 inputs 模块导入
from schemas.inputs import (
    DirectorGeneralInput,
    DirectorChapterInput,
    ChapterOutlineInput,
    RoleAssignerInput,
    TextPolisherInput,
)

# 从 outputs 模块导入
from schemas.outputs import (
    DirectorGeneralOutput,
    DirectorChapterOutput,
    PromptComponents,
    RoleAssignerOutput,
    StateChangeReport,
    RoleActorOutput,
    SelfCheckOutput,
    TextPolisherOutput,
)

# 从 memory 模块导入
from schemas.memory import (
    MemoryCard,
    RawMemory,
)

__all__ = [
    # common
    "CacheConfig",
    "CacheManifest",
    "CachedContent",
    "WorldBuilding",
    "WritingStyle",
    "ChapterOutline",
    "CharacterProfile",
    "ConflictDesign",
    "HookDesign",
    "ArcDesign",
    "GenreSpecific",
    "CharacterCard",
    "ChapterOutlineRef",
    "NodeConfig",
    "CharacterPresencePlan",
    "CurrentNodeInfo",
    "CharacterProfileData",
    "PerformanceMetrics",
    "LlmRequestConfig",
    "LlmResponseMetadata",
    # inputs
    "DirectorGeneralInput",
    "DirectorChapterInput",
    "ChapterOutlineInput",
    "RoleAssignerInput",
    "TextPolisherInput",
    # outputs
    "DirectorGeneralOutput",
    "DirectorChapterOutput",
    "PromptComponents",
    "RoleAssignerOutput",
    "StateChangeReport",
    "RoleActorOutput",
    "SelfCheckOutput",
    "TextPolisherOutput",
    # memory
    "MemoryCard",
    "RawMemory",
]
