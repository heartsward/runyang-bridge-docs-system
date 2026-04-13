# -*- coding: utf-8 -*-
"""
Anthropic提供商适配器
"""
from typing import List, Dict, Any
import httpx
from .base_provider import BaseAIProvider, AIMessage, AIResponse, AIModelInfo
import logging

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseAIProvider):
    """Anthropic提供商适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.api_url = config.get("api_url")
        self.client = httpx.AsyncClient(timeout=config.get("timeout", 30))
        
    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """发送聊天请求"""
        try:
            self._validate_messages(messages)
            
            system_msg = ""
            user_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    user_messages.append({"role": msg.role, "content": msg.content})
            
            response = await self.client.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "messages": user_messages,
                    "system": system_msg,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                return AIResponse(
                    content="",
                    model=self.model,
                    usage={},
                    success=False,
                    error=error_data.get("error", {}).get("message", "请求失败")
                )
            
            data = response.json()
            
            return AIResponse(
                content=data["content"][0]["text"],
                model=self.model,
                usage=data.get("usage", {}),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {e}")
            return AIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=str(e)
            )
    
    def get_available_models(self) -> List[AIModelInfo]:
        """获取可用模型列表"""
        return [
            AIModelInfo("claude-3-opus-20240229", 200000, 0.015, 0.075),
            AIModelInfo("claude-3-sonnet-20240229", 200000, 0.003, 0.015),
            AIModelInfo("claude-3-haiku-20240307", 200000, 0.00025, 0.00125),
        ]
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """估算成本"""
        models = self.get_available_models()
        model_info = next((m for m in models if m.name == self.model), models[0])
        
        input_cost = (prompt_tokens / 1000) * model_info.input_price
        output_cost = (completion_tokens / 1000) * model_info.output_price
        
        return input_cost + output_cost
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
