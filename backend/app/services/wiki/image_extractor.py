"""
Wiki 图片提取器（阶段十八·18.1）

参考 OpenKB（VectifyAI/OpenKB）images.py 的 dict-mode 方案：
- 用 pymupdf page.get_text("dict") 按阅读顺序遍历 block
- type=1（image block）且宽高 >= 32px → 落盘 PNG
- dict-mode 能抓到矢量渲染图（get_images() 只拿嵌入位图，会漏图）
- 兜底：block 无 image 字节（纯矢量图）→ 用 get_pixmap(clip=bbox) 裁剪渲染
- 独立图片文档（png/jpg 上传）→ 原样拷贝保留扩展名

图片统一存：wiki/images/{doc_id}/{filename}
命名：PDF 内嵌 p{页码}_img{序号}.png；独立图片 img{序号}.{ext}
"""
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from .storage import WIKI_DIR

# 最小像素边长 —— 过滤图标、项目符号、噪点（照 OpenKB）
MIN_IMAGE_DIM = 32


def images_dir_for(doc_id: int) -> Path:
    """某文档的图片目录：wiki/images/{doc_id}/"""
    d = WIKI_DIR / "images" / str(doc_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def extract_pdf_images(pdf_path, doc_id: int) -> List[Dict[str, Any]]:
    """从 PDF 提取图片（按阅读顺序），落盘到 wiki/images/{doc_id}/

    Returns:
        [{"page": 1, "file": "p1_img1.png", "rel_path": "images/1/p1_img1.png",
          "size": 12345, "w": 800, "h": 600}, ...]
        失败返回 []（不抛异常，不影响主流程）
    """
    pdf_path = Path(pdf_path)
    if not PYMUPDF_AVAILABLE:
        logger.warning("pymupdf 未安装，跳过图片提取")
        return []
    if not pdf_path.exists():
        logger.warning(f"PDF 不存在，跳过图片提取: {pdf_path}")
        return []

    out_dir = images_dir_for(doc_id)
    results: List[Dict[str, Any]] = []
    img_counter = 0

    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as e:
        logger.warning(f"打开 PDF 失败，跳过图片提取: {e}")
        return []

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1

            try:
                blocks = page.get_text("dict").get("blocks", [])
            except Exception as e:
                logger.warning(f"第 {page_num} 页 dict 解析失败: {e}")
                continue

            for block in blocks:
                if block.get("type") != 1:
                    continue  # 非图片块

                w = block.get("width", 0)
                h = block.get("height", 0)
                if w < MIN_IMAGE_DIM or h < MIN_IMAGE_DIM:
                    continue

                img_bytes = block.get("image")
                try:
                    if img_bytes:
                        # 嵌入位图：直接 Pixmap
                        try:
                            pix = pymupdf.Pixmap(img_bytes)
                            if pix.n - pix.alpha > 3:  # CMYK 等 → 转 RGB
                                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                            png_bytes = pix.tobytes("png")
                        except Exception:
                            # 位图解码失败 → 走裁剪渲染兜底
                            png_bytes = _render_block_clip(page, block)
                    else:
                        # 纯矢量图（无嵌入字节）→ 裁剪渲染兜底
                        png_bytes = _render_block_clip(page, block)

                    if not png_bytes:
                        continue

                    img_counter += 1
                    filename = f"p{page_num}_img{img_counter}.png"
                    (out_dir / filename).write_bytes(png_bytes)
                    rel_path = f"images/{doc_id}/{filename}"
                    results.append({
                        "page": page_num,
                        "file": filename,
                        "rel_path": rel_path,
                        "size": len(png_bytes),
                        "w": int(w),
                        "h": int(h),
                    })
                except Exception as e:
                    logger.warning(f"第 {page_num} 页图片落盘失败: {e}")
                    continue
    except Exception as e:
        logger.exception(f"PDF 图片提取异常: {e}")
    finally:
        try:
            doc.close()
        except Exception:
            pass

    logger.info(f"PDF 图片提取完成: {pdf_path.name} → {len(results)} 张 (doc_id={doc_id})")
    return results


def _render_block_clip(page, block: Dict[str, Any]) -> bytes:
    """兜底：按 block bbox 裁剪渲染（纯矢量图 / 位图解码失败时用）"""
    try:
        bbox = pymupdf.Rect(block.get("bbox") or block.get("rect"))
        if bbox.is_empty or bbox.is_infinite:
            return b""
        # 2x 分辨率保证清晰度
        mat = pymupdf.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, clip=bbox, alpha=False)
        return pix.tobytes("png")
    except Exception as e:
        logger.warning(f"裁剪渲染失败: {e}")
        return b""


