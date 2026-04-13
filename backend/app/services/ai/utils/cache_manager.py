# -*- coding: utf-8 -*-
"""
缓存管理器 - 支持内存和Redis缓存
"""
from typing import Optional, Dict
import logging
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.memory_cache: Dict[str, tuple] = {}
    
    async def get(self, key: str):
        """获取缓存"""
        from app.services.ai.ai_config import ai_config
        
        if ai_config.CACHE_STRATEGY == "none":
            return None
        
        if ai_config.CACHE_STRATEGY == "memory":
            cached_data = self.memory_cache.get(key)
            if cached_data:
                value, timestamp = cached_data
                import time
                if time.time() - timestamp < ai_config.CACHE_TTL:
                    logger.info(f"缓存命中: {key[:20]}...")
                    return value
                else:
                    del self.memory_cache[key]
            return None
        
        return None
    
    async def set(self, key: str, value, ttl: Optional[int] = None):
        """设置缓存"""
        from app.services.ai.ai_config import ai_config
        
        if ai_config.CACHE_STRATEGY == "none":
            return
        
        if ai_config.CACHE_STRATEGY == "memory":
            import time
            cache_ttl = ttl or ai_config.CACHE_TTL
            self.memory_cache[key] = (value, time.time())
            logger.info(f"缓存设置: {key[:20]}...")
    
    async def delete(self, key: str):
        """删除缓存"""
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    async def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        logger.info("缓存已清空")
