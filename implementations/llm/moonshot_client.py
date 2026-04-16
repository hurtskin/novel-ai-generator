"""
Moonshot LLM 客户端实现

实现 LLMClient 接口，提供与 Moonshot API 的交互能力
支持流式输出、自动重试、指数退避、性能指标收集
"""

import json
import logging
import os
import re
import time
from typing import Any, List, Optional

import requests
import yaml

from interfaces.llm_client import (
    LLMClient,
    ChatMessage,
    ChatResponse,
    TokenUsage,
    PerformanceMetrics,
    StreamCallback,
    LLMRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)


class MoonshotClient(LLMClient):
    """
    Moonshot API 客户端实现
    
    功能特性：
    - 支持流式输出和回调
    - 自动重试机制（429/500错误）
    - 指数退避策略
    - 性能指标自动收集
    - Context Caching 支持
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化 Moonshot 客户端
        
        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        self._config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "config.yaml"
        )
        self._config = self._load_config()
        self._api_key = self._resolve_api_key(self._config["api"]["api_key"])
        self.base_url = self._config["api"]["base_url"]
        self.model = self._config["api"]["model"]
        self.timeout = self._config["api"]["timeout"]
        self.max_retries = self._config["api"].get("max_retries", 5)
        self.pricing = self._config["pricing"].get(
            self.model, {"input_per_million": 12, "output_per_million": 60}
        )

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _resolve_api_key(self, key: str) -> str:
        """解析 API Key（支持环境变量）"""
        if key.startswith("${") and key.endswith("}"):
            env_var = key[2:-1]
            return os.environ.get(env_var, "")
        return key

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()
        self._api_key = self._resolve_api_key(self._config["api"]["api_key"])
        self.base_url = self._config["api"]["base_url"]
        self.model = self._config["api"]["model"]
        self.timeout = self._config["api"]["timeout"]
        self.max_retries = self._config["api"].get("max_retries", 5)
        self.pricing = self._config["pricing"].get(
            self.model, {"input_per_million": 12, "output_per_million": 60}
        )

    def get_model(self) -> str:
        """获取当前使用的模型名称"""
        return self.model

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量
        
        使用简单启发式：每4个字符约1个token
        """
        if isinstance(text, list):
            text = json.dumps(text)
        return len(text) // 4

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0
    ) -> float:
        """
        计算 API 调用成本（USD）
        
        Args:
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            cached_tokens: 缓存 token 数
            
        Returns:
            float: 成本（美元）
        """
        input_price = self.pricing.get("input_per_million", 12) / 1_000_000
        output_price = self.pricing.get("output_per_million", 60) / 1_000_000
        cache_discount = self.pricing.get("cache_discount", 0.1)

        non_cached_tokens = prompt_tokens - cached_tokens
        cached_cost = cached_tokens * input_price * cache_discount
        non_cached_cost = non_cached_tokens * input_price
        output_cost = completion_tokens * output_price

        return cached_cost + non_cached_cost + output_cost

    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[StreamCallback] = None,
        cache_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        发送聊天请求到 Moonshot API
        
        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            stream_callback: 流式输出回调函数
            cache_id: 缓存 ID
            
        Returns:
            ChatResponse: 包含生成内容、使用统计和性能指标
            
        Raises:
            LLMRequestError: 请求失败
            LLMRateLimitError: 触发速率限制
            LLMTimeoutError: 请求超时
        """
        model = model or self.model
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        logger.warning(
            f"[LLM_API] Calling API: model={model}, endpoint={endpoint}, messages_count={len(messages)}"
        )

        generation_config = self._config.get("generation", {})
        body = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
            "temperature": temperature
            if temperature is not None
            else generation_config.get("temperature", 1),
            "top_p": top_p if top_p is not None else generation_config.get("top_p", 0.95),
            "max_tokens": max_tokens
            if max_tokens is not None
            else generation_config.get("max_tokens", 4096),
            "response_format": {"type": "json_object"},
        }

        if cache_id:
            body["cache"] = {"mode": "reuse", "id": cache_id}

        self._log_request(model, endpoint, messages, body)

        start_time = time.time()
        first_token_time = None
        tokens = []
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=body,
                    stream=True,
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        wait_time = 30 * retry_count
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {retry_count}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMRateLimitError(
                            f"API rate limit exceeded after {self.max_retries} retries",
                            retry_after=wait_time if 'wait_time' in locals() else None
                        )

                if response.status_code >= 500:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        wait_time = 2 ** (retry_count - 1)
                        logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry {retry_count}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMRequestError(
                            f"API error after {self.max_retries} retries: {response.status_code}",
                            status_code=response.status_code
                        )

                if response.status_code != 200:
                    raise LLMRequestError(
                        f"API request failed with status {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if not content:
                                    content = delta.get("reasoning_content", "")
                                if content:
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                    tokens.append(content)
                                    if stream_callback:
                                        stream_callback(content)
                            except json.JSONDecodeError:
                                continue

                break

            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = 2 ** (retry_count - 1)
                    logger.warning(f"Timeout, waiting {wait_time}s before retry {retry_count}")
                    time.sleep(wait_time)
                else:
                    raise LLMTimeoutError(f"Request timeout after {self.max_retries} retries")
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = 2 ** (retry_count - 1)
                    logger.warning(f"Request error: {e}, waiting {wait_time}s before retry {retry_count}")
                    time.sleep(wait_time)
                else:
                    raise LLMRequestError(f"Request failed after {self.max_retries} retries: {str(e)}")

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000

        full_content = "".join(tokens)
        logger.warning(
            f"[LLM_API] response content length = {len(full_content)}, content = {full_content[:500]}"
        )

        self._log_response(full_content)

        prompt_tokens = self.estimate_tokens(
            json.dumps([{"role": msg.role, "content": msg.content} for msg in messages])
        )
        completion_tokens = self.estimate_tokens(full_content)
        total_tokens = prompt_tokens + completion_tokens

        ttf_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
        tps = (completion_tokens / (total_duration_ms / 1000)) if total_duration_ms > 0 else 0

        cache_hit = cache_id is not None
        cached_tokens = prompt_tokens if cache_hit else 0
        cost_usd = self.calculate_cost(prompt_tokens, completion_tokens, cached_tokens)

        return ChatResponse(
            content=full_content,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cached_tokens=cached_tokens,
            ),
            performance=PerformanceMetrics(
                ttf_ms=round(ttf_ms, 2),
                tps=round(tps, 2),
                duration_ms=round(total_duration_ms, 2),
                api_latency_ms=round(total_duration_ms, 2),
                retry_count=retry_count,
            ),
            model=model,
        )

    def chat_with_completion_check(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[StreamCallback] = None,
        check_interval: int = 100,
    ) -> ChatResponse:
        """
        流式调用并检查 JSON 完整性，如果完整则提前返回
        
        Args:
            messages: 聊天消息列表
            model: 模型名称
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            stream_callback: 流式输出回调函数
            check_interval: 检查间隔（字符数）
            
        Returns:
            ChatResponse: 包含生成内容和性能指标
        """
        model = model or self.model
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        generation_config = self._config.get("generation", {})
        body = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
            "temperature": temperature
            if temperature is not None
            else generation_config.get("temperature", 1),
            "top_p": top_p if top_p is not None else generation_config.get("top_p", 0.95),
            "max_tokens": max_tokens
            if max_tokens is not None
            else generation_config.get("max_tokens", 4096),
            "response_format": {"type": "json_object"},
        }

        start_time = time.time()
        first_token_time = None
        tokens = []
        received_content = ""

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=body,
                stream=True,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise LLMRequestError(
                    f"API request failed with status {response.status_code}: {response.text}",
                    status_code=response.status_code
                )

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if not content:
                                content = delta.get("reasoning_content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                tokens.append(content)
                                if stream_callback:
                                    stream_callback(content)

                                received_content += content
                                if len(received_content) >= check_interval:
                                    if self._check_json_complete(received_content):
                                        logger.warning(
                                            f"[LLM_API] JSON complete, returning early at {len(received_content)} chars"
                                        )
                                        break
                                    received_content = ""
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            raise LLMTimeoutError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise LLMRequestError(f"Request failed: {str(e)}")

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000

        full_content = "".join(tokens)
        logger.warning(
            f"[LLM_API] response content length = {len(full_content)}, content = {full_content[:500]}"
        )

        if not self._check_json_complete(full_content):
            logger.warning(
                f"[LLM_API] WARNING: Response truncated or incomplete JSON, length={len(full_content)}"
            )

        prompt_tokens = self.estimate_tokens(
            json.dumps([{"role": msg.role, "content": msg.content} for msg in messages])
        )
        completion_tokens = self.estimate_tokens(full_content)
        total_tokens = prompt_tokens + completion_tokens

        ttf_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
        tps = (completion_tokens / (total_duration_ms / 1000)) if total_duration_ms > 0 else 0

        cost_usd = self.calculate_cost(prompt_tokens, completion_tokens, 0)

        return ChatResponse(
            content=full_content,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            performance=PerformanceMetrics(
                ttf_ms=round(ttf_ms, 2),
                tps=round(tps, 2),
                duration_ms=round(total_duration_ms, 2),
                api_latency_ms=round(total_duration_ms, 2),
                retry_count=0,
            ),
            model=model,
        )

    def _log_request(
        self, model: str, endpoint: str, messages: List[ChatMessage], body: dict
    ) -> None:
        """记录请求日志"""
        debug_log_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "logs", "debug.log"
        )
        os.makedirs(os.path.dirname(debug_log_path), exist_ok=True)
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[LLM_API] REQUEST: model={model}, endpoint={endpoint}\n")
            f.write(
                f"[LLM_API] messages={json.dumps([{'role': msg.role, 'content': msg.content} for msg in messages], ensure_ascii=False, indent=2)}\n"
            )
            f.write(f"[LLM_API] body={json.dumps(body, ensure_ascii=False, indent=2)}\n")

    def _log_response(self, content: str) -> None:
        """记录响应日志"""
        debug_log_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "logs", "debug.log"
        )
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"[LLM_API] RESPONSE: length={len(content)}, content={content[:1000]}\n")

    def _check_json_complete(self, content: str) -> bool:
        """检查内容是否包含完整且有效的 JSON"""
        cleaned = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = re.sub(r"&#\d+;", "", cleaned)
        cleaned = re.sub(r"&\w+;", "", cleaned)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        try:
            if cleaned.startswith("{") and "}" in cleaned:
                json_str = self._find_json_object(cleaned, 0)
                if json_str:
                    json_str_fixed = re.sub(r",(\s*})", r"\1", json_str)
                    json_str_fixed = re.sub(r",(\s*])", r"\1", json_str_fixed)
                    parsed = json.loads(json_str_fixed)
                    content_field = parsed.get("content", "")
                    if content_field and content_field.strip():
                        return True
        except Exception:
            pass
        return False

    def _find_json_object(self, text: str, start_pos: int = 0) -> str:
        """使用括号匹配找到从 start_pos 开始的完整 JSON 对象"""
        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(start_pos, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\" and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_pos : i + 1]

        return ""
