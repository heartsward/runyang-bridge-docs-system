"""
统一 AI 服务配置 API（阶段七：精简版）

只保留 1 个统一 AI 服务配置（替代之前 3 个）。
- provider: ollama | openai
- url: AI 服务地址
- model: 模型名
- api_key: 仅在线服务需要
- timeout: 超时
- enabled: 总开关
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


class ExtractionConfig(BaseModel):
    """统一 AI 服务配置"""

    ai_service_enabled: bool = False
    ai_service_provider: str = "openai"  # ollama | openai
    ai_service_url: str = "http://localhost:8080/v1"
    ai_service_model: str = "qwen3-vl-8b"
    ai_service_api_key: str = ""  # 仅在线服务需要
    ai_service_timeout: int = 120
    ai_fallback_to_local: bool = True
    ai_all_formats_ai: bool = False  # 阶段十三：True=所有格式(docx/xlsx/txt)也走 AI 提取；False=仅 PDF+图片

    # 兼容旧字段（阶段五 OCR 配置，可选）
    ai_ocr_enabled: bool = False
    ai_ocr_service_url: str = "http://localhost:8001"


def _load_from_settings() -> ExtractionConfig:
    return ExtractionConfig(
        ai_service_enabled=getattr(settings, "AI_SERVICE_ENABLED", False),
        ai_service_provider=getattr(settings, "AI_SERVICE_PROVIDER", "openai"),
        ai_service_url=getattr(settings, "AI_SERVICE_URL", "http://localhost:8080/v1"),
        ai_service_model=getattr(settings, "AI_SERVICE_MODEL", "qwen3-vl-8b"),
        ai_service_api_key=getattr(settings, "AI_SERVICE_API_KEY", ""),
        ai_service_timeout=getattr(settings, "AI_SERVICE_TIMEOUT", 120),
        ai_fallback_to_local=getattr(settings, "AI_FALLBACK_TO_LOCAL", True),
        ai_all_formats_ai=getattr(settings, "AI_ALL_FORMATS_AI", False),
        ai_ocr_enabled=getattr(settings, "AI_OCR_ENABLED", False),
        ai_ocr_service_url=getattr(settings, "AI_OCR_SERVICE_URL", "http://localhost:8001"),
    )


def _parse_available_models(payload: dict, provider: str) -> list:
    """从 /models（openai 兼容）或 /api/tags（ollama）响应里解析模型 ID 列表。"""
    ids = []
    if not isinstance(payload, dict):
        return ids
    # openai 兼容：data[].id（llama.cpp 也在 data[].model / models[].name）
    for m in payload.get("data", []) or []:
        mid = m.get("id") or m.get("model")
        if mid:
            ids.append(mid)
    for m in payload.get("models", []) or []:
        mid = m.get("name") or m.get("model")
        if mid:
            ids.append(mid)
    # ollama：models[].name
    return ids


def _match_model(requested: str, available: list) -> bool:
    """判断请求的模型名是否命中服务里实际加载的某个模型。

    采用**严格匹配**：llama.cpp 等服务的 /chat/completions 按"加载时的完整 ID"
    精确匹配，短名/子串会 404。因此这里只认下列等价形式（任一命中即 True）：
    - 精确相等
    - 路径尾段相等（.../model.gguf vs model.gguf）
    - 去扩展名后相等（model.gguf vs model）
    不做子串包含匹配——否则短名会被误判为"可用"，而真实提取请求仍会 404。
    """
    if not requested or not available:
        return False
    req = requested.strip()
    req_lower = req.lower()
    req_stem = req.rsplit(".", 1)[0].lower() if "." in req else req_lower
    for m in available:
        m_str = str(m)
        m_lower = m_str.lower()
        base = m_str.rsplit("/", 1)[-1]                 # 去路径
        base_stem = base.rsplit(".", 1)[0] if "." in base else base  # 去扩展名
        if req_lower in (m_lower, base.lower(), base_stem.lower()):
            return True
        if req_stem == base_stem.lower():
            return True
    return False


@router.get("/extraction-config", response_model=ExtractionConfig, summary="拉取 AI 服务配置")
async def get_extraction_config(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return _load_from_settings()


@router.put("/extraction-config", summary="更新 AI 服务配置")
async def update_extraction_config(
    cfg: ExtractionConfig,
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    from pathlib import Path

    env_file = Path(__file__).parent.parent.parent.parent / ".env"

    env_lines = []
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                ls = line.rstrip("\n")
                if not any(ls.startswith(k) for k in [
                    "AI_SERVICE_ENABLED=", "AI_SERVICE_PROVIDER=", "AI_SERVICE_URL=",
                    "AI_SERVICE_MODEL=", "AI_SERVICE_API_KEY=", "AI_SERVICE_TIMEOUT=",
                    "AI_FALLBACK_TO_LOCAL=", "AI_ALL_FORMATS_AI=", "AI_OCR_ENABLED=", "AI_OCR_SERVICE_URL=",
                    "AI_OCR_SERVICE_URL=", "AI_PDF_ENABLED=", "AI_PDF_SERVICE_URL=",
                    "AI_VLM_ENABLED=", "AI_VLM_SERVICE_URL=", "AI_VLM_MODEL=",
                ]):
                    env_lines.append(ls)

    env_lines.append(f"AI_SERVICE_ENABLED={'true' if cfg.ai_service_enabled else 'false'}")
    env_lines.append(f"AI_SERVICE_PROVIDER={cfg.ai_service_provider}")
    env_lines.append(f"AI_SERVICE_URL={cfg.ai_service_url}")
    env_lines.append(f"AI_SERVICE_MODEL={cfg.ai_service_model}")
    env_lines.append(f"AI_SERVICE_API_KEY={cfg.ai_service_api_key}")
    env_lines.append(f"AI_SERVICE_TIMEOUT={cfg.ai_service_timeout}")
    env_lines.append(f"AI_FALLBACK_TO_LOCAL={'true' if cfg.ai_fallback_to_local else 'false'}")
    env_lines.append(f"AI_ALL_FORMATS_AI={'true' if cfg.ai_all_formats_ai else 'false'}")
    env_lines.append(f"AI_OCR_ENABLED={'true' if cfg.ai_ocr_enabled else 'false'}")
    env_lines.append(f"AI_OCR_SERVICE_URL={cfg.ai_ocr_service_url}")

    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入 .env 失败: {e}")

    # 关键修复：写完 .env 后刷新内存 settings，让新配置立即生效（无需重启进程）。
    # 之前只写文件不刷新，导致运行中进程仍用旧值 → 用户看到"保存后恢复默认"。
    try:
        settings.reload()
    except Exception as e:
        # 热刷新失败不阻断保存（.env 已落盘，重启后仍生效），仅记录
        print(f"[extraction_config] settings.reload 失败（重启后生效）: {e}")

    return {
        "success": True,
        "restart_required": False,
        "message": "配置已保存并立即生效（无需重启）。",
        "saved_to": str(env_file),
    }


@router.post("/extraction-config/test", summary="测试 AI 服务连接")
async def test_extraction_config(
    cfg: ExtractionConfig,
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    import requests

    results = {}

    # 统一 AI 服务
    if cfg.ai_service_enabled:
        try:
            url = cfg.ai_service_url.rstrip("/")
            if cfg.ai_service_provider == "ollama":
                r = requests.get(f"{url}/api/tags", timeout=5)
            else:
                r = requests.get(f"{url}/models", timeout=5)

            ai_result = {
                "reachable": r.status_code < 500,
                "status": r.status_code,
                "endpoint": f"{url}/models" if cfg.ai_service_provider != "ollama" else f"{url}/api/tags",
            }

            # 阶段十四：校验"模型名"是否真的在服务中加载（服务可达 ≠ 模型可用）
            if r.status_code < 500:
                available = _parse_available_models(r.json(), cfg.ai_service_provider)
                if available:
                    found = _match_model(cfg.ai_service_model, available)
                    ai_result["model"] = {
                        "requested": cfg.ai_service_model,
                        "found": found,
                        "available_models": available,
                    }
                    if not found:
                        ai_result["model"]["hint"] = (
                            "服务可达，但未找到名为 "
                            f"'{cfg.ai_service_model}' 的模型。llama.cpp 等服务的模型 ID 可能是"
                            "完整文件路径（见 available_models），请把模型名改成服务返回的实际 ID。"
                        )
            results["ai_service"] = ai_result
        except Exception as e:
            results["ai_service"] = {"reachable": False, "error": str(e)[:100]}

    # OCR 服务（可选）
    if cfg.ai_ocr_enabled:
        try:
            r = requests.get(cfg.ai_ocr_service_url, timeout=5)
            results["ocr_service"] = {
                "reachable": r.status_code < 500,
                "status": r.status_code,
            }
        except Exception as e:
            results["ocr_service"] = {"reachable": False, "error": str(e)[:100]}

    return {"results": results}