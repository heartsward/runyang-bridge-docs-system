# -*- coding: utf-8 -*-
"""
AI服务管理器 - 统一的AI服务入口
"""
from typing import List, Dict, Any, Optional
from .ai_config import ai_config, AIProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.alibaba_provider import AlibabaProvider
from .providers.zhipu_provider import ZhipuProvider
from .providers.minimax_provider import MiniMaxProvider
from .providers.base_provider import BaseAIProvider, AIMessage, AIResponse
from .utils.rate_limiter import RateLimiter
from .utils.cache_manager import CacheManager
from .utils.cost_tracker import CostTracker
import hashlib
import logging

logger = logging.getLogger(__name__)

class AIService:
    """AI服务管理器"""
    
    def __init__(self):
        self.providers: Dict[AIProvider, BaseAIProvider] = {}
        self.current_provider: AIProvider = ai_config.DEFAULT_PROVIDER
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager()
        self.cost_tracker = CostTracker()
        
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有提供商"""
        if ai_config.OPENAI_API_KEY:
            self.providers[AIProvider.OPENAI] = OpenAIProvider({
                "api_key": ai_config.OPENAI_API_KEY,
                "api_url": ai_config.OPENAI_API_URL,
                "model": ai_config.OPENAI_MODEL,
                "timeout": ai_config.TIMEOUT
            })
        
        if ai_config.ANTHROPIC_API_KEY:
            self.providers[AIProvider.ANTHROPIC] = AnthropicProvider({
                "api_key": ai_config.ANTHROPIC_API_KEY,
                "api_url": ai_config.ANTHROPIC_API_URL,
                "model": ai_config.ANTHROPIC_MODEL,
                "timeout": ai_config.TIMEOUT
            })
        
        if ai_config.ALIBABA_API_KEY:
            self.providers[AIProvider.ALIBABA] = AlibabaProvider({
                "api_key": ai_config.ALIBABA_API_KEY,
                "api_url": ai_config.ALIBABA_ENDPOINT,
                "model": ai_config.ALIBABA_MODEL,
                "timeout": ai_config.TIMEOUT
            })
        
        if ai_config.ZHIPU_API_KEY:
            self.providers[AIProvider.ZHIPU] = ZhipuProvider({
                "api_key": ai_config.ZHIPU_API_KEY,
                "api_url": ai_config.ZHIPU_API_URL,
                "model": ai_config.ZHIPU_MODEL,
                "timeout": ai_config.TIMEOUT
            })
        
        if ai_config.MINIMAX_API_KEY:
            self.providers[AIProvider.MINIMAX] = MiniMaxProvider({
                "api_key": ai_config.MINIMAX_API_KEY,
                "api_url": ai_config.MINIMAX_API_URL,
                "model": ai_config.MINIMAX_MODEL,
                "group_id": ai_config.MINIMAX_GROUP_ID,
                "timeout": ai_config.TIMEOUT
            })
        
        logger.info(f"已初始化 {len(self.providers)} 个AI提供商")
    
    async def chat(
        self,
        messages: List[AIMessage],
        provider: Optional[AIProvider] = None,
        use_cache: bool = True,
        user_id: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """发送聊天请求 - 统一入口"""
        
        provider = provider or self.current_provider
        if provider not in self.providers:
            return AIResponse(
                content="",
                model="",
                usage={},
                success=False,
                error=f"提供商 {provider} 未配置或不可用"
            )
        
        ai_provider = self.providers[provider]
        
        # 检查限流
        if ai_config.RATE_LIMIT_ENABLED:
            if not await self.rate_limiter.check(user_id):
                return AIResponse(
                    content="",
                    model=ai_provider.model,
                    usage={},
                    success=False,
                    error="请求过于频繁，请稍后再试"
                )
        
        # 检查缓存
        cache_key = self._generate_cache_key(messages, provider)
        if use_cache:
            cached_response = await self.cache_manager.get(cache_key)
            if cached_response:
                logger.info("从缓存返回响应")
                return cached_response
        
        # 发送请求
        response = await ai_provider.chat(messages, **kwargs)
        
        # 缓存成功响应
        if response.success and use_cache:
            await self.cache_manager.set(cache_key, response, ttl=ai_config.CACHE_TTL)
        
        # 追踪成本
        if response.success:
            self.cost_tracker.track(
                provider=provider,
                model=ai_provider.model,
                prompt_tokens=response.usage.get("prompt_tokens", 0),
                completion_tokens=response.usage.get("completion_tokens", 0)
            )
        
        # 记录请求
        await self.rate_limiter.record(user_id)
        
        return response
    
    def _generate_cache_key(self, messages: List[AIMessage], provider: AIProvider) -> str:
        """生成缓存键"""
        content = f"{provider}:{''.join(m.content for m in messages)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def switch_provider(self, provider: AIProvider) -> bool:
        """切换AI提供商"""
        if provider in self.providers:
            self.current_provider = provider
            logger.info(f"已切换到提供商: {provider}")
            return True
        return False
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """获取成本统计"""
        return self.cost_tracker.get_stats()
    
    async def close(self):
        """关闭所有连接"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()

# 全局AI服务实例
ai_service = AIService()
