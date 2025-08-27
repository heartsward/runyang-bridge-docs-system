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
    
    def extract_text_from_image(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """从图片文件提取文本"""
        if not self.tesseract_available:
            return None, "OCR功能不可用：需要安装pytesseract和Tesseract"
        
        if not Image:
            return None, "需要Pillow库"
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return None, f"文件不存在: {file_path}"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            max_size_mb = 10  # 限制10MB
            
            if file_size > max_size_mb * 1024 * 1024:
                return None, f"图片文件过大: {size_mb:.2f}MB，超过{max_size_mb}MB限制"
            
            # 检查是否为图片文件
            if not self.is_image_file(file_path):
                return None, "不是支持的图片文件格式"
            
            logger.info(f"开始图片OCR处理: {file_path} ({size_mb:.2f}MB)")
            
            # 打开图片
            try:
                img = Image.open(file_path)
                
                # 如果是RGBA模式，转换为RGB
                if img.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if len(img.split()) == 4 else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 图像预处理以提高OCR准确性
                img = self._preprocess_image_for_ocr(img)
                
                # 执行OCR
                text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 3')
                
                if text and text.strip():
                    # 清理文本
                    cleaned_text = self._clean_ocr_text(text.strip())
                    logger.info(f"图片OCR成功，提取 {len(cleaned_text)} 字符")
                    return cleaned_text, None
                else:
                    return None, "OCR未能从图片中提取到文本"
                    
            except Exception as img_error:
                return None, f"图片处理失败: {str(img_error)}"
                
        except Exception as e:
            logger.error(f"图片OCR处理失败: {str(e)}")
            return None, f"OCR处理失败: {str(e)}"
    
    def _preprocess_image_for_ocr(self, img: 'Image.Image') -> 'Image.Image':
        """图像预处理以提高OCR准确性"""
        try:
            # 如果图像太小，放大2倍
            if img.width < 1000 or img.height < 1000:
                new_size = (img.width * 2, img.height * 2)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 转换为灰度图像可以提高OCR效果
            img = img.convert('L')
            
            # 可以添加更多预处理步骤，如降噪、二值化等
            # 但简单的灰度转换通常就足够了
            
            return img
        except Exception as e:
            logger.warning(f"图像预处理失败，使用原图: {e}")
            return img
    
    def _clean_ocr_text(self, text: str) -> str:
        """清理OCR提取的文本"""
        if not text:
            return ""
        
        # 按行分割
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 清理每行
            cleaned_line = line.strip()
            
            # 跳过空行
            if not cleaned_line:
                continue
            
            # 跳过只有符号或特殊字符的行
            if len(cleaned_line) == 1 and not cleaned_line.isalnum():
                continue
            
            # 保留有意义的行
            cleaned_lines.append(cleaned_line)
        
        # 重新组织文本
        result = '\n'.join(cleaned_lines)
        
        # 清理多余的空行
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        
        return result.strip()
    
    def is_image_file(self, file_path: str) -> bool:
        """检查是否为支持的图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        file_ext = Path(file_path).suffix.lower()
        return file_ext in image_extensions
    
    def can_extract_from_file(self, file_path: str) -> bool:
        """检查文件是否可以进行OCR提取"""
        if not self.tesseract_available:
            return False
        
        # 检查是否为PDF或图片文件
        file_ext = Path(file_path).suffix.lower()
        
        # PDF文件
        if file_ext == '.pdf':
            return True
        
        # 图片文件
        if self.is_image_file(file_path):
            return True
        
        return False
    
    def get_ocr_suggestion(self, file_path: str) -> str:
        """获取OCR处理建议"""
        if not os.path.exists(file_path):
            return "文件不存在"
        
        file_ext = Path(file_path).suffix.lower()
        
        # PDF文件
        if file_ext == '.pdf':
            if self.is_scanned_pdf(file_path):
                if self.tesseract_available:
                    return "这是扫描版PDF，建议使用OCR功能提取文本"
                else:
                    return "这是扫描版PDF，需要安装OCR库才能提取文本：pip install pytesseract"
            else:
                return "这不是扫描版PDF，应该可以直接提取文本"
        
        # 图片文件
        elif self.is_image_file(file_path):
            if self.tesseract_available:
                return "这是图片文件，可以使用OCR功能提取文本"
            else:
                return "这是图片文件，需要安装OCR库才能提取文本：pip install pytesseract"
        
        else:
            return "此文件类型不支持OCR处理"