# -*- coding: utf-8 -*-
"""
OpenAI提供商适配器
"""
from typing import List, Dict, Any
import httpx
from .base_provider import BaseAIProvider, AIMessage, AIResponse, AIModelInfo
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI提供商适配器"""
    
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
            
            api_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await self.client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
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
            choice = data["choices"][0]
            
            return AIResponse(
                content=choice["message"]["content"],
                model=data["model"],
                usage=data.get("usage", {}),
                success=True
            )
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
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
            AIModelInfo("gpt-4o", 128000, 0.005, 0.015),
            AIModelInfo("gpt-4o-mini", 128000, 0.00015, 0.0006),
            AIModelInfo("gpt-4-turbo", 128000, 0.01, 0.03),
            AIModelInfo("gpt-3.5-turbo", 16385, 0.0005, 0.0015),
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
