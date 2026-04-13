# -*- coding: utf-8 -*-
"""
MiniMax提供商适配器
"""
from typing import List, Dict, Any
import httpx
from .base_provider import BaseAIProvider, AIMessage, AIResponse, AIModelInfo
import logging

logger = logging.getLogger(__name__)

class MiniMaxProvider(BaseAIProvider):
    """MiniMax提供商适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.group_id = config.get("group_id", "")
        
        # 检查用户提供的URL
        provided_url = config.get("api_url", "")
        
        # 根据URL类型确定端点
        if "/anthropic" in provided_url:
            # Anthropic兼容端点
            if "/v1/messages" in provided_url or "/messages" in provided_url:
                self.api_url = provided_url
            else:
                self.api_url = f"{provided_url}/v1/messages"
            self.use_anthropic_format = True
        elif "/chat/completions" in provided_url or "/v1/text/" in provided_url:
            # OpenAI兼容端点
            self.api_url = provided_url
            self.use_anthropic_format = False
        else:
            # 默认使用Anthropic兼容端点(Token Plan推荐)
            base_url = provided_url if provided_url else "https://api.minimaxi.com/anthropic"
            self.api_url = f"{base_url}/v1/messages"
            self.use_anthropic_format = True
        
        self.client = httpx.AsyncClient(timeout=config.get("timeout", 30))
        
    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """发送聊天请求 - 支持OpenAI和Anthropic两种格式"""
        try:
            self._validate_messages(messages)

            # 根据端点类型选择请求格式
            if getattr(self, 'use_anthropic_format', False):
                # Anthropic格式
                request_data = {
                    "model": self.model,
                    "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                headers = {
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            else:
                # OpenAI格式
                request_data = {
                    "model": self.model,
                    "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if self.group_id:
                    request_data["group_id"] = self.group_id
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

            response = await self.client.post(
                self.api_url,
                headers=headers,
                json=request_data
            )

            if response.status_code != 200:
                try:
                    error_data = response.json()

                    # 检查MiniMax特有的错误格式
                    if error_data.get("base_resp"):
                        base_resp = error_data["base_resp"]
                        status_code = base_resp.get('status_code', '')
                        status_msg = base_resp.get('status_msg', '未知错误')

                        error_messages = {
                            2013: f"模型 {self.model} 不存在。正确模型名称为: MiniMax-M2.7 或 MiniMax-M2.7-highspeed",
                            2061: f"您的MiniMax计划不支持模型 {self.model}",
                        }

                        error_message = error_messages.get(status_code, status_msg)

                        return AIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=error_message
                        )
                    else:
                        return AIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=error_data.get("error", {}).get("message", "请求失败")
                        )
                except Exception as parse_error:
                    logger.error(f"解析MiniMax错误响应失败: {parse_error}")
                    return AIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"HTTP {response.status_code} - 请求失败"
                    )

            data = response.json()

            # 检查响应中是否有错误
            if data.get("base_resp"):
                base_resp = data["base_resp"]
                status_code = base_resp.get('status_code')
                status_msg = base_resp.get('status_msg', '未知错误')

                error_messages = {
                    2013: f"模型 {self.model} 不存在。正确模型名称为: MiniMax-M2.7 或 MiniMax-M2.7-highspeed",
                    2061: f"您的MiniMax计划不支持模型 {self.model}",
                }

                error_message = error_messages.get(status_code, status_msg)

                return AIResponse(
                    content="",
                    model=self.model,
                    usage={},
                    success=False,
                    error=error_message
                )

            # 获取响应文本 - MiniMax使用OpenAI兼容格式
            content = ""
            if data.get("choices") and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                # 优先使用content字段（OpenAI标准），如果不存在则使用text字段（兼容性）
                content = message.get("content", message.get("text", ""))

            return AIResponse(
                content=content,
                model=self.model,
                usage=data.get("usage", {}),
                success=True
            )

        except Exception as e:
            logger.error(f"MiniMax API调用失败: {e}")
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
            AIModelInfo("MiniMax-M2.7", 204800, 0.00002, 0.00002),
            AIModelInfo("MiniMax-M2.7-highspeed", 204800, 0.00003, 0.00003),
            AIModelInfo("MiniMax-M2.5", 204800, 0.000015, 0.000015),
            AIModelInfo("MiniMax-M2.1", 204800, 0.00001, 0.00001),
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
