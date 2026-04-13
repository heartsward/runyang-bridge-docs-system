# -*- coding: utf-8 -*-
"""
成本追踪器 - 记录和追踪AI使用成本
"""
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CostTracker:
    """成本追踪器"""
    
    def __init__(self):
        self.costs: Dict[str, List[dict]] = {}
        self.daily_costs: Dict[str, float] = {}
    
    def track(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int):
        """记录成本"""
        from app.services.ai.ai_config import ai_config
        from app.services.ai.ai_service import ai_service
        
        if provider not in self.costs:
            self.costs[provider] = []
        
        provider_instance = ai_service.providers.get(provider)
        if not provider_instance:
            return
        
        cost = provider_instance.estimate_cost(prompt_tokens, completion_tokens)
        
        cost_record = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": cost
        }
        
        self.costs[provider].append(cost_record)
        
        # 更新每日成本
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0
        self.daily_costs[today] += cost
        
        logger.info(f"成本记录: {provider}/{model}, token={prompt_tokens+completion_tokens}, cost=${cost:.4f}")
        
        # 检查是否超过限制
        if ai_config.COST_LIMIT_ENABLED:
            if self.daily_costs[today] > ai_config.COST_LIMIT_DAILY:
                logger.warning(f"已超过每日成本限制: ${self.daily_costs[today]:.2f} > ${ai_config.COST_LIMIT_DAILY:.2f}")
    
    def get_stats(self) -> Dict:
        """获取成本统计"""
        total_cost = 0.0
        total_tokens = 0
        request_count = 0
        
        for provider_costs in self.costs.values():
            for record in provider_costs:
                total_cost += record["cost"]
                total_tokens += record["total_tokens"]
                request_count += 1
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "request_count": request_count,
            "daily_costs": self.daily_costs,
            "by_provider": {
                provider: sum(r["cost"] for r in records)
                for provider, records in self.costs.items()
            }
        }
