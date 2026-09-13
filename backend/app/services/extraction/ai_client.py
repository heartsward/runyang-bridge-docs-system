"""
AI 服务客户端（阶段七：统一多模态接口）

设计：一个客户端类 UnifiedAIClient，支持 2 种 provider
- ollama：本地部署（Ollama 服务跑 qwen3-vl 等多模态模型）
- openai：在线 API（DashScope / OpenAI / vLLM 等 OpenAI 兼容端点）

客户端处理：
- 多模态输入（图片 base64）
- 文档解析专用 prompt（强制输出 Markdown）
- 失败返回 (None, error_msg) 让调用方降级

旧客户端（PaddleOCRClient / MinerUClient）保留作为高速/低成本 fallback。
"""
import logging
import base64
import json
from typing import Optional, Tuple, Dict, Any, List

import requests

logger = logging.getLogger(__name__)


# 文档解析统一 prompt
DOC_PARSE_PROMPT = """你是专业的文档解析引擎。请仔细查看图片中的文档内容，并按以下规则输出 Markdown：

1. **标题层级**：用 # 一级标题、## 二级标题、### 三级标题
2. **段落**：用普通段落，保留原文换行
3. **表格**：必须用 Markdown 表格格式：
   ```
   | 列1 | 列2 | 列3 |
   | --- | --- | --- |
   | 数据 | 数据 | 数据 |
   ```
4. **列表**：有序列表用 `1. 2. 3.`，无序列表用 `-`
5. **公式**：行内用 `$...$`，块级用 `$$...$$`
6. **图片/图表**：插入 `![描述](占位)` 并简要说明
7. **不要编造**：看不到的内容不要猜测
8. **不输出解释**：只输出 Markdown 内容本身，不要"以下是..."等废话

请开始："""


class BaseAIClient:
    """AI 客户端基类"""

    def __init__(self, url: str, timeout: int = 120, enabled: bool = False):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled

    def health_check(self) -> bool:
        if not self.enabled:
            return False
        try:
            r = requests.get(self.url, timeout=5)
            return r.status_code < 500
        except Exception:
            return False


class PaddleOCRClient(BaseAIClient):
    """PaddleOCR 服务客户端（保留为高速 CPU 兜底）"""

    def ocr(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        if not self.enabled:
            return None, "PaddleOCR 服务未启用"
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.split("/")[-1].split("\\")[-1], f, "application/octet-stream")}
                r = requests.post(f"{self.url}/ocr", files=files, timeout=self.timeout)
            if r.status_code != 200:
                return None, f"PaddleOCR 返回 {r.status_code}: {r.text[:200]}"
            data = r.json()
            text = data.get("text", "")
            if not text:
                return None, "PaddleOCR 返回空文本"
            return text.strip(), None
        except requests.Timeout:
            return None, f"PaddleOCR 超时（>{self.timeout}s）"
        except Exception as e:
            return None, f"PaddleOCR 调用失败: {e}"


