# -*- coding: utf-8 -*-
"""
增强的文档内容提取服务
支持多种提取方法包括OCR
"""
import os
import logging
import tempfile
import time
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

# 导入现有的搜索服务来复用文件读取逻辑
from app.services.search_service import SearchService
from app.services.enhanced_pdf_extractor import EnhancedPDFExtractor
from app.services.advanced_pdf_extractor import AdvancedPDFExtractor
from app.services.image_preprocessor import ImagePreprocessor
from app.services.smart_text_processor import SmartTextProcessor
from app.services.content_quality_validator import ContentQualityValidator

# OCR相关导入
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    pytesseract = None
    Image = None
    HAS_TESSERACT = False

# PDF转图像工具
try:
    import pdf2image
    HAS_PDF2IMAGE = True
except ImportError:
    pdf2image = None
    HAS_PDF2IMAGE = False

# PyMuPDF作为备选方案
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    fitz = None
    HAS_PYMUPDF = False

# OCR功能需要tesseract和至少一种PDF处理工具
HAS_OCR = HAS_TESSERACT and (HAS_PDF2IMAGE or HAS_PYMUPDF)

logger = logging.getLogger(__name__)

class EnhancedContentExtractor:
    """增强的文档内容提取器 - 支持OCR"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.pdf_extractor = EnhancedPDFExtractor()
        self.advanced_pdf_extractor = AdvancedPDFExtractor()  # 新增高性能PDF提取器
        self.image_preprocessor = ImagePreprocessor()  # 图像预处理器
        
        # 性能监控
        self.performance_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "ocr_processing_time": 0.0,
            "preprocessing_time": 0.0
        }
        
        # 智能回退配置
        self.fallback_config = {
            "enable_smart_fallback": True,
            "max_processing_time": 60.0,  # 超过60秒触发回退
            "max_failure_rate": 30.0,     # 失败率超过30%触发回退
            "use_simple_mode": False,     # 是否启用简单模式
            "consecutive_failures": 0,    # 连续失败次数
            "max_consecutive_failures": 3 # 连续失败3次后启用简单模式
        }
        self.text_processor = SmartTextProcessor()  # 智能文本处理器
        self.quality_validator = ContentQualityValidator()  # 内容质量验证器
        
        # 配置OCR
        self.has_ocr = HAS_OCR
        if self.has_ocr:
            # 尝试设置tesseract路径（Windows系统常见路径）
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe", 
                r"C:\Users\cccly\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
                r"C:\tesseract\tesseract.exe",
                r"C:\tools\tesseract\tesseract.exe",
                "tesseract"  # 系统PATH中
            ]
            
            tesseract_found = False
            for path in possible_paths:
                if path == "tesseract" or os.path.exists(path):
                    try:
                        pytesseract.pytesseract.tesseract_cmd = path
                        # 修复Tesseract配置，使用更安全的测试配置
                        test_img = Image.new('RGB', (100, 30), color=(255, 255, 255))
                        test_result = pytesseract.image_to_string(
                            test_img, 
                            config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABC'
                        )
                        logger.info(f"✅ OCR功能已启用，使用路径: {path}")
                        tesseract_found = True
                        break
                    except Exception as e:
                        logger.debug(f"OCR路径 {path} 测试失败: {e}")
                        continue
            
            if not tesseract_found:
                logger.warning("⚠️ 未找到可用的Tesseract OCR，OCR功能将不可用")
                logger.info("请确保Tesseract已安装并添加到系统PATH，或安装到常见路径")
                self.has_ocr = False
        else:
            logger.warning("缺少OCR依赖包，请安装: pip install pytesseract pillow pdf2image")
        
    def extract_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取文档内容 - 增强版本
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[content, error]: (提取的内容, 错误信息)
        """
        start_time = time.time()
        self.performance_stats["total_extractions"] += 1
        
        # 检查是否需要启用智能回退
        should_use_simple_mode = self._should_use_simple_mode()
        if should_use_simple_mode:
            logger.info(f"启用简单模式处理文档: {file_path}")
        
        try:
            if not os.path.exists(file_path):
                self.performance_stats["failed_extractions"] += 1
                return None, f"文件不存在: {file_path}"
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            # 限制文件大小（避免处理过大的文件）
            max_size_mb = 100  # 增加到100MB支持更大文件
            if file_size > max_size_mb * 1024 * 1024:
                return None, f"文件过大: {size_mb:.2f}MB，超过{max_size_mb}MB限制"
            
            logger.info(f"开始提取文件内容: {file_path} ({size_mb:.2f}MB)")
            
            # 检查文件类型
            file_ext = Path(file_path).suffix.lower()
            
            # 多种提取方法
            content = None
            error = None
            
            # 方法1: 简单直接的PDF文本提取
            if file_ext == '.pdf':
                content, error = self._extract_pdf_content_simple(file_path)
                logger.info(f"PDF标准提取结果: {'成功' if content else '失败'}, 内容长度: {len(content) if content else 0}")
            else:
                # 其他文件类型使用原有的搜索服务
                content = self.search_service.extract_file_content(file_path)
            
            # 方法2: 如果标准提取失败或内容无效，尝试OCR
            # 检查内容是否主要包含占位符文本或OCR提示
            content_is_placeholder = content and (
                "(无可提取文本)" in content or 
                "无可提取文本" in content or
                "(无文本内容)" in content or
                "需要OCR处理" in content or
                "扫描内容或图像" in content or
                "扫描页面" in content
            )
            # 检查内容长度，排除提示文本后的实际内容长度
            actual_content_length = 0
            if content:
                # 移除提示性文本，计算实际内容长度
                clean_content = content
                for placeholder in ["需要OCR处理", "扫描内容或图像", "扫描页面", "(无可提取文本)", "无可提取文本", "(无文本内容)"]:
                    clean_content = clean_content.replace(placeholder, "")
                # 移除页面标记
                import re
                clean_content = re.sub(r'\[页面 \d+[^\]]*\]', '', clean_content)
                clean_content = re.sub(r'\[第\d+页[^\]]*\]', '', clean_content)
                actual_content_length = len(clean_content.strip())
            
            content_too_short = actual_content_length < 50
            
            # 检查是否是乱码内容
            content_is_garbled = content and self._is_garbled_text(content)
            if content_is_garbled:
                logger.info(f"检测到乱码内容，将尝试备用方案: {file_path}")
            
            # 方法2: 如果标准提取失败，先尝试LibreOffice（比OCR更快更准确）
            if (content_too_short or content_is_placeholder or content_is_garbled) and file_ext == '.pdf':
                logger.info(f"标准PDF提取不理想，尝试LibreOffice转换: {file_path}")
                
                # 尝试LibreOffice提取
                libreoffice_content, libreoffice_error = self.pdf_extractor._extract_with_libreoffice(file_path)
                
                if libreoffice_content and len(libreoffice_content.strip()) > 100:
                    logger.info(f"LibreOffice PDF提取成功，内容长度: {len(libreoffice_content)}")
                    content = libreoffice_content
                    error = None
                    # 重新检查是否还是乱码
                    content_is_garbled = self._is_garbled_text(content)
                elif libreoffice_error:
                    logger.warning(f"LibreOffice PDF提取失败: {libreoffice_error}")
            
            # 方法3: 如果LibreOffice也失败或仍是乱码，最后尝试OCR
            if (content_too_short or content_is_placeholder or content_is_garbled) and self.has_ocr:
                reason = "未知原因"
                if content_is_garbled:
                    reason = "检测到乱码内容"
                elif content_is_placeholder:
                    reason = "内容为占位符"
                elif content_too_short:
                    reason = "内容太短或为空"
                    
                logger.info(f"尝试OCR提取: {file_path} (原因: {reason})")
                ocr_content, ocr_error = self._extract_with_ocr(file_path)
                
                if ocr_content and len(ocr_content.strip()) > 100:  # OCR内容要足够长才替换
                    content = ocr_content
                    error = None
                    logger.info(f"OCR提取成功，内容长度: {len(ocr_content)}")
                elif ocr_error:
                    logger.warning(f"OCR提取失败: {ocr_error}")
            
            if content:
                # 智能文本处理和清理
                content = self._process_and_clean_content(content, file_path)
                
                if len(content.strip()) > 0:
                    self.performance_stats["successful_extractions"] += 1
                    logger.info(f"内容提取成功: {file_path}, 最终内容长度: {len(content)}")
                    return content, None
                else:
                    return None, "提取的内容为空"
            else:
                self.performance_stats["failed_extractions"] += 1
                return None, error or "无法提取文件内容"
                
        except Exception as e:
            error_msg = f"内容提取失败: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
            self.performance_stats["failed_extractions"] += 1
            self.fallback_config["consecutive_failures"] += 1
            return None, error_msg
        finally:
            # 更新性能统计
            processing_time = time.time() - start_time
            self.performance_stats["total_processing_time"] += processing_time
            if self.performance_stats["total_extractions"] > 0:
                self.performance_stats["average_processing_time"] = (
                    self.performance_stats["total_processing_time"] / 
                    self.performance_stats["total_extractions"]
                )
            
            # 检查是否触发智能回退
            self._update_fallback_status(processing_time, content is not None)
            
            # 记录性能日志
            if processing_time > 30:  # 超过30秒的处理记录警告
                logger.warning(f"文档处理耗时过长: {processing_time:.2f}s - {file_path}")
            else:
                logger.info(f"文档处理完成: {processing_time:.2f}s - {file_path}")
    
    def _extract_pdf_content_simple(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        简单直接的PDF内容提取
        优先使用文本提取，必要时使用OCR
        """
        try:
            # 添加详细的文件诊断信息
            file_size = os.path.getsize(file_path)
            logger.info(f"PDF文件诊断: {file_path}, 大小: {file_size} bytes")
            
            if file_size == 0:
                return None, "PDF文件为空"
            elif file_size > 100 * 1024 * 1024:  # 100MB
                logger.warning(f"PDF文件过大: {file_size / 1024 / 1024:.1f}MB")
            
            # 首先尝试文本提取
            content, error = self.pdf_extractor.extract_pdf_content(file_path)
            
            # 详细诊断提取结果
            if content:
                content_length = len(content.strip())
                logger.info(f"PDF标准提取: 成功, 内容长度: {content_length}, 错误: {error or '无'}")
                
                if content_length > 50:
                    return content, None
                else:
                    logger.info(f"PDF内容过短({content_length}字符)，可能需要其他方法")
            else:
                logger.warning(f"PDF标准提取: 失败, 错误: {error}")
                
            # 如果文本提取无效果，且支持OCR，则进行OCR
            if self.has_ocr:
                logger.info(f"PDF标准提取效果不佳，准备OCR处理: {file_path}")
                return self._ocr_pdf_simple(file_path)
            else:
                final_error = error or "PDF标准提取失败"
                logger.warning(f"PDF提取最终失败: {final_error}, OCR不可用")
                return content, f"{final_error}，且OCR不可用"
                
        except Exception as e:
            logger.error(f"PDF内容提取异常: {str(e)}, 文件: {file_path}")
            return None, f"PDF内容提取失败: {str(e)}"
    
    def _ocr_pdf_simple(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        简单直接的PDF OCR处理
        不使用图像预处理，使用最基本的OCR配置
        """
        doc = None
        try:
            doc = fitz.open(file_path)
            if not doc:
                return None, f"无法打开PDF文件: {file_path}"
            
            extracted_text = []
            
            # 动态调整页面处理限制（简单OCR模式 - 更保守的策略）
            if doc.page_count <= 15:
                max_pages = doc.page_count  # 小文档完全处理
            elif doc.page_count <= 30:
                max_pages = min(20, doc.page_count)  # 中等文档
            else:
                max_pages = 25  # 大文档保守处理
                logger.info(f"大型PDF文档({doc.page_count}页)，简单模式处理前{max_pages}页")
            
            for page_num in range(max_pages):
                logger.info(f"OCR处理PDF第{page_num+1}页")
                
                page = doc[page_num]
                
                # 使用固定的适中缩放
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img_data = pix.tobytes('png')
                
                # 直接进行OCR，不做任何预处理
                pil_image = Image.open(io.BytesIO(img_data))
                
                try:
                    # 使用优化的中文OCR配置
                    page_text = pytesseract.image_to_string(
                        pil_image,
                        lang='chi_sim+eng',
                        config='--psm 4 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1'
                    )
                    
                    if page_text and page_text.strip():
                        extracted_text.append(f"[第{page_num+1}页]\n{page_text.strip()}\n")
                        
                except Exception as ocr_error:
                    logger.warning(f"OCR处理第{page_num+1}页失败: {ocr_error}")
                    extracted_text.append(f"[第{page_num+1}页]\n(OCR处理失败)\n")
            
            if doc:
                doc.close()
                doc = None
            
            if extracted_text:
                full_text = "\n".join(extracted_text)
                
                # 添加详细的处理统计日志
                total_chars = len(full_text)
                pages_processed = len(extracted_text)
                logger.info(f"✅ 简单OCR处理完成 - 处理页数: {pages_processed}/{doc.page_count}, 提取字符: {total_chars}个")
                
                # 中文识别质量评估
                chinese_chars = len([c for c in full_text if '\u4e00' <= c <= '\u9fff'])
                if chinese_chars > 0:
                    chinese_ratio = chinese_chars / total_chars * 100
                    logger.info(f"   中文字符识别: {chinese_chars}个 ({chinese_ratio:.1f}%)")
                
                # 内容预览（调试用）
                preview = full_text.replace('\n', ' ').strip()[:100] + "..." if len(full_text) > 100 else full_text
                logger.debug(f"   内容预览: {preview}")
                
                return full_text, None
            else:
                logger.warning(f"⚠️ 简单OCR未提取到文本 - 处理了{max_pages}/{doc.page_count}页")
                return None, "简单OCR未提取到任何文本"
                
        except Exception as e:
            if doc:
                try:
                    doc.close()
                except:
                    pass
            logger.error(f"❌ 简单OCR处理失败: {str(e)}")
            return None, f"简单OCR处理失败: {str(e)}"
    
    def _extract_pdf_content_advanced(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用高级PDF提取器提取内容"""
        try:
            # 优先使用高性能的AdvancedPDFExtractor
            content, error = self.advanced_pdf_extractor.extract_pdf_content(file_path)
            
            if content and len(content.strip()) > 50:
                return content, error
            else:
                logger.warning(f"高级PDF提取器结果不理想，回退到原有提取器: {error}")
                # 回退到原有的PDF提取器
                return self.pdf_extractor.extract_pdf_content(file_path)
                
        except Exception as e:
            logger.warning(f"高级PDF提取器出错，回退到原有提取器: {e}")
            return self.pdf_extractor.extract_pdf_content(file_path)
    
    def _extract_pdf_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """提取PDF内容（原有方法，保持兼容性）"""
        return self.pdf_extractor.extract_pdf_content(file_path)
    
    def _extract_with_ocr(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用OCR提取内容"""
        if not self.has_ocr:
            return None, "OCR功能不可用"
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                return self._ocr_pdf(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return self._ocr_image(file_path)
            else:
                return None, f"不支持OCR的文件类型: {file_ext}"
                
        except Exception as e:
            return None, f"OCR处理失败: {str(e)}"
    
    def _ocr_pdf(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """对PDF文件进行OCR"""
        try:
            # 优先使用PyMuPDF，因为它不需要poppler
            if HAS_PYMUPDF:
                content, error = self._ocr_pdf_with_pymupdf(file_path)
                if content:
                    return content, error
                else:
                    logger.warning(f"PyMuPDF OCR失败: {error}, 尝试pdf2image备用方案")
                    
            # 如果PyMuPDF失败，尝试pdf2image
            if HAS_PDF2IMAGE:
                return self._ocr_pdf_with_pdf2image(file_path)
            else:
                return None, "没有可用的PDF处理工具"
                
        except Exception as e:
            return None, f"PDF OCR失败: {str(e)}"
    
    def _ocr_pdf_with_pymupdf(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用PyMuPDF进行PDF OCR - 集成图像预处理"""
        doc = None
        try:
            import io
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return None, f"PDF文件不存在: {file_path}"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return None, f"PDF文件为空: {file_path}"
            
            logger.info(f"尝试打开PDF文件: {file_path} (大小: {file_size} bytes)")
            
            doc = fitz.open(file_path)
            if not doc:
                return None, f"PyMuPDF无法打开PDF文件: {file_path}"
            
            logger.info(f"PDF文件打开成功，页数: {doc.page_count}")
            
            extracted_text = []
            
            # 智能页面处理策略（完整OCR模式 - 更积极的处理）
            if doc.page_count <= 20:
                max_pages = doc.page_count  # 小文档完全处理
            elif doc.page_count <= 50:
                max_pages = min(40, doc.page_count)  # 中等文档处理更多页面
            else:
                max_pages = 60  # 大文档允许处理更多页面
                logger.info(f"大型PDF文档({doc.page_count}页)，完整模式处理前{max_pages}页")
            
            logger.info(f"开始OCR处理，共{max_pages}页（总{doc.page_count}页），使用图像预处理")
            
            for page_num in range(max_pages):
                logger.info(f"OCR处理PDF第{page_num+1}页")
                
                page = doc[page_num]
                
                # 使用固定的适中缩放提高OCR效果
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 固定2x缩放
                img_data = pix.tobytes('png')
                
                # 直接使用原始图像进行OCR
                pil_image = Image.open(io.BytesIO(img_data))
                
                # 进行OCR - 使用简单有效的配置
                try:
                    # 使用专门针对中文文档优化的OCR配置
                    page_text = pytesseract.image_to_string(
                        pil_image,
                        lang='chi_sim+eng',
                        config='--psm 4 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1 -c textord_min_linesize=2.5'
                    )
                except Exception as ocr_error:
                    logger.warning(f"OCR处理第{page_num+1}页失败: {ocr_error}")
                    
                    # 尝试使用备用配置
                    page_text = self._retry_ocr_with_different_config(pil_image)
                    if not page_text:
                        page_text = f"(OCR处理失败: {str(ocr_error)[:100]})"
                
                if page_text.strip():
                    cleaned_text = self._post_process_ocr_text(page_text)
                    extracted_text.append(f"[第{page_num+1}页]\n{cleaned_text}\n")
                else:
                    # 如果OCR失败，尝试不同的配置
                    backup_text = self._retry_ocr_with_different_config(pil_image)
                    if backup_text:
                        cleaned_text = self._post_process_ocr_text(backup_text)
                        extracted_text.append(f"[第{page_num+1}页]\n{cleaned_text}\n")
                    else:
                        extracted_text.append(f"[第{page_num+1}页]\n(OCR未识别到文本)\n")
            
            if doc:
                doc.close()
                doc = None
            
            if extracted_text:
                full_text = "\n".join(extracted_text)
                
                # 详细的完整OCR处理统计
                total_chars = len(full_text)
                pages_processed = len(extracted_text)
                successful_pages = len([page for page in extracted_text if "OCR处理失败" not in page and "OCR未识别到文本" not in page])
                
                logger.info(f"✅ 完整OCR处理完成 - 总页数: {doc.page_count}, 处理: {pages_processed}, 成功: {successful_pages}")
                logger.info(f"   提取字符总数: {total_chars}个, 平均每页: {total_chars//max(1,successful_pages)}个字符")
                
                # 中文识别质量详细分析
                chinese_chars = len([c for c in full_text if '\u4e00' <= c <= '\u9fff'])
                english_chars = len([c for c in full_text if c.isalpha() and ord(c) < 128])
                digit_chars = len([c for c in full_text if c.isdigit()])
                
                if chinese_chars > 0:
                    logger.info(f"   中文字符: {chinese_chars}个 ({chinese_chars/total_chars*100:.1f}%)")
                if english_chars > 0:
                    logger.info(f"   英文字符: {english_chars}个 ({english_chars/total_chars*100:.1f}%)")
                if digit_chars > 0:
                    logger.info(f"   数字字符: {digit_chars}个 ({digit_chars/total_chars*100:.1f}%)")
                
                # 识别质量评估
                if successful_pages < pages_processed:
                    failed_pages = pages_processed - successful_pages
                    logger.warning(f"   ⚠️ {failed_pages}页OCR识别失败")
                
                return full_text, None
            else:
                logger.warning(f"⚠️ 完整OCR未提取到文本 - 处理了{max_pages}/{doc.page_count}页")
                return None, "完整OCR未提取到任何文本"
                
        except Exception as e:
            if doc:
                try:
                    doc.close()
                except:
                    pass
            logger.error(f"❌ PyMuPDF完整OCR处理失败: {str(e)}")
            return None, f"PyMuPDF OCR失败: {str(e)}"
    
    def _ocr_pdf_with_pdf2image(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用pdf2image进行PDF OCR（原始方法）"""
        try:
            # 先获取PDF页数信息来决定处理策略
            import fitz
            temp_doc = fitz.open(file_path)
            total_pages = temp_doc.page_count
            temp_doc.close()
            
            # 动态决定处理页数
            if total_pages <= 15:
                last_page = total_pages  # 小文档完全处理
            elif total_pages <= 40:
                last_page = min(25, total_pages)  # 中等文档
            else:
                last_page = 35  # 大文档限制页数
                logger.info(f"使用pdf2image处理大型PDF({total_pages}页)，处理前{last_page}页")
            
            # 将PDF转换为图像
            images = pdf2image.convert_from_path(
                file_path,
                dpi=200,  # 提高DPI以获得更好的OCR效果
                first_page=1,
                last_page=last_page  # 动态调整页数
            )
            
            extracted_text = []
            
            for i, image in enumerate(images):
                logger.info(f"OCR处理PDF第{i+1}页")
                
                # 对每页进行OCR - 针对中文文档优化的配置
                page_text = pytesseract.image_to_string(
                    image, 
                    lang='chi_sim+eng',  # 支持简体中文和英文
                    config='--psm 4 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1 -c textord_min_linesize=2.5'
                )
                
                if page_text.strip():
                    extracted_text.append(f"[第{i+1}页]\n{page_text.strip()}\n")
            
            if extracted_text:
                full_text = "\n".join(extracted_text)
                return full_text, None
            else:
                return None, "OCR未提取到任何文本"
                
        except Exception as e:
            return None, f"pdf2image OCR失败: {str(e)}"
    
    def _ocr_image(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """对图像文件进行OCR"""
        try:
            # 打开图像
            image = Image.open(file_path)
            
            # 进行OCR - 针对中文文档优化的配置
            text = pytesseract.image_to_string(
                image,
                lang='chi_sim+eng',  # 支持简体中文和英文
                config='--psm 4 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1 -c textord_min_linesize=2.5'
            )
            
            if text.strip():
                return text.strip(), None
            else:
                return None, "OCR未提取到任何文本"
                
        except Exception as e:
            return None, f"图像OCR失败: {str(e)}"
    
    def _clean_content(self, content: str) -> str:
        """清理提取的内容"""
        if not content:
            return ""
        
        try:
            # 确保内容是有效的UTF-8字符串
            if isinstance(content, bytes):
                # 如果是字节，尝试解码
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = content.decode('gbk')
                    except UnicodeDecodeError:
                        content = content.decode('utf-8', errors='ignore')
            
            # 清理无效字符和特殊符号
            import re
            import unicodedata
            
            # 移除控制字符
            content = content.replace('\x00', '')  # 移除空字符
            content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', content)  # 移除其他控制字符
            
            # 处理特殊符号和无法识别的字符
            cleaned_chars = []
            for char in content:
                try:
                    # 检查字符是否可以正常编码
                    char.encode('utf-8')
                    
                    # 检查字符类别
                    category = unicodedata.category(char)
                    
                    # 保留正常字符：字母、数字、标点、空白、符号
                    if category.startswith(('L', 'N', 'P', 'Z', 'S')):
                        # 特别处理一些常见的问题字符
                        if ord(char) < 32 and char not in '\t\n\r':
                            # 控制字符用*替换
                            cleaned_chars.append('*')
                        elif ord(char) > 0xFFFF:
                            # 超出基本多文种平面的字符可能显示有问题，用*替换
                            cleaned_chars.append('*')
                        else:
                            cleaned_chars.append(char)
                    elif category.startswith('C'):
                        # 其他控制字符和私有使用区字符用*替换
                        if char not in '\t\n\r ':  # 保留基本空白字符
                            cleaned_chars.append('*')
                        else:
                            cleaned_chars.append(char)
                    else:
                        cleaned_chars.append(char)
                        
                except (UnicodeError, UnicodeEncodeError):
                    # 无法编码的字符用*替换
                    cleaned_chars.append('*')
            
            content = ''.join(cleaned_chars)
            
            # 清理多余的空白字符
            content = re.sub(r'\n{3,}', '\n\n', content)  # 多个换行符合并
            content = re.sub(r' {3,}', ' ', content)  # 多个空格合并
            content = re.sub(r'\*{3,}', '***', content)  # 多个连续*号合并为最多3个
            
            # 限制内容长度
            max_content_length = 2000000  # 2MB文本内容
            if len(content) > max_content_length:
                content = content[:max_content_length] + "\n\n[内容过长，已截断...]"
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"内容清理失败: {e}")
            # 如果清理失败，至少尝试基本的字符替换
            try:
                import re
                content = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,;:!?()[]{}"\'-]', '*', content)
                return content.strip()
            except:
                return content
    
    def _preprocess_image_for_ocr(self, image_data: bytes, document_type: str = "general", enable_smart_preprocessing: bool = True) -> Tuple[Optional[bytes], Optional[str]]:
        """
        为OCR预处理图像
        
        Args:
            image_data: 图像数据
            document_type: 文档类型
            enable_smart_preprocessing: 是否启用智能预处理（默认True）
        """
        if not self.image_preprocessor.has_opencv:
            return None, "OpenCV未安装，跳过图像预处理"
        
        try:
            # 分析图像质量
            analysis = self.image_preprocessor.analyze_image_quality(image_data, enable_smart_preprocessing)
            
            if analysis.get("needs_preprocessing", False):
                # 执行预处理
                processed_data, error = self.image_preprocessor.preprocess_for_ocr(image_data, analysis, enable_smart_preprocessing)
                return processed_data, error
            else:
                # 不需要预处理
                return image_data, None
                
        except Exception as e:
            return None, f"图像预处理失败: {str(e)}"
    
    def _get_optimal_scale_factor(self, page) -> float:
        """
        获取最优缩放因子
        
        Args:
            page: PDF页面对象
            
        Returns:
            float: 缩放因子
        """
        try:
            # 获取页面基础信息
            rect = page.rect
            page_width = rect.width
            page_height = rect.height
            
            # 估算页面的原始DPI
            # 标准A4页面是 210×297mm，对应 595×842 点
            estimated_dpi = max(page_width / 8.27, page_height / 11.69) * 72  # 粗略估算
            
            # 根据估算DPI决定缩放策略
            if estimated_dpi >= 300:
                # 高DPI页面，使用较小的缩放
                scale_factor = 1.2
            elif estimated_dpi >= 200:
                # 中等DPI，使用中等缩放  
                scale_factor = 1.5
            else:
                # 低DPI页面，需要较大的缩放
                scale_factor = 2.0
                
            # 考虑页面大小，避免生成过大的图像
            total_pixels = page_width * page_height
            if total_pixels > 1000000:  # 大于100万像素
                scale_factor = min(scale_factor, 1.5)
            
            return scale_factor
            
        except Exception as e:
            logger.warning(f"无法计算最优缩放因子: {e}")
            return 1.5  # 默认使用保守的1.5x缩放
    
    def _get_optimized_ocr_config(self, page_num: int, total_pages: int) -> str:
        """
        获取优化的OCR配置
        基于实践经验选择最有效的参数组合
        """
        # 经过验证的中文文档最优配置
        # PSM 4: 假设文本为单列，不定尺寸的文本块 
        # OEM 3: 默认LSTM神经网络引擎，准确性最好
        # 添加中文优化参数
        return '--psm 4 --oem 3 -c preserve_interword_spaces=1 -c page_separator="" -c textord_heavy_nr=1'
    
    def _retry_ocr_with_different_config(self, pil_image) -> Optional[str]:
        """
        使用不同配置重试OCR
        """
        if not self.has_ocr:
            return None
        
        # 针对中文优化的备用OCR配置
        backup_configs = [
            '--psm 6 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1',  # 单一文本块
            '--psm 4 --oem 3 -c preserve_interword_spaces=0 -c textord_heavy_nr=1',  # 单列文本
            '--psm 3 --oem 3 -c preserve_interword_spaces=0',  # 全自动分割
            '--psm 11 --oem 3 -c textord_heavy_nr=1',  # 稀疏文本
            '--psm 12 --oem 3 -c preserve_interword_spaces=0'   # 稀疏文本OSD
        ]
        
        for config in backup_configs:
            try:
                text = pytesseract.image_to_string(
                    pil_image,
                    lang='chi_sim+eng',
                    config=config
                )
                if text and len(text.strip()) >= 5:  # 至少5个字符才算有效
                    logger.info(f"备用OCR配置成功: {config}")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"备用OCR配置失败 {config}: {e}")
                continue
        
        return None
    
    def _post_process_ocr_text(self, raw_text: str) -> str:
        """
        OCR文本后处理
        修正常见的OCR错误
        """
        if not raw_text:
            return ""
        
        try:
            text = raw_text
            
            # 常见OCR错误修正（中文）
            ocr_corrections = {
                # 数字误识别
                'O': '0',  # 字母O识别为数字0
                'l': '1',  # 小写l识别为数字1
                '|': '1',  # 竖线识别为数字1
                
                # 标点符号修正
                '，': '，',  # 统一逗号
                '。': '。',  # 统一句号
                '？': '？',  # 统一问号
                '！': '！',  # 统一感叹号
                
                # 常见汉字误识别
                '巳': '已',
                '己': '已',
                '戸': '户',
                '仝': '同',
                '堇': '堪'
            }
            
            # 应用修正
            for wrong, correct in ocr_corrections.items():
                text = text.replace(wrong, correct)
            
            # 增强的中文文本空格清理和格式优化
            import re
            
            # 第一步：处理OCR常见的过度分割问题
            # 清理中文字符间的多余空格（如"网 络 安 全"变为"网络安全"）
            text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
            
            # 第二步：处理中文与标点符号间的空格
            text = re.sub(r'([\u4e00-\u9fff])\s+([，。！？；：、])', r'\1\2', text)  # 中文与标点间
            text = re.sub(r'([，。！？；：、])\s+([\u4e00-\u9fff])', r'\1\2', text)  # 标点与中文间
            
            # 第三步：处理数字与中文间的空格（保持合理间距）
            text = re.sub(r'([\u4e00-\u9fff])\s+(\d)', r'\1\2', text)  # 中文数字间
            text = re.sub(r'(\d)\s+([\u4e00-\u9fff])', r'\1\2', text)  # 数字中文间
            
            # 第四步：处理英文单词间的空格（保持正常）
            text = re.sub(r'([a-zA-Z])\s{2,}([a-zA-Z])', r'\1 \2', text)  # 英文间多空格合并
            
            # 第五步：处理中英文混合的间距
            text = re.sub(r'([\u4e00-\u9fff])\s+([a-zA-Z])', r'\1 \2', text)  # 中英文间保持一个空格
            text = re.sub(r'([a-zA-Z])\s+([\u4e00-\u9fff])', r'\1 \2', text)  # 英中文间保持一个空格
            
            # 第六步：处理常见的OCR字符连接问题
            # 修正被错误分离的常见词汇
            common_fixes = {
                '网 络': '网络', '安 全': '安全', '数 据': '数据', '系 统': '系统',
                '信 息': '信息', '管 理': '管理', '技 术': '技术', '服 务': '服务',
                '工 作': '工作', '建 设': '建设', '发 展': '发展', '运 行': '运行',
                '维 护': '维护', '监 控': '监控', '检 查': '检查', '测 试': '测试',
                '配 置': '配置', '部 署': '部署', '升 级': '升级', '优 化': '优化'
            }
            for wrong, correct in common_fixes.items():
                text = text.replace(wrong, correct)
            
            # 第七步：清理多余的空白字符
            text = re.sub(r'\s{3,}', ' ', text)  # 3个以上空格合并为1个
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # 3个以上换行合并为2个
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"OCR文本后处理失败: {e}")
            return raw_text.strip()
    
    def _process_and_clean_content(self, raw_content: str, file_path: str) -> str:
        """
        智能处理和清理内容
        使用SmartTextProcessor进行高质量处理
        """
        try:
            # 确定文档类型
            doc_type = self._detect_document_type(file_path, raw_content)
            
            # 使用智能文本处理器处理
            result = self.text_processor.process_extracted_text(raw_content, doc_type)
            
            # 记录处理统计信息
            stats = self.text_processor.get_processing_statistics(result)
            logger.info(f"文本处理统计: 质量评分={stats['quality_score']:.1f}, "
                       f"修正{stats['corrections_applied']}处, "
                       f"评级={stats.get('grade', '未知')}")
            
            # 如果处理失败或质量太低，使用基础清理
            if result["quality_score"] < 30 or not result["processed_text"]:
                logger.warning("智能文本处理质量较低，使用基础清理")
                return self._clean_content(raw_content)
            
            processed_content = result["processed_text"]
            
            # 记录警告信息
            if result["warnings"]:
                for warning in result["warnings"]:
                    logger.warning(f"文本处理警告: {warning}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"智能文本处理失败: {e}，回退到基础清理")
            return self._clean_content(raw_content)
    
    def _detect_document_type(self, file_path: str, content: str) -> str:
        """
        检测文档类型，用于选择最优处理策略
        """
        try:
            file_name = Path(file_path).name.lower()
            
            # 基于文件名判断
            if any(keyword in file_name for keyword in ["法", "规定", "条例", "办法", "通知", "公告"]):
                return "legal"
            elif any(keyword in file_name for keyword in ["报告", "总结", "分析", "计划"]):
                return "report"  
            elif any(keyword in file_name for keyword in ["技术", "说明", "手册", "指南", "系统"]):
                return "technical"
            
            # 基于内容特征判断
            if content:
                # 法律文档特征
                legal_indicators = ["第", "条", "款", "项", "根据", "依照", "按照", "规定"]
                legal_score = sum(1 for indicator in legal_indicators if indicator in content[:1000])
                
                # 技术文档特征
                tech_indicators = ["系统", "网络", "数据", "技术", "配置", "安装", "操作"]
                tech_score = sum(1 for indicator in tech_indicators if indicator in content[:1000])
                
                # 报告文档特征
                report_indicators = ["报告", "分析", "统计", "总结", "情况", "工作"]
                report_score = sum(1 for indicator in report_indicators if indicator in content[:1000])
                
                # 选择最高分的类型
                scores = {"legal": legal_score, "technical": tech_score, "report": report_score}
                max_type = max(scores, key=scores.get)
                
                if scores[max_type] >= 3:  # 至少有3个相关指示词
                    return max_type
            
            return "general"
            
        except Exception as e:
            logger.debug(f"文档类型检测失败: {e}")
            return "general"
    
    def extract_content_with_validation(self, file_path: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """
        提取内容并进行质量验证
        
        Returns:
            Tuple[content, error, validation_result]: (内容, 错误, 验证结果)
        """
        start_time = time.time()
        
        # 使用标准方法提取内容
        content, error = self.extract_content(file_path)
        
        processing_time = time.time() - start_time
        
        # 质量验证
        validation_result = None
        if content:
            try:
                validation_result = self.quality_validator.validate_extraction_result(
                    original_file=file_path,
                    extracted_content=content,
                    extraction_method="enhanced_extractor", 
                    processing_time=processing_time
                )
                
                # 根据质量评估结果决定是否需要重新处理
                if validation_result["quality_score"] < 40:  # 质量太差
                    logger.warning(f"内容质量较差({validation_result['quality_score']:.1f}分)，尝试重新提取")
                    
                    # 尝试备用提取方法
                    backup_content, backup_error = self._try_backup_extraction(file_path)
                    if backup_content:
                        backup_validation = self.quality_validator.validate_extraction_result(
                            original_file=file_path,
                            extracted_content=backup_content,
                            extraction_method="backup_extractor",
                            processing_time=time.time() - start_time
                        )
                        
                        # 如果备用方法质量更好，使用备用结果
                        if backup_validation["quality_score"] > validation_result["quality_score"]:
                            logger.info(f"备用方法质量更好({backup_validation['quality_score']:.1f}分)，采用备用结果")
                            content = backup_content
                            error = backup_error
                            validation_result = backup_validation
                
                logger.info(f"内容质量评估: {validation_result['quality_score']:.1f}分 "
                           f"({validation_result['quality_grade']}) - {file_path}")
                
            except Exception as e:
                logger.warning(f"质量验证失败: {e}")
        
        return content, error, validation_result
    
    def _try_backup_extraction(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        尝试备用提取方法
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                # 尝试不同的PDF提取方法
                methods = [
                    lambda: self.pdf_extractor.extract_pdf_content(file_path),
                    lambda: self._ocr_pdf(file_path) if self.has_ocr else (None, "OCR不可用"),
                ]
                
                for method in methods:
                    try:
                        content, error = method()
                        if content and len(content.strip()) > 50:
                            return content, error
                    except Exception as e:
                        logger.debug(f"备用提取方法失败: {e}")
                        continue
            else:
                # 其他文件类型使用搜索服务
                content = self.search_service.extract_file_content(file_path)
                if content and len(content.strip()) > 50:
                    return content, None
            
            return None, "所有备用提取方法都失败了"
            
        except Exception as e:
            return None, f"备用提取异常: {str(e)}"
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """
        获取提取统计信息
        """
        try:
            performance_summary = self.quality_validator.get_performance_summary()
            
            stats = {
                "validator_stats": performance_summary,
                "extractor_info": {
                    "has_ocr": self.has_ocr,
                    "has_opencv": self.image_preprocessor.has_opencv if hasattr(self.image_preprocessor, 'has_opencv') else False,
                    "supported_formats": len(self.supported_extensions) if hasattr(self, 'supported_extensions') else 15,
                },
                "quality_thresholds": self.quality_validator.quality_thresholds,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否支持内容提取
        """
        if not os.path.exists(file_path):
            return False
            
        file_ext = Path(file_path).suffix.lower()
        
        # 支持的文件格式
        supported_formats = {
            # 文本文件
            '.txt', '.md', '.csv', '.json', '.xml', '.log',
            '.py', '.js', '.html', '.css', '.sql', '.yml', '.yaml',
            # 文档文件
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            # 图像文件（支持OCR）
            '.jpg', '.jpeg', '.png', '.tiff', '.bmp'
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
    
    def split_content_pages(self, content: str, page_size: int = 5000) -> List[str]:
        """
        将长内容分页
        """
        if not content or len(content) <= page_size:
            return [content] if content else []
        
        pages = []
        words = content.split()
        current_page = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > page_size and current_page:
                # 保存当前页
                pages.append(" ".join(current_page))
                current_page = [word]
                current_length = word_length
            else:
                current_page.append(word)
                current_length += word_length
        
        # 保存最后一页
        if current_page:
            pages.append(" ".join(current_page))
        
        return pages
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        """
        stats = self.performance_stats.copy()
        
        # 计算成功率
        if stats["total_extractions"] > 0:
            stats["success_rate"] = (
                stats["successful_extractions"] / stats["total_extractions"]
            ) * 100
            stats["failure_rate"] = (
                stats["failed_extractions"] / stats["total_extractions"]
            ) * 100
        else:
            stats["success_rate"] = 0
            stats["failure_rate"] = 0
        
        # 格式化时间
        stats["average_processing_time_formatted"] = f"{stats['average_processing_time']:.2f}s"
        stats["total_processing_time_formatted"] = f"{stats['total_processing_time']:.1f}s"
        
        return stats
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.performance_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "ocr_processing_time": 0.0,
            "preprocessing_time": 0.0
        }
        logger.info("性能统计已重置")
    
    def _should_use_simple_mode(self) -> bool:
        """
        判断是否应该使用简单模式
        """
        if not self.fallback_config["enable_smart_fallback"]:
            return False
        
        # 如果已经启用简单模式，继续使用
        if self.fallback_config["use_simple_mode"]:
            return True
        
        # 检查连续失败次数
        if (self.fallback_config["consecutive_failures"] >= 
            self.fallback_config["max_consecutive_failures"]):
            logger.warning(f"连续失败{self.fallback_config['consecutive_failures']}次，启用简单模式")
            self.fallback_config["use_simple_mode"] = True
            return True
        
        # 检查平均处理时间
        if (self.performance_stats["average_processing_time"] > 
            self.fallback_config["max_processing_time"]):
            logger.warning(f"平均处理时间过长({self.performance_stats['average_processing_time']:.1f}s)，启用简单模式")
            self.fallback_config["use_simple_mode"] = True
            return True
        
        # 检查失败率
        if self.performance_stats["total_extractions"] >= 10:  # 至少10次提取后检查
            current_failure_rate = (
                self.performance_stats["failed_extractions"] / 
                self.performance_stats["total_extractions"]
            ) * 100
            
            if current_failure_rate > self.fallback_config["max_failure_rate"]:
                logger.warning(f"失败率过高({current_failure_rate:.1f}%)，启用简单模式")
                self.fallback_config["use_simple_mode"] = True
                return True
        
        return False
    
    def _update_fallback_status(self, processing_time: float, success: bool):
        """
        更新回退状态
        """
        if success:
            # 成功时重置连续失败次数
            self.fallback_config["consecutive_failures"] = 0
            
            # 如果在简单模式下连续成功多次，可以尝试恢复正常模式
            if (self.fallback_config["use_simple_mode"] and 
                self.performance_stats["successful_extractions"] > 0 and
                self.performance_stats["successful_extractions"] % 20 == 0):  # 每20次成功检查一次
                
                # 检查最近的性能表现
                if (self.performance_stats["average_processing_time"] < 
                    self.fallback_config["max_processing_time"] * 0.5):  # 性能良好
                    logger.info("性能良好，尝试恢复正常模式")
                    self.fallback_config["use_simple_mode"] = False
                    self.fallback_config["consecutive_failures"] = 0
    
    def _extract_pdf_content_advanced_with_fallback(self, file_path: str, start_time: float) -> Tuple[Optional[str], Optional[str]]:
        """
        带回退机制的高级PDF内容提取
        """
        try:
            # 尝试使用高级提取器，但设置超时检查
            content, error = self._extract_pdf_content_advanced(file_path)
            
            # 检查处理时间是否过长
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            if elapsed_time > self.fallback_config["max_processing_time"]:
                logger.warning(f"高级提取器处理超时({elapsed_time:.1f}s)，尝试简单提取器")
                # 尝试使用简单提取器作为备选
                backup_content, backup_error = self.pdf_extractor.extract_pdf_content(file_path)
                
                # 如果简单提取器成功且速度更快，使用其结果
                if backup_content and len(backup_content.strip()) > 0:
                    logger.info("简单提取器成功提供备选结果")
                    return backup_content, backup_error
            
            return content, error
            
        except Exception as e:
            logger.warning(f"高级提取器异常，回退到简单提取器: {e}")
            # 异常时直接使用简单提取器
            return self.pdf_extractor.extract_pdf_content(file_path)
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """
        获取智能回退状态
        """
        return {
            "config": self.fallback_config.copy(),
            "performance": self.get_performance_stats(),
            "recommendations": self._get_performance_recommendations()
        }
    
    def _get_performance_recommendations(self) -> List[str]:
        """
        获取性能优化建议
        """
        recommendations = []
        
        if self.performance_stats["average_processing_time"] > 30:
            recommendations.append("平均处理时间过长，建议启用简单模式或减少图像预处理")
        
        if self.performance_stats["total_extractions"] > 0:
            failure_rate = (self.performance_stats["failed_extractions"] / 
                           self.performance_stats["total_extractions"]) * 100
            if failure_rate > 20:
                recommendations.append(f"失败率较高({failure_rate:.1f}%)，检查OCR配置或文档格式支持")
        
        if self.fallback_config["use_simple_mode"]:
            recommendations.append("当前使用简单模式，可能影响OCR和高级功能")
        
        if not recommendations:
            recommendations.append("性能表现良好，无需调整")
        
        return recommendations
    
    def _is_garbled_text(self, text: str) -> bool:
        """
        检测文本是否是乱码
        
        Args:
            text: 要检测的文本
            
        Returns:
            bool: True如果检测到乱码，False否则
        """
        if not text or len(text.strip()) < 10:
            return False
        
        import re
        
        # 清理页面标记，只检查实际内容
        clean_text = text
        clean_text = re.sub(r'\[页面 \d+[^\]]*\]', '', clean_text)
        clean_text = re.sub(r'\[第\d+页[^\]]*\]', '', clean_text)
        clean_text = clean_text.strip()
        
        if len(clean_text) < 10:
            return False
        
        # 快速检测：明显的乱码模式
        obvious_garbled_patterns = [
            r'[A-Z0-9]{2,}\s+[A-Z0-9]{2,}\s+[A-Z0-9]{2,}',  # 连续的大写字母数字组合
            r'\b[A-Z]{1,3}[0-9]{1,3}[A-Z]{1,3}\b',           # 字母数字字母模式
            r'\b[0-9][A-Z]{2,}[0-9]\b',                      # 数字字母数字模式
        ]
        
        for pattern in obvious_garbled_patterns:
            if re.search(pattern, clean_text):
                logger.debug(f"快速检测到明显乱码模式: {pattern}")
                return True
        
        # 检测乱码特征
        garbled_indicators = 0
        total_checks = 0
        
        # 1. 检查连续大写字母+数字的异常模式（如"8LA5 AP CE"）
        uppercase_digit_pattern = re.findall(r'[A-Z0-9]{2,}', clean_text)
        if len(uppercase_digit_pattern) > len(clean_text) / 20:  # 超过5%是大写字母数字组合
            garbled_indicators += 1
            logger.debug("检测到大量大写字母数字组合")
        total_checks += 1
        
        # 2. 检查异常字符分布
        char_count = len(clean_text)
        uppercase_count = sum(1 for c in clean_text if c.isupper())
        if uppercase_count > char_count * 0.7:  # 超过70%是大写字母
            garbled_indicators += 1
            logger.debug(f"大写字母比例异常: {uppercase_count}/{char_count}")
        total_checks += 1
        
        # 3. 检查是否缺少常见的中文字符和英文单词
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', clean_text))
        has_common_english = bool(re.search(r'\b(the|and|is|in|to|of|a|that|it|with|for|as|was|on|are|you|have|be|at|this|not|or|from|he|by|but|they|his|had|has|an|were|said|one|all|we|when|your|can|there|each|which|do|how|their|if|will|up|other|about|out|many|then|them|these|so|some|her|would|make|like|into|time|very|what|know|just|first|no|way|could|may|new|also|after|back|two|work|see|go|good|now|people|any|day|man|through|my|old|come|us|well|most|over|put|think|before|down|take|only|little|where|years|around|much|high|under|get|here|such|both|even|year|still|every|big|small|while|great|another|\w+ly)\b', clean_text, re.IGNORECASE))
        
        if not has_chinese and not has_common_english and char_count > 100:
            garbled_indicators += 1
            logger.debug("缺少常见的中英文字符")
        total_checks += 1
        
        # 4. 检查单词边界异常（正常文本应该有空格分隔）
        words = clean_text.split()
        if len(words) > 5:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length < 2 or avg_word_length > 15:  # 平均单词长度异常
                garbled_indicators += 1
                logger.debug(f"平均单词长度异常: {avg_word_length}")
        total_checks += 1
        
        # 5. 检查是否有大量单字符"词"（如"8 L A 5"）
        single_char_words = sum(1 for word in words if len(word.strip()) == 1)
        if len(words) > 10 and single_char_words > len(words) * 0.5:  # 超过50%是单字符
            garbled_indicators += 1
            logger.debug(f"单字符词过多: {single_char_words}/{len(words)}")
        total_checks += 1
        
        # 6. 检查特定乱码模式（基于实际观察到的乱码）
        garbled_patterns = [
            r'[A-Z]{1,3}\d+\s+[A-Z]{1,3}\s+[A-Z]{2,4}',  # 如 "8LA5 AP CE"
            r'[A-Z]{2,4}[A-Z0-9]{2,4}[A-Z]{2,4}',        # 如 "RMLAN5CE"
            r'\b[A-Z]{1,2}\d[A-Z]{1,2}\b',               # 如 "R1", "A5E"
            r'[A-Z]+\d+[A-Z]+\d+',                       # 如 "REA5AR"
        ]
        
        pattern_matches = 0
        for pattern in garbled_patterns:
            if re.search(pattern, clean_text):
                pattern_matches += 1
        
        if pattern_matches >= 2:  # 匹配多个乱码模式
            garbled_indicators += 2  # 乱码模式匹配给更高权重
            logger.debug(f"匹配到{pattern_matches}个乱码模式")
        total_checks += 1
        
        # 综合判断 - 降低阈值，提高检测灵敏度
        garbled_ratio = garbled_indicators / total_checks
        is_garbled = garbled_ratio >= 0.3  # 30%以上指标异常认为是乱码（降低阈值）
        
        if is_garbled:
            logger.info(f"乱码检测结果: {garbled_indicators}/{total_checks} 项异常 (比例: {garbled_ratio:.2f})")
            logger.debug(f"乱码样本: {clean_text[:200]}...")
        
        return is_garbled