# -*- coding: utf-8 -*-
"""
OCR文本提取器 - 处理扫描版PDF和图像
"""
import os
import io
import logging
from typing import Optional, Tuple
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger(__name__)


# Tesseract路径配置
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    print("Tesseract路径已配置")
except ImportError:
    print("pytesseract未安装")

class OCRExtractor:
    """OCR文本提取器"""
    
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
        
    def _check_tesseract(self) -> bool:
        """检查Tesseract是否可用"""
        if not pytesseract:
            logger.warning("pytesseract未安装")
            return False
            
        try:
            # 测试Tesseract
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR可用")
            return True
        except Exception as e:
            logger.warning(f"Tesseract不可用: {e}")
            return False
    
    def is_scanned_pdf(self, file_path: str) -> bool:
        """检查是否为扫描版PDF"""
        if not fitz:
            return False
            
        try:
            doc = fitz.open(file_path)
            
            # 检查前3页
            scanned_pages = 0
            total_checked = min(3, len(doc))
            
            for page_num in range(total_checked):
                page = doc.load_page(page_num)
                
                # 检查文本内容
                text = page.get_text().strip()
                
                # 检查图像数量
                images = page.get_images()
                
                # 如果页面几乎没有文本但有大图像，可能是扫描版
                if len(text) < 50 and len(images) > 0:
                    scanned_pages += 1
            
            doc.close()
            
            # 如果大部分页面都像扫描版，则认定为扫描版
            is_scanned = scanned_pages >= total_checked * 0.8
            
            if is_scanned:
                logger.info(f"检测到扫描版PDF: {file_path}")
            
            return is_scanned
            
        except Exception as e:
            logger.error(f"检查扫描版PDF失败: {e}")
            return False
    
    def extract_text_from_scanned_pdf(self, file_path: str, max_pages: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """从扫描版PDF提取文本"""
        if not self.tesseract_available:
            return None, "OCR功能不可用：需要安装pytesseract和Tesseract"
        
        if not fitz:
            return None, "需要PyMuPDF库"
        
        try:
            doc = fitz.open(file_path)
            extracted_texts = []
            
            page_count = min(len(doc), max_pages)
            logger.info(f"开始OCR处理，页数: {page_count}")
            
            for page_num in range(page_count):
                try:
                    page = doc.load_page(page_num)
                    
                    # 将页面转为图像
                    mat = fitz.Matrix(2.0, 2.0)  # 提高分辨率
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # 使用PIL处理图像
                    if Image:
                        img = Image.open(io.BytesIO(img_data))
                        
                        # OCR提取文本
                        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                        
                        if text.strip():
                            extracted_texts.append(f"[页面 {page_num + 1}]\n{text.strip()}\n")
                            logger.info(f"页面 {page_num + 1} OCR成功，提取 {len(text)} 字符")
                        else:
                            logger.warning(f"页面 {page_num + 1} OCR未提取到文本")
                            
                except Exception as e:
                    logger.error(f"页面 {page_num + 1} OCR失败: {e}")
                    continue
            
            doc.close()
            
            if extracted_texts:
                full_text = "\n".join(extracted_texts)
                return full_text, None
            else:
                return None, "OCR未能提取到任何文本"
                
        except Exception as e:
            return None, f"OCR处理失败: {str(e)}"
    
    def get_ocr_suggestion(self, file_path: str) -> str:
        """获取OCR处理建议"""
        if self.is_scanned_pdf(file_path):
            if self.tesseract_available:
                return "这是扫描版PDF，建议使用OCR功能提取文本"
            else:
                return "这是扫描版PDF，需要安装OCR库才能提取文本：pip install pytesseract"
        else:
            return "这不是扫描版PDF，应该可以直接提取文本"