"""
阶段二十七：OnlyOffice Document Server 集成端点

4 个端点：
- GET  /api/v1/onlyoffice/config                  前端拉配置（DS URL）
- POST /api/v1/onlyoffice/documents/{id}/url      签发编辑 URL（登录态）
- POST /api/v1/onlyoffice/callback                DS 保存回调（免登录，DS 服务器调用）
- GET  /api/v1/onlyoffice/file/{id}               DS 拉文件 URL（免登录，DS 调用）

调用链路：
1. 用户在前端点"在线编辑"
2. 前端调 GET /config 拿 DS URL，再调 POST .../url 拿编辑入口 URL
3. 前端 window.open(url) → 跳到 OnlyOffice 编辑器
4. OnlyOffice 通过 GET /file/{id} 拉原文件
6. 用户编辑完，OnlyOffice 通过 POST /callback 通知保存
7. callback 端点从 DS URL 下载新版文件，覆盖 uploads/{file}
8. 触发重新提取（内容提取 + AI 描述）
9. 返回 {"error": 0} 给 DS
"""
import logging
import os
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.crud import document as crud_document
from app.models.user import User
from app.services.onlyoffice import (
    STATUS_SAVE,
    STATUS_CLOSE_NO_CHANGES,
    build_callback_url,
    build_editor_config,
    build_editor_page_url,
    build_file_download_url,
    download_edited_file_from_ds,
    get_onlyoffice_file_type,
    is_onlyoffice_supported,
    sign_jwt,
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
# 端点 2：签发编辑 URL
# ============================================================
@router.post(
    "/onlyoffice/documents/{document_id}/url",
    summary="获取 OnlyOffice 编辑器入口 URL",
)
def get_onlyoffice_edit_url(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """为已登录用户签发 OnlyOffice 编辑器入口 URL

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
            detail=f"文档类型 {os.path.splitext(document.file_path)[1]} 不支持在线编辑",
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
        mode="edit",
    )

    url = build_editor_page_url(config)

    logger.info(
        f"[OnlyOffice] 签发编辑 URL doc={document_id} user={current_user.id} type={file_type}"
    )

    return {
        "url": url,
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
# 端点 4：DS 保存回调（免登录）
# ============================================================
@router.post("/onlyoffice/callback", summary="OnlyOffice 保存回调")
async def onlyoffice_callback(request: Request, db: Session = Depends(get_db)):
    """OnlyOffice 在文档保存/关闭时回调此端点

    Payload 格式：
    {
        "key": "...",
        "status": 2,           # 2=保存 4=关闭无修改 6=强制断开
        "url": "...",          # DS 上临时文件 URL（status=2/6 时）
        "token": "...",
        "users": [...],
        "actions": [...]
    }

    - 必须免登录：DS 没有用户 token，用自己的 JWT 校验
    - status=2 时需要下载新版文件并覆盖原文件
    - status=4 时直接返回 error=0
    - status=6 时同样下载 + 覆盖（强制断开 = 用户最后编辑过的版本）
    """
    try:
        body = await request.json()
    except Exception:
        logger.warning("[OnlyOffice] callback: 无法解析 JSON")
        return JSONResponse({"error": 1, "message": "invalid JSON"})

    # 1) 校验 token（DS 在 payload.token 里带了 JWT）
    token = body.get("token", "")
    if not token:
        return JSONResponse({"error": 1, "message": "missing token"})

    try:
        payload = verify_jwt(token)
    except jwt.InvalidTokenError as e:
        logger.warning(f"[OnlyOffice] callback token 验证失败: {e}")
        return JSONResponse({"error": 1, "message": "invalid token"})

    status = body.get("status")
    download_url = body.get("url", "")
    doc_id = payload.get("document_id")
    logger.info(f"[OnlyOffice] callback doc={doc_id} status={status}")

    if status == STATUS_CLOSE_NO_CHANGES:
        # 文档关闭无修改，不下载
        return JSONResponse({"error": 0})

    if status not in (STATUS_SAVE, 2, 6):
        # 状态 1=正在编辑（DS 周期性发，不算回调）
        # 状态 5=错误
        # 其它未知状态 → 也返回 error=0（DS 不会再重试）
        return JSONResponse({"error": 0})

    # 2) 查文档
    document = crud_document.get(db=db, id=doc_id)
    if not document or not document.file_path:
        logger.warning(f"[OnlyOffice] callback 文档 {doc_id} 不存在")
        return JSONResponse({"error": 1, "message": "document not found"})

    target_path = document.file_path
    if not os.path.exists(target_path):
        logger.warning(f"[OnlyOffice] callback 文档 {doc_id} 路径无效: {target_path}")
        return JSONResponse({"error": 1, "message": "file path invalid"})

    # 3) 下载新版文件 + 覆盖原文件
    if not download_url:
        return JSONResponse({"error": 1, "message": "no download url"})

    ok = download_edited_file_from_ds(download_url, target_path)
    if not ok:
        return JSONResponse({"error": 1, "message": "download failed"})

    # 4) 触发重新提取（异步，不阻塞 DS 回调）
    try:
        from app.services.background_tasks import get_task_manager
        task_manager = get_task_manager()
        # 先标记为"未中中"
        document.content_extracted = None
        document.content_extraction_error = None
        db.commit()
        db.refresh(document)

        task_manager.add_content_extraction_task(
            document_id=document.id,
            file_path=document.file_path,
            title=document.title,
        )
        logger.info(f"[OnlyOffice] 触发文档 {doc_id} 重新提取")
    except Exception as e:
        logger.exception(f"[OnlyOffice] 触发重新提取失败: {e}")

    return JSONResponse({"error": 0})