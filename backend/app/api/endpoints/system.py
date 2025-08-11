# -*- coding: utf-8 -*-
"""
系统信息API端点
提供服务器状态、配置信息等系统级API
"""
import time
import platform
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_optional_user
from app.core.config import settings
from app.models.user import User
from app.schemas.mobile import MobileBaseResponse

router = APIRouter()


class SystemInfoResponse(MobileBaseResponse):
    """系统信息响应"""
    data: Dict[str, Any]


@router.get("/info", response_model=SystemInfoResponse, summary="获取系统信息")
async def get_system_info(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取服务器基本信息
    - 系统状态
    - API版本信息 
    - 支持的功能列表
    - 移动端配置参数
    """
    start_time = time.time()
    
    try:
        # 系统基础信息
        system_info = {
            "server_name": "润扬大桥运维文档管理系统",
            "version": "1.0.2",
            "api_version": "v1.1",
            "build_time": "2024-08-10",
            "environment": getattr(settings, 'ENVIRONMENT', 'production')
        }
        
        # 服务器状态
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            server_status = {
                "status": "healthy",
                "uptime": time.time() - psutil.boot_time(),
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "memory_total": f"{memory.total / (1024**3):.1f}GB",
                "disk_usage": f"{disk.percent:.1f}%",
                "disk_free": f"{disk.free / (1024**3):.1f}GB"
            }
        except Exception as e:
            server_status = {
                "status": "unknown",
                "error": f"无法获取系统状态: {str(e)}"
            }
        
        # 平台信息
        platform_info = {
            "os": platform.system(),
            "os_version": platform.release(),
            "python_version": platform.python_version(),
            "architecture": platform.machine()
        }
        
        # API功能支持列表
        supported_features = {
            "authentication": True,
            "document_management": True,
            "asset_management": True,
            "intelligent_search": True,
            "mobile_api": True,
            "voice_query": True,  # 准备支持
            "file_upload": True,
            "multi_file_upload": True,
            "analytics": True,
            "user_management": True,
            "offline_cache": True,  # 移动端支持
            "push_notifications": False  # 待实现
        }
        
        # 移动端配置
        mobile_config = {
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "supported_file_types": [
                "pdf", "doc", "docx", "txt", "md", 
                "xls", "xlsx", "csv", "jpg", "jpeg", "png"
            ],
            "cache_duration": 3600,  # 1小时
            "pagination_size": 20,
            "search_limit": 100,
            "token_expiry_days": 30,
            "refresh_token_expiry_days": 60
        }
        
        # API端点列表
        api_endpoints = {
            "authentication": {
                "login": "/api/v1/auth/login",
                "mobile_login": "/api/v1/mobile/auth/login", 
                "refresh": "/api/v1/mobile/auth/refresh",
                "profile": "/api/v1/mobile/auth/profile"
            },
            "documents": {
                "list": "/api/v1/mobile/documents/",
                "detail": "/api/v1/mobile/documents/{id}",
                "search": "/api/v1/mobile/documents/search",
                "upload": "/api/v1/upload/single",
                "download": "/api/v1/documents/{id}/download"
            },
            "assets": {
                "list": "/api/v1/mobile/assets/",
                "detail": "/api/v1/mobile/assets/{id}",
                "search": "/api/v1/mobile/assets/search"
            },
            "voice_query": {
                "query": "/api/v1/voice/query",
                "parse": "/api/v1/voice/parse",
                "suggest": "/api/v1/voice/suggest"
            },
            "system": {
                "info": "/api/v1/system/info",
                "health": "/api/v1/system/health"
            }
        }
        
        # 安全配置（公开信息）
        security_info = {
            "authentication_required": True,
            "token_type": "Bearer",
            "https_enabled": False,  # 可根据实际情况调整
            "cors_enabled": True,
            "rate_limiting": False   # 待实现
        }
        
        # 数据库连接状态
        try:
            # 测试数据库连接
            db.execute("SELECT 1")
            database_status = {
                "status": "connected",
                "type": "SQLite",
                "version": "3.x"
            }
        except Exception as e:
            database_status = {
                "status": "error",
                "error": str(e)
            }
        
        # 汇总所有信息
        response_data = {
            "system": system_info,
            "server_status": server_status,
            "platform": platform_info,
            "features": supported_features,
            "mobile_config": mobile_config,
            "api_endpoints": api_endpoints,
            "security": security_info,
            "database": database_status,
            "response_time": f"{(time.time() - start_time) * 1000:.0f}ms",
            "server_time": datetime.utcnow().isoformat() + "Z"
        }
        
        return SystemInfoResponse(
            success=True,
            message="系统信息获取成功",
            data=response_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取系统信息失败: {str(e)}"
        )


@router.get("/health", summary="健康检查")
async def health_check(
    db: Session = Depends(get_db)
):
    """
    简单的健康检查端点
    用于负载均衡器和监控系统
    """
    try:
        # 测试数据库连接
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "润扬大桥运维文档管理系统",
            "version": "1.0.2"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get("/version", summary="获取版本信息")
async def get_version():
    """获取API版本信息"""
    return {
        "api_version": "v1.1",
        "system_version": "1.0.2",
        "build_date": "2024-08-10",
        "features": {
            "mobile_api": "1.0.0",
            "voice_query": "0.9.0",  # 开发中
            "core_features": "1.0.2"
        }
    }


@router.get("/capabilities", summary="获取系统能力")
async def get_capabilities():
    """
    获取系统支持的功能能力
    用于移动端动态调整功能
    """
    return {
        "document_formats": [
            "pdf", "doc", "docx", "txt", "md", "rtf"
        ],
        "image_formats": [
            "jpg", "jpeg", "png", "gif", "bmp"
        ],
        "spreadsheet_formats": [
            "xls", "xlsx", "csv"
        ],
        "search_capabilities": {
            "full_text_search": True,
            "fuzzy_search": True,
            "category_filter": True,
            "date_range_filter": True,
            "content_type_filter": True
        },
        "mobile_features": {
            "offline_cache": True,
            "background_sync": False,
            "push_notifications": False,
            "biometric_auth": False,
            "voice_search": True  # 准备支持
        },
        "limits": {
            "max_file_size_mb": 10,
            "max_files_per_upload": 10,
            "search_results_per_page": 20,
            "api_rate_limit_per_minute": 1000
        }
    }