IMAGE_DOC_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tiff", ".tif"}

# 阶段十八·18.9 修复：图片扩展名 → MIME（此前 f"image{suffix}" 拼成 image.png 导致 AI 400）
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


def image_mime(suffix: str, default: str = "image/png") -> str:
    """扩展名 → 图片 MIME 类型"""
    return IMAGE_MIME.get((suffix or "").lower(), default)


def register_image_doc(doc_id: int, source_path) -> List[Dict[str, Any]]:
    """独立图片文档登记：原样拷贝到 wiki/images/{doc_id}/（保留扩展名）

    Returns:
        [{"page": 0, "file": "img1.png", "rel_path": "images/77/img1.png",
          "size": 12345}, ...]
    """
    source_path = Path(source_path)
    if not source_path.exists():
        logger.warning(f"图片文件不存在: {source_path}")
        return []

    ext = source_path.suffix.lower()
    if ext not in IMAGE_DOC_EXTENSIONS:
        logger.warning(f"非图片扩展名，跳过登记: {ext}")
        return []

    out_dir = images_dir_for(doc_id)
    filename = f"img1{ext}"
    dest = out_dir / filename
    try:
        shutil.copy2(source_path, dest)
    except Exception as e:
        logger.warning(f"图片拷贝失败: {e}")
        return []

    return [{
        "page": 0,
        "file": filename,
        "rel_path": f"images/{doc_id}/{filename}",
        "size": dest.stat().st_size,
    }]


# 阶段二十三·23.1：删除 insert_image_refs（图片引用不再插入 Markdown）。
# 落盘 + wiki_images 登记 + AI 描述仍由 extract_pdf_images / register_image_doc / describe_image_sync 提供。


def describe_image_sync(image_path, fallback_caption: str = "") -> str:
    """同步版图片描述（供非 async 上下文使用）；失败回退 fallback_caption"""
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
        client = get_unified_ai_client()
        if not client.is_enabled():
            return fallback

        mime = image_mime(p.suffix)
        # max_tokens=2048：thinking 模型需预留 reasoning token，128 会导致 content 为空
        text, error = client.describe_image(p.read_bytes(), mime_type=mime, max_tokens=2048)
        if not text:
            logger.warning(f"图片描述失败: {error}")
            return fallback

        caption = text.strip().strip('"\'`').replace("\n", " ").strip()
        for prefix in ("描述：", "描述:", "图片描述：", "图片描述:"):
            if caption.startswith(prefix):
                caption = caption[len(prefix):].strip()
        return caption[:80] or fallback
    except Exception as e:
        logger.warning(f"图片描述异常 {p.name}: {e}")
        return fallback


def list_doc_images(doc_id: int) -> List[Dict[str, Any]]:
    """列出某文档已落盘的图片文件"""
    d = WIKI_DIR / "images" / str(doc_id)
    if not d.exists():
        return []
    files = sorted(f for f in d.iterdir() if f.is_file())
    return [
        {
            "file": f.name,
            "rel_path": f"images/{doc_id}/{f.name}",
            "size": f.stat().st_size,
        }
        for f in files
    ]
