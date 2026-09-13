"""
AI 元数据生成（title + tags）

阶段十·Q4：所有文档都用 AI 生成（.md/.txt 也调一次）
阶段十·Q5：可通过 AI_METADATA_ENABLED 开关关闭
"""
import json
import logging
import re
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

# 阶段十八·18.5：业务分类受控词表（AI 必须从中选一项）
DOC_CATEGORIES = [
    "运维报告", "应急预案", "操作规程", "资产台账",
    "拓扑与配置", "会议纪要", "培训材料", "其他",
]

METADATA_PROMPT = """你是文档元数据生成器。请分析以下文档内容，输出严格 JSON（无解释、无前缀）：

{
  "title": "文档标题（不超过 30 字）",
  "tags": ["标签1", "标签2", "标签3"],
  "doc_category": "业务分类"
}

要求：
1. title 用中文，简洁、准确；能从文件名或内容推断
2. tags 3-5 个关键词（领域/类型/主题）
3. doc_category 必须从以下词表中选一项（不要自创）：运维报告 / 应急预案 / 操作规程 / 资产台账 / 拓扑与配置 / 会议纪要 / 培训材料 / 其他
4. 仅输出 JSON 对象本身，不要 ```json``` 围栏"""


def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """从模型输出提取 JSON（容忍 markdown 围栏、前后空格）"""
    if not text:
        return None
    text = text.strip()
    # 去除可能的 markdown 围栏
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试找第一个 {...}
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None


async def generate_metadata_via_ai(
    content_sample: str,
    fallback_title: str = "",
    fallback_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """用 AI 生成 title/tags；失败回退到 fallback

    Args:
        content_sample: 文档内容前 ~2000 字（节省 token）
        fallback_title: AI 失败时使用的标题（通常是文件名）
        fallback_tags: AI 失败时使用的标签（可空）
    Returns:
        {"title": str, "tags": [str, ...]}
    """
    from app.core.config import settings

    if not getattr(settings, "AI_METADATA_ENABLED", True):
        return {
            "title": fallback_title,
            "tags": fallback_tags or [],
            "doc_category": "其他",
        }

    if not getattr(settings, "AI_SERVICE_ENABLED", False):
        return {
            "title": fallback_title,
            "tags": fallback_tags or [],
            "doc_category": "其他",
        }

    try:
        from app.services.extraction.ai_client import get_unified_ai_client

        client = get_unified_ai_client()
        if not client.is_enabled():
            return {"title": fallback_title, "tags": fallback_tags or [], "doc_category": "其他"}

        # 截取前 2000 字
        sample = content_sample[:2000] if len(content_sample) > 2000 else content_sample

        # 复用 UnifiedAIClient 的 openai/ollama 调用（不发图片，纯文本）
        prompt = f"{METADATA_PROMPT}\n\n文件名：{fallback_title}\n\n文档内容片段：\n{sample}"
        text = await _chat(client, prompt)
        if not text:
            return {"title": fallback_title, "tags": fallback_tags or [], "doc_category": "其他"}

        parsed = parse_json_response(text)
        if parsed and "title" in parsed:
            # 阶段十八·18.5：category 受控词表校验（词表外的归"其他"）
            category = str(parsed.get("doc_category", "")).strip()
            if category not in DOC_CATEGORIES:
                category = "其他"
            return {
                "title": str(parsed.get("title", fallback_title)).strip()[:80],
                "tags": [str(t).strip() for t in parsed.get("tags", []) if str(t).strip()][:5],
                "doc_category": category,
            }

        # JSON 解析失败，尝试简单启发式
        logger.warning(f"AI 元数据 JSON 解析失败: {text[:200]}")
        return {"title": fallback_title, "tags": fallback_tags or [], "doc_category": "其他"}

    except Exception as e:
        logger.exception(f"AI 元数据生成失败: {e}")
        return {"title": fallback_title, "tags": fallback_tags or [], "doc_category": "其他"}


# 阶段十八·18.2：图片描述 prompt
IMAGE_DESCRIBE_PROMPT = """请描述这张图片的内容，用于文档检索。要求：
1. 用中文，不超过 60 字，一句话
2. 说明图的类型与关键内容：如"网络拓扑图，含核心交换机与汇聚层连线"、"设备台账表格，列有 IP 与端口"、"机房现场照片，显示机柜与配线架"
3. 只输出描述本身，不要任何前缀/解释"""


async def describe_image_via_ai(image_path, fallback_caption: str = "") -> str:
    """用多模态 AI 生成图片中文描述（≤60 字）

    Args:
        image_path: 图片文件路径
        fallback_caption: AI 关闭/失败时的回退文案（如 "第3页图1"）
    Returns:
        描述文本（永远非空：失败时返回 fallback_caption 或占位）
    """
    from pathlib import Path
    p = Path(image_path)

    fallback = fallback_caption or "文档图片"
    if not p.exists() or p.stat().st_size == 0:
        return fallback

    try:
        from app.core.config import settings
        if not getattr(settings, "AI_SERVICE_ENABLED", False):
            return fallback

        from app.services.extraction.ai_client import get_unified_ai_client
        from app.services.wiki.image_extractor import image_mime
        client = get_unified_ai_client()
        if not client.is_enabled():
            return fallback

        image_bytes = p.read_bytes()
        mime = image_mime(p.suffix)

        # max_tokens=2048：thinking 模型需预留 reasoning token，128 会导致 content 为空
        text, error = client.describe_image(image_bytes, mime_type=mime, max_tokens=2048)
        if not text:
            logger.warning(f"图片描述 AI 返回空: {error}")
            return fallback

        # 清洗：去引号/围栏，压成单行，限长
        caption = text.strip().strip('"\'`').replace("\n", " ").strip()
        # 去掉可能的"描述："前缀
        for prefix in ("描述：", "描述:", "图片描述：", "图片描述:"):
            if caption.startswith(prefix):
                caption = caption[len(prefix):].strip()
        return caption[:80] or fallback
    except Exception as e:
        logger.exception(f"图片描述生成失败 {p.name}: {e}")
        return fallback


async def _chat(client, prompt: str) -> str:
    """调 UnifiedAIClient.chat（不带图片）"""
    import requests

    if client.provider == "ollama":
        url = f"{client.url}/api/chat"
        payload = {
            "model": client.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 512, "temperature": 0.1},
        }
    else:
        # OpenAI 兼容（llama.cpp server / DashScope / vLLM）
        url = f"{client.url}/chat/completions"
        payload = {
            "model": client.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.1,
        }

    headers = {"Content-Type": "application/json"}
    if client.api_key:
        headers["Authorization"] = f"Bearer {client.api_key}"

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=client.timeout)
        if r.status_code != 200:
            logger.warning(f"AI 元数据 API 返回 {r.status_code}: {r.text[:200]}")
            return ""
        data = r.json()
        if client.provider == "ollama":
            return data.get("message", {}).get("content", "")
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""
    except requests.Timeout:
        logger.warning(f"AI 元数据调用超时")
        return ""
    except Exception as e:
        logger.exception(f"AI 元数据 HTTP 调用失败: {e}")
        return ""