"""
阶段二十七：OnlyOffice Document Server 集成

职责：
- JWT 签发/校验（用 ONLYOFFICE_JWT_SECRET，与 DS 容器一致；不复用用户 SECRET_KEY）
- 文件扩展名 → OnlyOffice fileType / fileTypeKey 映射
- 构造前端 JS SDK 用的 editor config（含回调 URL、文件下载 URL 等）
- 处理 OnlyOffice 保存回调（status=2/4/6）— 从 DS 下载新版覆盖原文件 + 触发重新提取

文档：
- 后端集成: https://api.onlyoffice.com/editors/advancedcontrols.htm
- JS SDK: https://api.onlyoffice.com/editors/sdk/
"""
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

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
    mode: str = "edit",   # edit / view
    lang: str = "zh-CN",
) -> dict:
    """构造 OnlyOffice JS SDK 的 config dict（直接传给 DocEditor）

    重要：所有 URL 必须填绝对 URL；DS 不接受相对路径。
    """
    doc_key = f"doc_{doc_id}_v{int(datetime.now(timezone.utc).timestamp())}"

    # token: 给前端用（DS 同时会用它验签文件下载请求）
    token_payload = {
        "document_id": doc_id,
        "file_type": file_type,
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }
    config_token = sign_jwt(token_payload, expires_in=600)

    return {
        "document": {
            "fileType": file_type,
            "key": doc_key,
            "title": file_name,
            "url": file_url,
            "permissions": {
                "edit": mode == "edit",
                "download": True,
                "print": True,
                "review": True,
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
                "autosave": True,
                "comments": True,
                "review": True,
                "spellcheck": True,
                "compactHeader": False,
                "toolbar": True,
            },
        },
        "token": config_token,
    }


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
    """DS 保存回调后端的 URL"""
    return f"{settings.ONLYOFFICE_CALLBACK_BASE_URL.rstrip('/')}/api/v1/onlyoffice/callback"


# ============================================================
# 回调处理（状态码 + 文件下载）
# ============================================================
# OnlyOffice callback status codes
STATUS_EDITING = 1          # 文档正在编辑
STATUS_SAVE = 2              # 文档保存（用户点保存）
STATUS_SAVE_NO_CHANGES = 3  # 文档保存（无修改，仍通知）
STATUS_CLOSE_NO_CHANGES = 4 # 文档关闭，无修改
STATUS_ERROR = 5            # 错误
STATUS_FORCE_CLOSE = 6      # 强制关闭（无保存）


def download_edited_file_from_ds(download_url: str, target_path: str) -> bool:
    """从 OnlyOffice 临时文件 URL 下载新版文件，覆盖 target_path

    DS 的 URL 在 callback payload 中（url 字段），带 token。
    失败返回 False，不抛异常（callback 必须返回 error=0 给 DS，否则 DS 会重试）。
    """
    import requests
    try:
        # DS 回调的 url 走 DS_JWT 或独立 token，按 OnlyOffice 默认约定
        # payload 里的 url 通常带 token（DS 给的直链），不需要额外 Authorization
        # 但保险起见加个短超时和异常捕获
        resp = requests.get(download_url, timeout=60, stream=True)
        if resp.status_code != 200:
            logger.error(f"[OnlyOffice] 下载失败 status={resp.status_code} url={download_url[:80]}")
            return False

        # 原子写入：临时文件 + rename，避免 DS 写一半导致后端文件损坏
        tmp_path = target_path + ".tmp." + str(os.getpid())
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
        # 确保磁盘写完
        os.replace(tmp_path, target_path)
        logger.info(f"[OnlyOffice] 已下载新版文件 → {target_path}")
        return True
    except Exception as e:
        logger.exception(f"[OnlyOffice] 下载异常: {e}")
        return False