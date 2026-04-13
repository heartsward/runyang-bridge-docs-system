# -*- coding: utf-8 -*-
"""
AI服务配置管理
支持多个AI提供商的配置
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from enum import Enum

class AIProvider(str, Enum):
    """AI提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ALIBABA = "alibaba"
    ZHIPU = "zhipu"
    MINIMAX = "minimax"
    MOCK = "mock"

class AICacheStrategy(str, Enum):
    """缓存策略"""
    NONE = "none"
    MEMORY = "memory"
    REDIS = "redis"

class AIConfig(BaseSettings):
    """AI服务配置"""
    
    # 默认AI提供商
    DEFAULT_PROVIDER: AIProvider = AIProvider.OPENAI
    
    # OpenAI配置
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API密钥")
    OPENAI_API_URL: str = Field(default="https://api.openai.com/v1/chat/completions")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="默认模型")
    OPENAI_MAX_TOKENS: int = Field(default=2000)
    OPENAI_TEMPERATURE: float = Field(default=0.3)
    
    # Anthropic配置
    ANTHROPIC_API_KEY: str = Field(default="")
    ANTHROPIC_API_URL: str = Field(default="https://api.anthropic.com/v1/messages")
    ANTHROPIC_MODEL: str = Field(default="claude-3-haiku-20240307")
    
    # 阿里云配置
    ALIBABA_API_KEY: str = Field(default="")
    ALIBABA_ENDPOINT: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    ALIBABA_MODEL: str = Field(default="qwen-plus")
    
    # 智谱AI配置
    ZHIPU_API_KEY: str = Field(default="")
    ZHIPU_API_URL: str = Field(default="https://open.bigmodel.cn/api/paas/v4/chat/completions")
    ZHIPU_MODEL: str = Field(default="glm-4-flash")
    
    # MiniMax配置
    MINIMAX_API_KEY: str = Field(default="")
    MINIMAX_API_URL: str = Field(default="https://api.minimax.chat/v1/text/chatcompletion_v2")
    MINIMAX_MODEL: str = Field(default="abab5.5-chat")
    MINIMAX_GROUP_ID: str = Field(default="")
    
    # 通用配置
    MAX_RETRIES: int = Field(default=3, description="最大重试次数")
    TIMEOUT: int = Field(default=30, description="请求超时时间(秒)")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用限流")
    RATE_LIMIT_REQUESTS: int = Field(default=10, description="每分钟最大请求数")
    RATE_LIMIT_PER_USER: int = Field(default=5, description="每用户每分钟最大请求数")
    
    # 缓存配置
    CACHE_STRATEGY: AICacheStrategy = AICacheStrategy.MEMORY
    CACHE_TTL: int = Field(default=3600, description="缓存过期时间(秒)")
    
    # 成本控制
    COST_LIMIT_ENABLED: bool = Field(default=False, description="是否启用成本限制")
    COST_LIMIT_DAILY: float = Field(default=10.0, description="每日成本限制(美元)")
    
    # 降级配置
    FALLBACK_ENABLED: bool = Field(default=True, description="是否启用降级")
    FALLBACK_TO_TRADITIONAL: bool = Field(default=True, description="AI失败时是否降级到传统方法")
    
    class Config:
        env_file = ".env"
        env_prefix = "AI_"
        extra = "allow"  # 允许额外的配置字段

ai_config = AIConfig()
