"""
缓存系统
"""
import json
import time
import hashlib
from typing import Any, Optional, Dict, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleMemoryCache:
    """简单内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """检查缓存项是否过期"""
        return time.time() > item["expires_at"]
    
    def _cleanup_expired(self):
        """清理过期缓存项"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items() 
            if current_time > item["expires_at"]
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if self._is_expired(item):
            del self.cache[key]
            return None
        
        # 更新访问次数和时间
        item["access_count"] += 1
        item["last_access"] = time.time()
        
        return item["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
            "last_access": time.time(),
            "access_count": 0
        }
        
        # 定期清理过期项
        if len(self.cache) % 100 == 0:
            self._cleanup_expired()
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        self._cleanup_expired()
        total_access = sum(item["access_count"] for item in self.cache.values())
        
        return {
            "total_items": len(self.cache),
            "total_accesses": total_access,
            "memory_usage_estimate": len(str(self.cache)),
            "oldest_item": min(
                (item["created_at"] for item in self.cache.values()),
                default=time.time()
            )
        }

# 全局缓存实例
cache = SimpleMemoryCache()

def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator

def cache_documents_list(ttl: int = 60):
    """文档列表缓存装饰器"""
    return cached(ttl=ttl, key_prefix="docs")

def cache_user_info(ttl: int = 300):
    """用户信息缓存装饰器"""
    return cached(ttl=ttl, key_prefix="user")

def cache_search_results(ttl: int = 120):
    """搜索结果缓存装饰器"""
    return cached(ttl=ttl, key_prefix="search")

def invalidate_user_cache(user_id: int):
    """使用户相关缓存失效"""
    # 简单实现：清除所有用户相关缓存
    keys_to_delete = [key for key in cache.cache.keys() if f"user_{user_id}" in key]
    for key in keys_to_delete:
        cache.delete(key)

def invalidate_document_cache(document_id: int):
    """使文档相关缓存失效"""
    keys_to_delete = [key for key in cache.cache.keys() if f"doc_{document_id}" in key or "docs:" in key]
    for key in keys_to_delete:
        cache.delete(key)

class CacheWarmer:
    """缓存预热器"""
    
    @staticmethod
    def warm_popular_content():
        """预热热门内容"""
        try:
            from app.db.database_optimized import db_manager
            from sqlalchemy import text
            
            with db_manager.get_db_session() as session:
                # 预热热门文档
                popular_docs = session.execute(text("""
                    SELECT id FROM documents 
                    ORDER BY view_count DESC 
                    LIMIT 10
                """)).fetchall()
                
                logger.info(f"预热了 {len(popular_docs)} 个热门文档的缓存")
                
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")

# 性能监控装饰器
def monitor_performance(func_name: str = ""):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录性能指标
                if execution_time > 1.0:  # 慢函数阈值
                    logger.warning(f"慢函数检测: {func_name or func.__name__} - {execution_time:.2f}秒")
                else:
                    logger.debug(f"函数执行: {func_name or func.__name__} - {execution_time:.3f}秒")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"函数执行错误: {func_name or func.__name__} - {execution_time:.3f}秒 - {e}")
                raise
        
        return wrapper
    return decorator