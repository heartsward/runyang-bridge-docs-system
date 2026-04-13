# -*- coding: utf-8 -*-
"""
限流器 - 控制API请求频率
"""
from typing import Optional, Dict
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self):
        self.user_requests: Dict[int, list] = {}
        self.global_requests: list = []
    
    async def check(self, user_id: Optional[int] = None) -> bool:
        """检查是否可以发起请求"""
        from app.services.ai.ai_config import ai_config
        
        if not ai_config.RATE_LIMIT_ENABLED:
            return True
        
        current_time = time.time()
        window_seconds = 60
        
        # 全局限流检查
        self.global_requests = [t for t in self.global_requests if current_time - t < window_seconds]
        if len(self.global_requests) >= ai_config.RATE_LIMIT_REQUESTS:
            logger.warning(f"全局请求限流: {len(self.global_requests)}/{ai_config.RATE_LIMIT_REQUESTS}")
            return False
        
        # 用户限流检查
        if user_id is not None:
            if user_id not in self.user_requests:
                self.user_requests[user_id] = []
            
            self.user_requests[user_id] = [
                t for t in self.user_requests[user_id] 
                if current_time - t < window_seconds
            ]
            
            if len(self.user_requests[user_id]) >= ai_config.RATE_LIMIT_PER_USER:
                logger.warning(f"用户 {user_id} 请求限流: {len(self.user_requests[user_id])}/{ai_config.RATE_LIMIT_PER_USER}")
                return False
        
        return True
    
    async def record(self, user_id: Optional[int] = None):
        """记录请求"""
        current_time = time.time()
        
        self.global_requests.append(current_time)
        
        if user_id is not None:
            if user_id not in self.user_requests:
                self.user_requests[user_id] = []
            self.user_requests[user_id].append(current_time)
