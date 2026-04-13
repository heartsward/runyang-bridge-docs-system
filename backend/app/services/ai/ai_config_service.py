# -*- coding: utf-8 -*-
"""
AI配置持久化服务
"""
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.ai_config import AIUserConfig
from app.models.user import User


class AIConfigService:
    """AI配置持久化服务"""
    
    @staticmethod
    def get_user_ai_config(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户的AI配置
        优先从数据库读取，如果不存在则返回None
        """
        config = db.query(AIUserConfig).filter(AIUserConfig.user_id == user_id).first()
        
        if not config:
            return None
            
        try:
            # 解析providers_config JSON
            providers_config = json.loads(config.providers_config) if config.providers_config else {}
            
            return {
                "default_provider": config.default_provider,
                "enabled": config.enabled,
                "fallback_enabled": config.fallback_enabled,
                "cost_limit_enabled": config.cost_limit_enabled,
                "daily_cost_limit": config.daily_cost_limit,
                "cache_enabled": config.cache_enabled,
                "cache_ttl": config.cache_ttl,
                "providers": providers_config
            }
        except Exception as e:
            print(f"解析AI配置失败: {e}")
            return None
    
    @staticmethod
    def save_user_ai_config(db: Session, user_id: int, config: Dict[str, Any]) -> AIUserConfig:
        """
        保存用户的AI配置到数据库
        """
        try:
            # 查找现有配置
            existing_config = db.query(AIUserConfig).filter(AIUserConfig.user_id == user_id).first()
            
            # 序列化providers配置
            providers_config_json = json.dumps(config.get("providers", {}), ensure_ascii=False)

            if existing_config:
                # 更新现有配置
                existing_config.default_provider = config.get("default_provider", "openai")
                existing_config.enabled = config.get("enabled", True)
                existing_config.fallback_enabled = config.get("fallback_enabled", True)
                existing_config.cost_limit_enabled = config.get("cost_limit_enabled", False)
                existing_config.daily_cost_limit = config.get("daily_cost_limit", 10.0)
                existing_config.cache_enabled = config.get("cache_enabled", True)
                existing_config.cache_ttl = config.get("cache_ttl", 3600)
                existing_config.providers_config = providers_config_json
                db.commit()
                db.refresh(existing_config)
                return existing_config
            else:
                # 创建新配置
                new_config = AIUserConfig(
                    user_id=user_id,
                    default_provider=config.get("default_provider", "openai"),
                    enabled=config.get("enabled", True),
                    fallback_enabled=config.get("fallback_enabled", True),
                    cost_limit_enabled=config.get("cost_limit_enabled", False),
                    daily_cost_limit=config.get("daily_cost_limit", 10.0),
                    cache_enabled=config.get("cache_enabled", True),
                    cache_ttl=config.get("cache_ttl", 3600),
                    providers_config=providers_config_json
                )
                db.add(new_config)
                db.commit()
                db.refresh(new_config)
                return new_config
                
        except Exception as e:
            print(f"保存AI配置失败: {e}")
            db.rollback()
            raise Exception(f"保存AI配置失败: {str(e)}")
