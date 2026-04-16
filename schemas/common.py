"""
通用数据结构和基础模型

包含在多个模块间共享的基础模型、枚举类型、常量定义等
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = Field(default=False, description="是否启用 Context Caching")
    cache_type: str = Field(default="file", description="缓存类型，目前支持 'file'")
    cache_id: Optional[str] = Field(default=None, description="已创建的缓存 ID，用于复用")
    cache_content: Optional[str] = Field(default=None, description="缓存内容，用于创建新缓存")
    expires_ttl: Optional[int] = Field(default=300, description="缓存有效期(秒)，默认5分钟")


class CacheManifest(BaseModel):
    """缓存清单"""
    cache_id: str = Field(description="缓存 ID")
    cache_key: str = Field(description="缓存键名，用于标识缓存内容")
    cached_tokens: int = Field(default=0, description="缓存的 token 数量")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    expires_at: Optional[str] = Field(default=None, description="过期时间")


class CachedContent(BaseModel):
    """缓存内容"""
    system_prompt: str = Field(description="系统提示词（静态，可缓存）")
    static_context: Optional[str] = Field(default=None, description="静态上下文（如世界观、角色设定等）")
    cache_manifest: Optional[CacheManifest] = Field(default=None, description="缓存清单")


class WorldBuilding(BaseModel):
    """世界观设定"""
    setting: str
    time_period: str
    location: str
    social_structure: str
    rules: Dict[str, Any]


class WritingStyle(BaseModel):
    """写作风格"""
    tone: str
    perspective: str
    pacing: str
    language_level: str


class ChapterOutline(BaseModel):
    """章节大纲"""
    chapter_id: int
    title: str
    summary: str
    key_events: List[str]
    characters_involved: List[str]


class CharacterProfile(BaseModel):
    """角色档案"""
    name: str
    role: str
    background: str
    personality: str
    goals: str
    relationships: Dict[str, str]


class ConflictDesign(BaseModel):
    """冲突设计"""
    main_conflict: str
    sub_conflicts: List[str]
    stakes: str


class HookDesign(BaseModel):
    """钩子设计"""
    hook_type: str
    content: str
    placement: str


class ArcDesign(BaseModel):
    """角色弧光设计"""
    character_name: str
    starting_state: str
    turning_point: str
    ending_state: str


class GenreSpecific(BaseModel):
    """文体特定字段"""
    genre: str
    specific_fields: Dict[str, Any] = Field(default_factory=dict)


class CharacterCard(BaseModel):
    """角色卡片"""
    name: str
    role: str
    background: str
    personality: str
    goals: str
    relationships: Dict[str, str]
    speaking_style: str = ""
    habits: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    fears: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)


class ChapterOutlineRef(BaseModel):
    """章节大纲引用"""
    chapter_id: int
    title: str
    summary: str
    key_events: List[str]
    characters_involved: List[str]


class NodeConfig(BaseModel):
    """节点配置"""
    node_id: int
    type: str
    character: Optional[str] = None
    description: str


class CharacterPresencePlan(BaseModel):
    """角色出场计划"""
    character: str
    node_indices: List[int]


class CurrentNodeInfo(BaseModel):
    """当前节点信息"""
    node_id: int
    type: str
    description: str
    target_character: Optional[str] = None


class CharacterProfileData(BaseModel):
    """角色档案数据"""
    name: str
    role: str
    background: str
    personality: str
    goals: str
    relationships: Dict[str, str]


class PerformanceMetrics(BaseModel):
    """性能指标"""
    ttf_ms: float
    tps: float
    api_latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class LlmRequestConfig(BaseModel):
    """LLM 请求配置"""
    model: str = Field(default="kimi-k2.5", description="模型名称")
    temperature: Optional[float] = Field(default=1.0, description="温度参数")
    top_p: Optional[float] = Field(default=0.95, description="Top P 参数")
    max_tokens: Optional[int] = Field(default=4096, description="最大生成 token 数")
    enable_cache: bool = Field(default=False, description="是否启用 Context Caching")
    cache_id: Optional[str] = Field(default=None, description="已存在的缓存 ID")
    cache_ttl: int = Field(default=300, description="缓存 TTL（秒）")


class LlmResponseMetadata(BaseModel):
    """LLM 响应元数据"""
    cache_hit: Optional[bool] = Field(default=None, description="是否命中缓存")
    cache_id: Optional[str] = Field(default=None, description="缓存 ID")
    input_tokens: int = Field(default=0, description="输入 token 数")
    output_tokens: int = Field(default=0, description="输出 token 数")
    cached_tokens: Optional[int] = Field(default=None, description="缓存的 token 数（缓存命中时）")
    cost_usd: Optional[float] = Field(default=None, description="本次请求费用（USD）")
    latency_ms: Optional[float] = Field(default=None, description="请求延迟（毫秒）")
    ttf_ms: Optional[float] = Field(default=None, description="首个 token 生成时间（毫秒）")
    tps: Optional[float] = Field(default=None, description="Token 生成速度")
