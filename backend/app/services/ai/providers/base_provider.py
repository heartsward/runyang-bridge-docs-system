# -*- coding: utf-8 -*-
"""
AI提供商基础接口
所有AI提供商都需要实现这个接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class AIMessage:
    """AI消息"""
    role: str
    content: str

@dataclass
class AIResponse:
    """AI响应"""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None

@dataclass
class AIModelInfo:
    """模型信息"""
    name: str
    max_tokens: int
    input_price: float
    output_price: float

class BaseAIProvider(ABC):
    """AI提供商基础接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        
    @abstractmethod
    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[AIModelInfo]:
        """获取可用模型列表"""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """估算成本"""
        pass
    
    def _validate_messages(self, messages: List[AIMessage]) -> None:
        """验证消息格式"""
        if not messages:
            raise ValueError("消息列表不能为空")
        
        for msg in messages:
            if msg.role not in ["system", "user", "assistant"]:
                raise ValueError(f"无效的消息角色: {msg.role}")
            if not msg.content:
                raise ValueError("消息内容不能为空")
