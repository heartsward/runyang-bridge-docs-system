"""
阶段二十七·27.2：OnlyOffice Document Server 集成端点（只读预览）

4 个端点：
- GET  /api/v1/onlyoffice/config                          前端拉配置（DS URL）
- POST /api/v1/onlyoffice/documents/{id}/preview-url      签发只读预览 URL（登录态）
- POST /api/v1/onlyoffice/callback                        DS 回调（免登录，心跳应答）
- GET  /api/v1/onlyoffice/file/{id}                       DS 拉文件 URL（免登录，DS 调用）

调用链路：
1. 用户在前端点"在线预览"
2. 前端调 GET /config 拿 DS URL，再调 POST .../preview-url 拿预览入口 URL
3. 前端 window.open(url) → 跳到 OnlyOffice 预览器（mode=view，无编辑权限）
4. OnlyOffice 通过 GET /file/{id} 拉原文件
5. DS 周期性 POST /callback 心跳（只读模式无保存事件，一律回 error=0）
"""
import logging
import os
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, get_current_active_user
from app.crud import document as crud_document
from app.models.user import User
from app.services.onlyoffice import (
    build_callback_url,
    build_editor_config,
    build_editor_page_url,
    build_file_download_url,
    get_onlyoffice_file_type,
    is_onlyoffice_supported,
    verify_jwt,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 端点 1：前端拉 DS 配置（用于初始化 JS SDK 或直接跳 URL）
# ============================================================
@router.get("/onlyoffice/config", summary="获取 OnlyOffice 配置（前端用）")
def get_onlyoffice_config(current_user: User = Depends(get_current_active_user)):
    """前端初始化 OnlyOffice 编辑器所需的 DS 地址 + 后端回调 base URL"""
    if not settings.ONLYOFFICE_ENABLED:
        raise HTTPException(status_code=404, detail="OnlyOffice 功能未启用")

    return {
        "enabled": True,
        "ds_url": settings.ONLYOFFICE_DS_URL,
        "callback_base_url": settings.ONLYOFFICE_CALLBACK_BASE_URL,
        "available_types": [
            ".doc", ".docx", ".docm", ".odt", ".rtf",
            ".xls", ".xlsx", ".xlsm", ".xlsb", ".csv",
            ".ppt", ".pptx", ".pptm", ".pps", ".ppsx", ".ppsm", ".pot", ".potx", ".odp",
            ".epub",
        ],
        "current_user": {
            "id": current_user.id,
            "name": current_user.username,
        },
    }


# ============================================================
# 端点 2：签发只读预览 URL（27.2：编辑能力已移除）
# ============================================================
@router.post(
    "/onlyoffice/documents/{document_id}/preview-url",
    summary="获取 OnlyOffice 只读预览入口 URL",
)
def get_onlyoffice_preview_url(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """为已登录用户签发 OnlyOffice 只读预览入口 URL

    返回的 URL 已经含 JWT + base64 编码的 config，前端直接 window.open 即可。
    """
    if not settings.ONLYOFFICE_ENABLED:
        raise HTTPException(status_code=404, detail="OnlyOffice 功能未启用")

    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")

    if not is_onlyoffice_supported(document.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"文档类型 {os.path.splitext(document.file_path)[1]} 不支持在线预览",
        )

    file_type = get_onlyoffice_file_type(document.file_path)
    file_name = document.file_name or os.path.basename(document.file_path)

    config = build_editor_config(
        doc_id=document_id,
        file_name=file_name,
        file_type=file_type,
        file_url=build_file_download_url(doc_id=document_id),
        callback_url=build_callback_url(),
        user_id=current_user.id,
        user_name=current_user.username,
        mode="view",  # 27.2：只读预览，禁用编辑
    )

    url = build_editor_page_url(config)

    logger.info(
        f"[OnlyOffice] 签发只读预览 URL doc={document_id} user={current_user.id} type={file_type}"
    )

    # 同时返回 config dict（前端 SDK 直接用，不必再 base64 解码）
    return {
        "url": url,  # SDK 入口 URL（用于显示或直接跳转）
        "config": config,  # 关键：SDK 接受这种格式直接初始化
        "doc_id": document_id,
        "file_name": file_name,
        "file_type": file_type,
    }


# ============================================================
# 端点 3：DS 拉文件 URL（DS 主动访问，必须免登录 + JWT 验签）
# ============================================================
@router.get("/onlyoffice/file/{document_id}", summary="DS 拉文件（OnlyOffice 服务端调用）")
def onlyoffice_download_file(
    document_id: int,
    token: str = Query(..., description="JWT token，verify_jwt 校验"),
    db: Session = Depends(get_db),
):
    """OnlyOffice 调此 URL 拉原文件

    - 免登录（DS 服务器没有用户的 JWT）
    - 必须 JWT 验证（防止任何人拉到文件）
    - 返回文件二进制流
    """
    try:
        payload = verify_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token 已过期")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"token 无效: {e}")

    if payload.get("document_id") != document_id:
        raise HTTPException(status_code=403, detail="token 与文档不匹配")
    if payload.get("purpose") != "file_download":
        raise HTTPException(status_code=403, detail="token 用途错误")

    document = crud_document.get(db=db, id=document_id)
    if not document or not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = document.file_path
    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_FILE_SIZE * 10:
        # OnlyOffice 文件上传通常有 100MB+ 限制，这里给 10x 上限保险
        # 实际限制由 OnlyOffice 决定
        pass

    # 用 FileResponse 流式返回；OnlyOffice 会用 Range 请求支持大文件分块
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(file_path),
    )


# ============================================================
# 端点 4：DS 回调（免登录，只读模式下仅作心跳应答）
# ============================================================
@router.post("/onlyoffice/callback", summary="OnlyOffice 回调（只读心跳）")
async def onlyoffice_callback(request: Request):
    """OnlyOffice 在文档打开/关闭/心跳时回调此端点

    Payload 格式：
    {
        "key": "...",
        "status": 4,           # 1=编辑中心跳 2=保存 4=关闭无修改 6=强制断开
        "url": "...",
        "token": "...",
        "users": [...],
        "actions": [...]
    }

    27.2：系统已改为只读预览（mode=view），DS 不会产生保存事件。
    本端点只做 token 校验 + 记日志 + 回 {"error": 0}，
    **不再下载/覆盖任何文件**，保留它是为了 DS 协议兼容（必须有应答）。
    """
    try:
        body = await request.json()
    except Exception:
        logger.warning("[OnlyOffice] callback: 无法解析 JSON")
        return JSONResponse({"error": 1, "message": "invalid JSON"})

    # 校验 token（DS 在 payload.token 里带了 JWT）
    token = body.get("token", "")
    if not token:
        return JSONResponse({"error": 1, "message": "missing token"})

    try:
        payload = verify_jwt(token)
    except jwt.InvalidTokenError as e:
        logger.warning(f"[OnlyOffice] callback token 验证失败: {e}")
        return JSONResponse({"error": 1, "message": "invalid token"})

    status = body.get("status")
    doc_id = payload.get("document_id")
    logger.info(f"[OnlyOffice] callback（只读心跳）doc={doc_id} status={status}")

    # 只读模式：无论何种状态都不覆盖文件，直接应答成功
    return JSONResponse({"error": 0})