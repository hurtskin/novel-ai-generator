"""
简单记忆存储实现

实现 MemoryStore 接口，提供基于内存的记忆存储功能
支持全局记忆、章节记忆、角色记忆的管理
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import yaml

from interfaces.memory import (
    MemoryStore,
    MemoryUpdate,
    CharacterMemory,
    RetrievalResult,
    RetrievalMetrics,
)

logger = logging.getLogger(__name__)


class SimpleMemoryStore(MemoryStore):
    """
    简单记忆存储实现
    
    功能特性：
    - 基于内存的字典存储
    - 支持全局记忆和章节记忆
    - 支持角色记忆管理
    - 自动持久化到 JSON 文件
    - 记忆检索和截断
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化简单记忆存储
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        
        # 内存存储
        self._global_memory: Dict[str, Any] = {}
        self._chapter_memories: Dict[int, Dict[str, Any]] = {}
        
        # 持久化路径
        self._global_memory_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "global_memory.json"
        )
        
        # 加载已有数据
        self._load_global_memory()

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_global_memory(self) -> None:
        """从文件加载全局记忆"""
        if os.path.exists(self._global_memory_path):
            try:
                with open(self._global_memory_path, "r", encoding="utf-8") as f:
                    self._global_memory = json.load(f)
                logger.info(f"Loaded global memory from {self._global_memory_path}")
            except Exception as e:
                logger.error(f"Failed to load global memory: {e}")
                self._global_memory = {}
        else:
            self._global_memory = {}

    def _save_global_memory(self) -> None:
        """保存全局记忆到文件"""
        try:
            with open(self._global_memory_path, "w", encoding="utf-8") as f:
                json.dump(self._global_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save global memory: {e}")

    def get_character_memory(self, character_name: str) -> Optional[CharacterMemory]:
        """
        获取角色记忆
        
        Args:
            character_name: 角色名称
            
        Returns:
            CharacterMemory: 角色记忆数据，不存在则返回None
        """
        characters = self._global_memory.get("characters", {})
        char_data = characters.get(character_name)
        
        if char_data is None:
            return None
        
        return CharacterMemory(
            character_name=character_name,
            memories=char_data.get("memories", []),
            emotions=char_data.get("emotions", []),
            relationships=char_data.get("relationships", {}),
        )

    def update_memory(self, memory_update: MemoryUpdate) -> None:
        """
        更新记忆
        
        Args:
            memory_update: 记忆更新数据
        """
        target_character = memory_update.target_character
        if not target_character:
            logger.warning("Memory update skipped: no target character")
            return

        # 确保 characters 字典存在
        if "characters" not in self._global_memory:
            self._global_memory["characters"] = {}

        # 确保角色数据存在
        if target_character not in self._global_memory["characters"]:
            self._global_memory["characters"][target_character] = {
                "memories": [],
                "emotions": [],
                "relationships": {},
            }

        char_data = self._global_memory["characters"][target_character]

        # 添加新记忆
        for memory_text in memory_update.new_memories:
            memory_entry = {
                "chapter_id": memory_update.chapter_id,
                "node_id": memory_update.node_id,
                "content": memory_text,
                "timestamp": f"chapter_{memory_update.chapter_id}_node_{memory_update.node_id}",
            }
            char_data["memories"].append(memory_entry)

        # 添加情感变化
        if memory_update.emotion_shift:
            char_data["emotions"].append({
                "chapter_id": memory_update.chapter_id,
                "node_id": memory_update.node_id,
                "shift": memory_update.emotion_shift,
            })

        # 更新关系
        if memory_update.relationship_updates:
            for other_char, updates in memory_update.relationship_updates.items():
                if "relationships" not in char_data:
                    char_data["relationships"] = {}
                if other_char not in char_data["relationships"]:
                    char_data["relationships"][other_char] = {}
                char_data["relationships"][other_char].update(updates)

        # 添加新发现事件
        if memory_update.new_discoveries:
            if "events" not in self._global_memory:
                self._global_memory["events"] = []
            
            for discovery in memory_update.new_discoveries:
                event_entry = {
                    "chapter_id": memory_update.chapter_id,
                    "node_id": memory_update.node_id,
                    "character": target_character,
                    "discovery": discovery,
                }
                self._global_memory["events"].append(event_entry)

        # 持久化
        self._save_global_memory()
        logger.info(f"Updated memory for character: {target_character}")

    def get_global_memory(self) -> Dict[str, Any]:
        """获取全局记忆"""
        return self._global_memory

    def save_global_memory(self, memory: Dict[str, Any]) -> None:
        """保存全局记忆"""
        self._global_memory = memory
        self._save_global_memory()

    def get_chapter_memory(self, chapter_id: int) -> Dict[str, Any]:
        """获取章节记忆"""
        return self._chapter_memories.get(chapter_id, {})

    def save_chapter_memory(self, chapter_id: int, memory: Dict[str, Any]) -> None:
        """保存章节记忆"""
        self._chapter_memories[chapter_id] = memory

    def clear_character_memory(self, character_name: str) -> None:
        """清空角色记忆"""
        if "characters" in self._global_memory:
            if character_name in self._global_memory["characters"]:
                del self._global_memory["characters"][character_name]
                self._save_global_memory()
                logger.info(f"Cleared memory for character: {character_name}")

    def clear(self) -> None:
        """清空所有记忆数据"""
        self._global_memory = {}
        self._chapter_memories = {}
        self._save_global_memory()
        logger.info("All memories cleared")

    def add_memory(self, content: str, metadata: Dict[str, Any]) -> None:
        """添加记忆（兼容 RAG 接口）"""
        # 使用 MemoryUpdate 对象而不是字典
        from interfaces.memory import MemoryUpdate
        self.update_memory(MemoryUpdate(
            chapter_id=metadata.get("chapter_id", 0),
            node_id=metadata.get("node_id", "unknown"),
            target_character=metadata.get("target_character", "global"),
            new_memories=[content],
        ))
        logger.debug(f"Added memory: {content[:50]}...")

    def get_all_characters(self) -> List[str]:
        """获取所有角色名称列表"""
        characters = self._global_memory.get("characters", {})
        return list(characters.keys())

    def truncate_memories(
        self,
        memories: List[Dict[str, Any]],
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """
        截断记忆列表到指定字符数
        
        Args:
            memories: 记忆列表
            max_chars: 最大字符数
            
        Returns:
            List[Dict[str, Any]]: 截断后的记忆列表
        """
        if max_chars <= 0:
            return []

        result = []
        total_chars = 0

        for card in memories:
            card_str = json.dumps(card, ensure_ascii=False)
            card_chars = len(card_str)

            if total_chars + card_chars <= max_chars:
                result.append(card)
                total_chars += card_chars
            else:
                remaining = max_chars - total_chars
                if remaining > 100:
                    partial_card = {
                        **card,
                        "core_action": card.get("core_action", "")[:remaining - 50] + "...",
                        "key_quote": "",
                        "future_impacts": []
                    }
                    result.append(partial_card)
                break

        return result

    def deduplicate_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        去重记忆列表
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的记忆列表
        """
        seen_ids = set()
        result = []
        for card in memories:
            event_id = card.get("event_id", "")
            if event_id not in seen_ids:
                seen_ids.add(event_id)
                result.append(card)
        return result

    def retrieve(
        self,
        character: str,
        current_scene: Dict[str, Any],
        global_memory: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        metrics: Optional[RetrievalMetrics] = None
    ) -> RetrievalResult:
        """
        检索角色相关记忆
        
        Args:
            character: 角色名称
            current_scene: 当前场景信息
            global_memory: 全局记忆存储（可选，使用内部存储）
            config: 配置参数（可选，使用内部配置）
            metrics: 性能指标收集器（可选）
            
        Returns:
            RetrievalResult: 检索结果
        """
        start_time = time.perf_counter()
        
        # 使用传入的参数或默认值
        memory_config = config.get("memory", {}) if config else self._config.get("memory", {})
        recent_chapters = memory_config.get("recent_chapters", 3)
        truncation_limit = memory_config.get("truncation", 2000)
        
        mem_data = global_memory if global_memory else self._global_memory
        recent_detailed = mem_data.get("recent_detailed", [])
        recent = recent_detailed[-recent_chapters:] if recent_detailed else []
        
        scene_description = current_scene.get("description", "")
        scene_other_chars = current_scene.get("other_characters", [])
        
        scene_keywords = self.extract_keywords(scene_description)
        
        # 关键词匹配
        matched = []
        for memory in recent:
            emotion_marks = memory.get("emotion_marks", {})
            emotion_str = str(emotion_marks)
            if any(keyword in emotion_str for keyword in scene_keywords):
                matched.append(memory)
        
        # 关系匹配
        related = []
        for memory in recent:
            relationship_changes = memory.get("relationship_changes", {})
            rel_str = str(relationship_changes)
            for char in scene_other_chars:
                if char in rel_str:
                    related.append(memory)
                    break
        
        # 合并并去重
        combined = self.deduplicate_memories(recent + matched + related)
        
        # 截断
        truncated = self.truncate_memories(combined, truncation_limit)
        
        end_time = time.perf_counter()
        retrieval_time_ms = (end_time - start_time) * 1000
        
        total_chars = sum(len(json.dumps(c, ensure_ascii=False)) for c in truncated)
        
        # 更新指标
        if metrics is not None:
            metrics.retrieval_time_ms = retrieval_time_ms
            metrics.cards_retrieved = len(truncated)
            metrics.chars_returned = total_chars
        
        return RetrievalResult(
            character=character,
            current_scene=current_scene,
            retrieved_memories=truncated,
            memory_count=len(truncated),
            total_chars=total_chars,
            retrieval_time_ms=retrieval_time_ms,
            config_used={
                "recent_chapters": recent_chapters,
                "truncation_limit": truncation_limit
            },
            content="",  # 简单实现不返回组装后的内容
        )

    def extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        if not text:
            return []

        # 移除非字母数字和中文字符
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        words = text.split()

        keywords = []
        for word in words:
            if len(word) >= 2:
                keywords.append(word)

        return keywords[:20]

    def validate_token_overflow(self, context: Dict[str, Any], max_tokens: int = 8000) -> bool:
        """
        验证是否超出token限制
        
        Args:
            context: 上下文数据
            max_tokens: 最大token数
            
        Returns:
            bool: 是否超出限制
        """
        total_chars = context.get("total_chars", 0)
        estimated_tokens = total_chars // 4

        return estimated_tokens > max_tokens