class UnifiedAIClient:
    """统一多模态 AI 客户端（阶段七核心）

    支持 provider:
    - ollama: 本地 Ollama 服务（POST /api/chat）
    - openai: 任意 OpenAI 兼容端点（DashScope / OpenAI / vLLM）

    用途：文档解析（PDF/图片 → Markdown）
    """

    def __init__(
        self,
        url: str,
        provider: str = "ollama",
        model: str = "qwen3-vl:latest",
        timeout: int = 120,
        enabled: bool = False,
        api_key: str = "",
    ):
        self.url = url.rstrip("/")
        self.provider = provider.lower()
        self.model = model
        self.timeout = timeout
        self.enabled = enabled
        self.api_key = api_key

    def is_enabled(self) -> bool:
        return self.enabled

    def health_check(self) -> bool:
        """健康检查（Ollama 探测 /api/tags，OpenAI 探测 /models）"""
        if not self.enabled:
            return False
        try:
            if self.provider == "ollama":
                r = requests.get(f"{self.url}/api/tags", timeout=5)
                return r.status_code == 200
            else:
                # openai 兼容
                r = requests.get(f"{self.url}/models", timeout=5)
                return r.status_code == 200
        except Exception:
            return False

    def vision_parse(
        self,
        images: List[bytes],
        mime_type: str = "image/png",
        prompt: str = DOC_PARSE_PROMPT,
        max_tokens: int = 4096,
    ) -> Tuple[Optional[str], Optional[str]]:
        """调用多模态模型解析图片列表（多页文档场景）

        Args:
            images: 图片字节列表（每页一张）
            mime_type: 图片 MIME 类型
            prompt: 解析指令
        Returns:
            (markdown, error)
        """
        if not self.enabled:
            return None, "AI 服务未启用"
        if not images:
            return None, "无图片数据"

        if self.provider == "ollama":
            return self._call_ollama(images, mime_type, prompt, max_tokens)
        else:
            return self._call_openai(images, mime_type, prompt, max_tokens)

    def parse_text(
        self,
        text: str,
        prompt: str = DOC_PARSE_PROMPT,
        max_tokens: int = 8192,
    ) -> Tuple[Optional[str], Optional[str]]:
        """把纯文本喂给多模态模型，让其规整/抽取为 Markdown。

        阶段十三"全格式 AI 提取"：docx/xlsx/txt 等格式先读原始文本，
        再用本方法让 VLM 整理成规范 Markdown。不发图片，只发文本。
        返回 (markdown, error)，失败返回 (None, error)。
        """
        if not self.enabled:
            return None, "AI 服务未启用"
        if not text or not text.strip():
            return None, "输入文本为空"

        # 针对纯文本场景定制 prompt：模型已拿到原始内容，只需规整为 Markdown
        text_prompt = (
            "下面是从文档中提取的原始文本。请将其整理为规范的 Markdown，"
            "保留标题层级(#/##)、段落、列表与表格(用 | 分隔)。"
            "不要编造原始文本中没有的内容，不要输出任何解释性文字，只输出 Markdown 本身。\n\n"
            + text.strip()
        )

        if self.provider == "ollama":
            return self._call_ollama_text(text_prompt, max_tokens)
        return self._call_openai_text(text_prompt, max_tokens)

    def _call_ollama_text(self, text_prompt: str, max_tokens: int) -> Tuple[Optional[str], Optional[str]]:
        """Ollama 纯文本调用（content 为纯字符串）"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text_prompt}],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }
        try:
            r = requests.post(f"{self.url}/api/chat", json=payload, timeout=self.timeout)
            if r.status_code != 200:
                return None, f"Ollama 返回 {r.status_code}: {r.text[:200]}"
            data = r.json()
            text = data.get("message", {}).get("content", "")
            return (text.strip(), None) if text else (None, "Ollama 返回空 content")
        except requests.Timeout:
            return None, f"Ollama 超时（>{self.timeout}s）"
        except Exception as e:
            return None, f"Ollama 调用失败: {e}"

    def _call_openai_text(self, text_prompt: str, max_tokens: int) -> Tuple[Optional[str], Optional[str]]:
        """OpenAI 兼容纯文本调用"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text_prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            r = requests.post(
                f"{self.url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return None, f"OpenAI API 返回 {r.status_code}: {r.text[:200]}"
            data = r.json()
            choices = data.get("choices", [])
            if not choices:
                return None, "返回空 choices"
            text = choices[0].get("message", {}).get("content", "")
            return (text.strip(), None) if text else (None, "返回空 content")
        except requests.Timeout:
            return None, f"超时（>{self.timeout}s）"
        except Exception as e:
            return None, f"调用失败: {e}"

    def _call_ollama(
        self, images: List[bytes], mime_type: str, prompt: str, max_tokens: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Ollama API（POST /api/chat）"""
        # Ollama 支持多图：content 数组里多个 image 项
        content: List[Dict[str, Any]] = []
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime_type, "data": b64},
            })
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }

        try:
            r = requests.post(
                f"{self.url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return None, f"Ollama 返回 {r.status_code}: {r.text[:200]}"
            data = r.json()
            text = data.get("message", {}).get("content", "")
            return (text.strip(), None) if text else (None, "Ollama 返回空 content")
        except requests.Timeout:
            return None, f"Ollama 超时（>{self.timeout}s）"
        except Exception as e:
            return None, f"Ollama 调用失败: {e}"

    def _call_openai(
        self, images: List[bytes], mime_type: str, prompt: str, max_tokens: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """OpenAI 兼容 API（DashScope / OpenAI / vLLM）"""
        content: List[Dict[str, Any]] = []
        for img_bytes in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64}"
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            r = requests.post(
                f"{self.url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return None, f"OpenAI API 返回 {r.status_code}: {r.text[:200]}"
            data = r.json()
            choices = data.get("choices", [])
            if not choices:
                return None, "返回空 choices"
            text = choices[0].get("message", {}).get("content", "")
            return (text.strip(), None) if text else (None, "返回空 content")
        except requests.Timeout:
            return None, f"超时（>{self.timeout}s）"
        except Exception as e:
            return None, f"调用失败: {e}"


# 工厂
def get_unified_ai_client():
    from app.core.config import settings
    return UnifiedAIClient(
        url=settings.AI_SERVICE_URL,
        provider=settings.AI_SERVICE_PROVIDER,
        model=settings.AI_SERVICE_MODEL,
        timeout=settings.AI_SERVICE_TIMEOUT,
        enabled=settings.AI_SERVICE_ENABLED,
        api_key=settings.AI_SERVICE_API_KEY,
    )


def get_ocr_client():
    """保留旧 PaddleOCRClient（高速 CPU 兜底）"""
    from app.core.config import settings
    return PaddleOCRClient(
        url=settings.AI_OCR_SERVICE_URL,
        timeout=settings.AI_SERVICE_TIMEOUT,
        enabled=settings.AI_OCR_ENABLED,
    )