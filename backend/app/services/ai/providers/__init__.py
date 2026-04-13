# -*- coding: utf-8 -*-
"""
AI提供商适配器
"""
from .base_provider import BaseAIProvider, AIMessage, AIResponse, AIModelInfo
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .alibaba_provider import AlibabaProvider
from .zhipu_provider import ZhipuProvider
from .minimax_provider import MiniMaxProvider

__all__ = [
    'BaseAIProvider',
    'AIMessage',
    'AIResponse',
    'AIModelInfo',
    'OpenAIProvider',
    'AnthropicProvider',
    'AlibabaProvider',
    'ZhipuProvider',
    'MiniMaxProvider'
]
