"""
阶段二十七·27.2：OnlyOffice Document Server 集成（只读预览）

职责：
- JWT 签发/校验（用 ONLYOFFICE_JWT_SECRET，与 DS 容器一致；不复用用户 SECRET_KEY）
- 文件扩展名 → OnlyOffice fileType 映射
- 构造前端 JS SDK 用的预览 config（mode=view，含回调 URL、文件下载 URL 等）

27.2：编辑能力已移除——callback 只作心跳应答，不再从 DS 下载/覆盖文件。

文档：
- 后端集成: https://api.onlyoffice.com/editors/advancedcontrols.htm
- JS SDK: https://api.onlyoffice.com/editors/sdk/
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# JWT 工具（用 ONLYOFFICE_JWT_SECRET，与用户登录 SECRET_KEY 隔离）
# ============================================================
def sign_jwt(payload: dict, expires_in: int = 300) -> str:
    """签发 OnlyOffice 用的 JWT（短时效，默认 5 分钟）

    Payload 默认附加 exp + iat，避免时钟漂移。
    """
    import time
    now = int(time.time())
    payload = dict(payload)
    payload.setdefault("iat", now)
    payload.setdefault("exp", now + expires_in)
    return jwt.encode(
        payload,
        settings.ONLYOFFICE_JWT_SECRET,
        algorithm="HS256",
    )


def verify_jwt(token: str) -> dict:
    """校验 OnlyOffice JWT，失败抛 jwt 异常"""
    return jwt.decode(
        token,
        settings.ONLYOFFICE_JWT_SECRET,
        algorithms=["HS256"],
    )


# ============================================================
# 文件类型 → OnlyOffice 类型映射
# ============================================================
# 文件扩展名（小写）→ OnlyOffice "fileType" 字段
# 详见 https://api.onlyoffice.com/editors/supportedformats.htm
SUPPORTED_OFFICE_EXTENSIONS = {
    # Word
    ".docx": "docx", ".doc": "doc", ".docm": "docx",
    # Excel
    ".xlsx": "xlsx", ".xls": "xls", ".xlsm": "xlsx", ".xlsb": "xlsx", ".csv": "csv",
    # PowerPoint
    ".pptx": "pptx", ".ppt": "ppt", ".pptm": "pptx",
    ".ppsx": "pptx", ".pps": "ppt", ".ppsm": "pptx", ".pot": "ppt", ".potx": "pptx",
    # OpenDocument
    ".odt": "odt", ".ods": "ods", ".odp": "odp",
    # 富文本
    ".rtf": "rtf",
    # 电子书
    ".epub": "epub",
}


def get_onlyoffice_file_type(file_path: str) -> Optional[str]:
    """从文件路径取 OnlyOffice fileType，未知类型返回 None"""
    ext = os.path.splitext(file_path)[1].lower()
    return SUPPORTED_OFFICE_EXTENSIONS.get(ext)


def is_onlyoffice_supported(file_path: str) -> bool:
    return get_onlyoffice_file_type(file_path) is not None


# ============================================================
# 编辑器 config 构造（给前端 JS SDK 用）
# ============================================================
def build_editor_config(
    *,
    doc_id: int,
    file_name: str,
    file_type: str,
    file_url: str,        # DS 可访问的文件下载 URL（后端提供，需带 token）
    callback_url: str,    # DS 保存后回调后端的 URL
    user_id: int,
    user_name: str,
    mode: str = "view",   # view（只读预览，默认）/ edit（编辑，27.2 已弃用）
    lang: str = "zh-CN",
) -> dict:
    """构造 OnlyOffice JS SDK 的 config dict（直接传给 DocEditor）

    阶段二十七·27.2：默认 mode='view'（只读预览，不允许编辑）。
    编辑功能完全回退：用户改主意不想编辑 Office 文件，只想在线预览。
    callback 端点仍保留（DS 在用户关闭编辑器时仍会发 status=4 心跳）。
    重要：所有 URL 必须填绝对 URL；DS 不接受相对路径。
    """
    doc_key = f"doc_{doc_id}_v{int(datetime.now(timezone.utc).timestamp())}"

    is_view_mode = mode == "view"
    config = {
        "document": {
            "fileType": file_type,
            "key": doc_key,
            "title": file_name,
            "url": file_url,
            "permissions": {
                "edit": not is_view_mode,
                "download": True,
                "print": True,
                "review": not is_view_mode,
            },
        },
        "editorConfig": {
            "mode": mode,
            "lang": lang,
            "user": {
                "id": f"user_{user_id}",
                "name": user_name,
            },
            "callbackUrl": callback_url,
            "customization": {
                "autosave": False,   # 只读预览不需要自动保存
                "comments": not is_view_mode,  # 只读预览禁用评论
                "review": not is_view_mode,
                "spellcheck": True,
                "compactHeader": False,
                "toolbar": True,
                # viewer 专用缩放：-2 = 适应页宽（宽屏下文档不再缩成中间窄条）
                "zoom": -2 if is_view_mode else 100,
            },
        },
    }

    # 27.3：DS 开了 JWT 校验时，token payload 必须是【整个 config 对象】
    # （官方约定：token = JWT(secret, config)，DS 逐字段比对；
    #  之前只签 {document_id, file_type} → 报"文档安全令牌的格式不正确"）
    config["token"] = sign_jwt(dict(config), expires_in=600)
    return config


# ============================================================
# 编辑 URL 构造（前端 window.open 用）
# ============================================================
def build_editor_page_url(config: dict) -> str:
    """构造 OnlyOffice 编辑器入口 URL

    格式：{DS_URL}/web-apps/apps/api/documents/api.js?config=...
    config 用 base64 编码成 URL 参数。
    """
    import base64
    # DS API 要求 config 必须 base64 编码
    config_b64 = base64.b64encode(json.dumps(config).encode("utf-8")).decode("ascii")
    return f"{settings.ONLYOFFICE_DS_URL.rstrip('/')}/web-apps/apps/api/documents/api.js?config={config_b64}"


# ============================================================
# 文件下载 URL（DS 通过此 URL 拉文件 + 保存时回推）
# ============================================================
def build_file_download_url(*, doc_id: int) -> str:
    """DS 拉文件的 URL（带 JWT）

    注意：DS 是从自己的 callback URL 反向访问此 URL，必须网络可达；
    该 URL 也必须走 GET，且 header 带 Authorization: Bearer <jwt>。
    """
    token = sign_jwt({"document_id": doc_id, "purpose": "file_download"}, expires_in=600)
    return f"{settings.ONLYOFFICE_CALLBACK_BASE_URL.rstrip('/')}/api/v1/onlyoffice/file/{doc_id}?token={token}"


def build_callback_url() -> str:
    """DS 回调后端的 URL（只读模式下仅心跳）"""
    return f"{settings.ONLYOFFICE_CALLBACK_BASE_URL.rstrip('/')}/api/v1/onlyoffice/callback"