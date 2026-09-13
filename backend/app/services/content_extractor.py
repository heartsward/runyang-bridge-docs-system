# -*- coding: utf-8 -*-
"""
文档内容提取服务
支持多种文件格式的内容提取并存储到数据库
"""
import os
import logging
from typing import Optional, Tuple
from pathlib import Path

# 导入现有的搜索服务来复用文件读取逻辑
from app.services.search_service import SearchService
from app.services.wiki.storage import WikiStorage, sanitize_title

from app.services.ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)

class ContentExtractor:
    """文档内容提取器"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.ocr_extractor = OCRExtractor()
        self.wiki_storage = WikiStorage()

    async def extract_content_async(
        self,
        file_path: str,
        doc_id: Optional[int] = None,
        source_filename: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        异步版：提取后立即保存 MD 副本到 wiki 目录

        Returns:
            (markdown, error)
        """
        # 先调用同步的提取
        result = self.extract_content(file_path)
        # result 是 (content, error) 元组
        markdown, error = result

        # 保存到 wiki（如有 doc_id）
        # 阶段十八：若内嵌了图片引用，最终返回的 markdown 也带引用，
        # 这样 documents.content（前端预览数据源）也能渲染图片
        final_markdown = markdown
        if markdown and doc_id is not None:
            try:
                from .wiki import generate_metadata_via_ai, derive_fallback_tags
                from .wiki.index import WikiIndex
                from .wiki import image_extractor as wiki_images
                from .wiki.image_extractor import (
                    extract_pdf_images, register_image_doc,
                    insert_image_refs, describe_image_sync,
                )

                filename = source_filename or Path(file_path).name
                fallback_title = sanitize_title(filename)
                ext = Path(file_path).suffix.lower()

                # 调 AI 生成 title/tags/category
                meta = await generate_metadata_via_ai(
                    content_sample=markdown[:2000],
                    fallback_title=fallback_title,
                    fallback_tags=derive_fallback_tags(filename, markdown),
                )

                title = (meta or {}).get("title") or fallback_title
                tags = (meta or {}).get("tags") or []
                category = (meta or {}).get("doc_category") or "其他"

                # 阶段十八·18.3：图片提取 + 描述 + MD 内嵌引用
                idx = WikiIndex()
                if ext == ".pdf":
                    try:
                        images = extract_pdf_images(file_path, doc_id)
                        for n, img in enumerate(images, 1):
                            img_file = wiki_images.WIKI_DIR / "images" / str(doc_id) / img["file"]
                            caption = describe_image_sync(
                                img_file, fallback_caption=f"第{img['page']}页图{n}"
                            )
                            img["caption"] = caption
                            idx.add_image(
                                doc_id, img["file"], page=img["page"],
                                caption=caption, rel_path=img["rel_path"],
                                size=img.get("size", 0),
                            )
                        if images:
                            markdown = insert_image_refs(markdown, images)
                            logger.info(f"doc {doc_id}: MD 内嵌 {len(images)} 张图引用")
                    except Exception as e:
                        logger.exception(f"PDF 图片提取失败 (doc_id={doc_id}): {e}")
                elif ext in wiki_images.IMAGE_DOC_EXTENSIONS:
                    try:
                        images = register_image_doc(doc_id, file_path)
                        for img in images:
                            img_file = wiki_images.WIKI_DIR / "images" / str(doc_id) / img["file"]
                            caption = describe_image_sync(
                                img_file, fallback_caption=fallback_title
                            )
                            idx.add_image(
                                doc_id, img["file"], page=img.get("page", 0),
                                caption=caption, rel_path=img["rel_path"],
                                size=img.get("size", 0),
                            )
                        # 独立图片文档：MD 正文 = 图引用 + 描述
                        if images:
                            img_block = "\n".join(
                                f"<!-- wiki-img -->\n![{i.get('caption', '图片')}]({i['rel_path']})"
                                for i in images
                            )
                            markdown = f"{markdown.strip()}\n\n{img_block}\n" if markdown.strip() else img_block + "\n"
                    except Exception as e:
                        logger.exception(f"图片文档登记失败 (doc_id={doc_id}): {e}")

                md_path = self.wiki_storage.write(
                    doc_id=doc_id,
                    title=title,
                    source_file=filename,
                    doc_type=doc_type or Path(file_path).suffix.lstrip(".").lower() or "unknown",
                    tags=tags,
                    markdown_body=markdown,
                    doc_category=category,
                )

                # 阶段十·W2：写入后立即建索引
                try:
                    idx.index_doc(doc_id, str(md_path))
                except Exception as e:
                    logger.exception(f"建索引失败 (doc_id={doc_id}): {e}")

                # 阶段十八：内嵌图引用后的 markdown 也作为最终提取内容返回
                final_markdown = markdown
            except Exception as e:
                logger.exception(f"保存 MD 副本失败 (doc_id={doc_id}): {e}")
                # 不影响主流程

        # result 是 (markdown, error) 元组；若内嵌了图引用，返回带引用的版本
        if final_markdown and result and final_markdown != result[0]:
            return (final_markdown, result[1])
        return result

    def extract_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取文档内容

        阶段四：只走新路由器（app.services.extraction.ExtractionRouter）。
        旧 LibreOffice 管线已删除；新路由器失败时直接返回错误。

        Args:
            file_path: 文件路径

        Returns:
            Tuple[content, error]: (提取的内容, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return None, f"文件不存在: {file_path}"

            # 获取文件大小
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)

            # 限制文件大小（避免处理过大的文件）
            max_size_mb = 50  # 最大50MB
            if file_size > max_size_mb * 1024 * 1024:
                return None, f"文件过大: {size_mb:.2f}MB，超过{max_size_mb}MB限制"

            logger.info(f"开始提取文件内容: {file_path} ({size_mb:.2f}MB)")

            # 新路由器
            try:
                from app.services.extraction import ExtractionRouter
                router = ExtractionRouter()
                result = router.extract(file_path)

                if result.is_success:
                    markdown = result.markdown

                    # 写入结构化 JSON 备用（AI Wiki 等）
                    if result.json_data:
                        try:
                            import json as _json
                            json_path = file_path + ".json"
                            with open(json_path, "w", encoding="utf-8") as f:
                                _json.dump(result.json_data, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass

                    markdown = self._clean_markdown(markdown)

                    logger.info(
                        f"内容提取成功 (format={result.json_data.get('format')}): "
                        f"{file_path}, 长度: {len(markdown)}"
                    )
                    return markdown, None

                # 阶段四：不再 fallback 到旧管线，直接报错
                logger.warning(f"提取失败: {result.error} | file={file_path}")
                return None, result.error or "无法提取文件内容"

            except Exception as e:
                logger.exception(f"提取异常: {file_path}")
                return None, f"内容提取异常: {str(e)}"

        except Exception as e:
            error_msg = f"内容提取失败: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
            return None, error_msg

    @staticmethod
    def _clean_markdown(content: str) -> str:
        """清理 Markdown 文本"""
        if not isinstance(content, str):
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = content.decode('gbk')
                    except UnicodeDecodeError:
                        content = content.decode('utf-8', errors='ignore')

        content = content.replace('\x00', '')
        content = ''.join(ch for ch in content if ord(ch) >= 32 or ch in '\t\n\r')

        max_content_length = 1000000  # 1MB
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[内容过长，已截断...]"
        return content
    
    
    def get_extraction_methods(self) -> dict:
        """
        获取可用的提取方法信息
        
        Returns:
            dict: 提取方法状态
        """
        return {
            "libreoffice": True,  # LibreOffice通过搜索服务提供
            "ocr": self.ocr_extractor.tesseract_available,
            "search_service": True  # 搜索服务总是可用
        }
    
    def _is_image_file(self, file_ext: str) -> bool:
        """检查文件扩展名是否为图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'}
        return file_ext.lower() in image_extensions
    
    def _extract_image_with_ocr(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        使用OCR提取图片文件中的文本
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            Tuple[content, error]: (提取的内容, 错误信息)
        """
        if not self.ocr_extractor.tesseract_available:
            return None, "OCR功能不可用，需要安装Tesseract"
        
        try:
            logger.info(f"尝试使用OCR提取图片内容: {file_path}")
            content, error = self.ocr_extractor.extract_text_from_image(file_path)
            
            if content and content.strip():
                logger.info(f"图片OCR成功提取内容，长度: {len(content)}")
                return content, None
            else:
                return None, error or "OCR未能从图片中提取到文本内容"
                
        except Exception as e:
            error_msg = f"图片OCR提取异常: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否支持内容提取
        """
        if not os.path.exists(file_path):
            return False
            
        file_ext = Path(file_path).suffix.lower()
        
        # 支持的文件格式
        supported_formats = {
            '.txt', '.md', '.csv', '.json', '.xml', '.log',
            '.py', '.js', '.html', '.css', '.sql', '.yml', '.yaml',
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            # 添加图片格式支持（OCR识别）
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'
        }
        
        return file_ext in supported_formats
        
    def get_content_preview(self, content: str, max_length: int = 500) -> str:
        """
        获取内容预览
        """
        if not content:
            return ""
            
        if len(content) <= max_length:
            return content
            
        return content[:max_length] + "..."