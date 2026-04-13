# -*- coding: utf-8 -*-
"""
AI资产信息提取器
使用AI从文档中提取设备资产信息
"""
from typing import List, Dict, Any, Optional
from ..ai_service import ai_service, AIMessage, AIResponse
from ..ai_config import ai_config
import json
import logging

logger = logging.getLogger(__name__)

class AIAssetExtractor:
    """基于AI的资产信息提取器"""
    
    def __init__(self):
        self.ai_service = ai_service
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """加载Prompt模板"""
        return """你是一个专业的IT资产信息提取助手。请从以下文档内容中提取设备资产信息。

提取规则：
1. 识别所有设备类型：服务器、网络设备、存储设备、安全设备、数据库、应用程序等
2. 提取关键信息：设备名称、IP地址、主机名、用户名、密码、设备型号、所处网络、部门、备注等
3. 如果某些信息缺失，使用合理的默认值或标记为"未设置"
4. IP地址必须符合IPv4格式
5. 设备名称应简洁明确

输出格式（JSON数组）：
[
  {
    "name": "设备名称",
    "asset_type": "server|network|storage|security|database|application|other",
    "ip_address": "IP地址",
    "hostname": "主机名",
    "username": "用户名",
    "password": "密码",
    "device_model": "设备型号",
    "network_location": "office|monitoring|billing|other",
    "department": "部门",
    "status": "active|inactive|maintenance|retired",
    "notes": "备注信息"
  }
]

文档内容：
{content}

请只输出JSON数组，不要包含其他解释文字。"""
    
    async def extract_from_text(
        self,
        text: str,
        provider: Optional[str] = None,
        use_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """从文本中提取资产信息"""
        
        # 检查文本长度
        if len(text) < 10:
            return []
        
        # 构建Prompt
        prompt = self.prompt_template.format(content=text[:10000])
        
        # 调用AI
        messages = [AIMessage(role="user", content=prompt)]
        from ..ai_config import AIProvider
        provider_enum = AIProvider(provider) if provider else None
        response: AIResponse = await self.ai_service.chat(
            messages=messages,
            provider=provider_enum
        )
        
        if not response.success:
            logger.error(f"AI提取失败: {response.error}")
            if use_fallback:
                return self._fallback_extraction(text)
            return []
        
        # 解析JSON响应
        try:
            # 清理响应文本
            content = response.content.strip()
            
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            assets = json.loads(content)
            
            # 验证和标准化
            validated_assets = []
            for asset in assets:
                if isinstance(asset, dict) and asset.get("name"):
                    validated_assets.append(self._validate_asset(asset))
            
            logger.info(f"AI成功提取 {len(validated_assets)} 个资产")
            return validated_assets
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 内容: {response.content[:200]}")
            if use_fallback:
                return self._fallback_extraction(text)
            return []
    
    async def extract_from_file(
        self,
        file_path: str,
        file_content: bytes,
        file_type: str,
        provider: Optional[str] = None,
        use_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """从文件中提取资产信息"""
        
        try:
            # 先用传统方法提取文本
            from app.services.enhanced_asset_extractor import EnhancedAssetExtractor
            text_extractor = EnhancedAssetExtractor()
            text = text_extractor._extract_text_from_file(file_path, file_content, file_type)
            
            if not text:
                logger.warning("无法从文件中提取文本内容")
                return []
            
            # 使用AI分析文本
            assets = await self.extract_from_text(text, provider, use_fallback)
            
            return assets
            
        except Exception as e:
            logger.error(f"文件提取失败: {e}")
            if use_fallback:
                # 直接使用传统方法
                from app.services.enhanced_asset_extractor import EnhancedAssetExtractor
                extractor = EnhancedAssetExtractor()
                return extractor.extract_from_file(file_path, file_content, file_type)
            return []
    
    def _validate_asset(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化资产信息"""
        # 设置默认值
        defaults = {
            "asset_type": "server",
            "network_location": "office",
            "status": "active",
            "confidence_score": 90
        }
        
        # 合并默认值
        for key, value in defaults.items():
            if key not in asset or not asset[key]:
                asset[key] = value
        
        # 验证IP地址格式
        if asset.get("ip_address"):
            import re
            ip_pattern = r'^\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b$'
            if not re.match(ip_pattern, asset["ip_address"]):
                asset["ip_address"] = ""
        
        # 标准化设备类型
        valid_types = ["server", "network", "storage", "security", "database", "application", "other"]
        if asset.get("asset_type") not in valid_types:
            asset["asset_type"] = "other"
        
        # 标准化网络位置
        valid_locations = ["office", "monitoring", "billing", "other"]
        if asset.get("network_location") not in valid_locations:
            asset["network_location"] = "other"
        
        # 标准化状态
        valid_statuses = ["active", "inactive", "maintenance", "retired"]
        if asset.get("status") not in valid_statuses:
            asset["status"] = "active"
        
        return asset
    
    def _fallback_extraction(self, text: str) -> List[Dict[str, Any]]:
        """降级到传统方法提取"""
        logger.info("降级到传统提取方法")
        from app.services.enhanced_asset_extractor import EnhancedAssetExtractor
        extractor = EnhancedAssetExtractor()
        
        # 简单的文本提取
        assets = []
        try:
            # 尝试从文本中提取资产信息
            import re
            
            # 提取IP地址
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ips = re.findall(ip_pattern, text)
            
            # 提取主机名
            hostname_pattern = r'[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*'
            hostnames = re.findall(hostname_pattern, text)
            
            # 为每个IP创建资产
            for i, ip in enumerate(ips):
                asset = {
                    "name": f"设备-{i+1}",
                    "asset_type": "server",
                    "ip_address": ip,
                    "hostname": hostnames[i] if i < len(hostnames) else "",
                    "username": "",
                    "password": "",
                    "device_model": "",
                    "network_location": "office",
                    "department": "",
                    "status": "active",
                    "notes": "从文档中提取",
                    "confidence_score": 70
                }
                assets.append(asset)
        
        except Exception as e:
            logger.error(f"传统提取失败: {e}")
        
        return assets
