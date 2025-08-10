# -*- coding: utf-8 -*-
"""
高级PDF内容提取器 - 基于PyMuPDF的高性能实现
优化重点：单文档提取速度、提取质量、内容后处理
"""
import os
import logging
import time
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import io

# 导入PDF处理库
try:
    import fitz  # PyMuPDF - 主引擎
    HAS_PYMUPDF = True
except ImportError:
    fitz = None
    HAS_PYMUPDF = False

try:
    import pdfplumber  # 备用引擎
    HAS_PDFPLUMBER = True
except ImportError:
    pdfplumber = None
    HAS_PDFPLUMBER = False

# 导入流式处理器
from .streaming_processor import StreamingFileProcessor

logger = logging.getLogger(__name__)

class AdvancedPDFExtractor:
    """
    高级PDF内容提取器
    - 基于PyMuPDF的高性能提取
    - 智能文档类型检测  
    - 自适应提取策略
    """
    
    def __init__(self):
        self.max_pages = 100  # 最大处理页数
        self.max_file_size_mb = 100  # 最大文件大小(MB)
        self.text_extraction_threshold = 0.1  # 文本提取率阈值
        self.streaming_processor = StreamingFileProcessor()  # 流式处理器
        
        # 检查依赖库
        if not HAS_PYMUPDF:
            logger.warning("PyMuPDF未安装，性能将受到影响")
        if not HAS_PDFPLUMBER:
            logger.warning("pdfplumber未安装，备用方案不可用")
    
    def extract_pdf_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        智能PDF内容提取
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            Tuple[content, error]: (提取的内容, 错误信息)
        """
        try:
            start_time = time.time()
            
            if not os.path.exists(file_path):
                return None, f"文件不存在: {file_path}"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            if size_mb > self.max_file_size_mb:
                return None, f"文件过大: {size_mb:.2f}MB，超过{self.max_file_size_mb}MB限制"
            
            logger.info(f"开始高级PDF提取: {file_path} ({size_mb:.2f}MB)")
            
            # 智能文档类型分析
            doc_analysis = self._analyze_pdf_document(file_path)
            logger.info(f"文档分析结果: {doc_analysis}")
            
            # 根据文档类型选择最优提取策略
            content, error = self._extract_with_optimal_strategy(file_path, doc_analysis)
            
            extraction_time = time.time() - start_time
            
            if content:
                logger.info(f"PDF提取成功: {file_path}, 耗时: {extraction_time:.2f}s, 内容长度: {len(content)}")
                return content, None
            else:
                logger.warning(f"PDF提取失败: {file_path}, 耗时: {extraction_time:.2f}s, 错误: {error}")
                return None, error
                
        except Exception as e:
            error_msg = f"PDF提取异常: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
            return None, error_msg
    
    def _analyze_pdf_document(self, file_path: str) -> Dict[str, Any]:
        """
        分析PDF文档特征，确定最优提取策略
        
        Returns:
            文档分析结果字典
        """
        analysis = {
            "document_type": "unknown",  # text_based, image_based, hybrid
            "total_pages": 0,
            "text_pages": 0,
            "image_pages": 0,
            "text_extraction_rate": 0.0,
            "has_images": False,
            "has_tables": False,
            "average_chars_per_page": 0,
            "recommended_method": "pymupdf"
        }
        
        if not HAS_PYMUPDF:
            analysis["recommended_method"] = "pdfplumber"
            return analysis
        
        try:
            # 使用PyMuPDF进行快速分析
            doc = fitz.open(file_path)
            analysis["total_pages"] = len(doc)
            
            total_chars = 0
            text_pages = 0
            image_pages = 0
            
            # 采样分析（最多分析前10页）
            sample_pages = min(10, len(doc))
            
            for page_num in range(sample_pages):
                page = doc[page_num]
                
                # 检查文本内容
                text = page.get_text()
                char_count = len(text.strip()) if text else 0
                total_chars += char_count
                
                if char_count > 50:  # 有意义的文本内容
                    text_pages += 1
                
                # 检查图像内容
                image_list = page.get_images()
                if image_list:
                    analysis["has_images"] = True
                    image_pages += 1
                
                # 检查表格（简单启发式）
                if text and any(indicator in text for indicator in ['\t', '  ', '|', '┃', '─']):
                    analysis["has_tables"] = True
            
            doc.close()
            
            # 计算统计信息
            analysis["text_pages"] = text_pages
            analysis["image_pages"] = image_pages
            analysis["average_chars_per_page"] = total_chars / sample_pages if sample_pages > 0 else 0
            analysis["text_extraction_rate"] = text_pages / sample_pages if sample_pages > 0 else 0
            
            # 确定文档类型
            if analysis["text_extraction_rate"] > 0.8:
                analysis["document_type"] = "text_based"
                analysis["recommended_method"] = "pymupdf_fast"
            elif analysis["text_extraction_rate"] < 0.3:
                analysis["document_type"] = "image_based"
                analysis["recommended_method"] = "ocr_required"
            else:
                analysis["document_type"] = "hybrid"
                analysis["recommended_method"] = "pymupdf_ocr"
                
        except Exception as e:
            logger.warning(f"PDF文档分析失败: {e}")
            analysis["recommended_method"] = "pdfplumber"
        
        return analysis
    
    def _extract_with_optimal_strategy(self, file_path: str, analysis: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        根据文档分析结果选择最优提取策略
        """
        method = analysis["recommended_method"]
        
        try:
            if method == "pymupdf_fast":
                return self._fast_text_extraction(file_path)
            elif method == "pymupdf_ocr":
                return self._hybrid_extraction(file_path)
            elif method == "ocr_required":
                return self._prepare_for_ocr(file_path)
            else:  # fallback to pdfplumber
                return self._extract_with_pdfplumber(file_path)
                
        except Exception as e:
            logger.warning(f"主要提取方法失败 ({method}): {e}")
            # 降级到备用方法
            return self._extract_with_fallback(file_path)
    
    def _fast_text_extraction(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        快速文本提取 - 适用于纯文本PDF
        使用PyMuPDF的高性能文本提取 + 流式处理优化
        """
        try:
            # 检查是否需要流式处理
            file_info = self.streaming_processor.get_file_info(file_path)
            use_streaming = file_info["is_large"]
            
            if use_streaming:
                logger.info(f"使用流式处理提取大型PDF: {file_info['size_mb']:.2f}MB")
            
            content_parts = []
            doc = fitz.open(file_path)
            total_pages = min(len(doc), self.max_pages)
            
            if use_streaming:
                # 流式处理 - 分批处理页面
                for page_num, text in self.streaming_processor.process_large_pdf_pages(doc, total_pages):
                    if text and text.strip():
                        content_parts.append(f"[页面 {page_num + 1}]\n{text}\n")
                    else:
                        content_parts.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                        
                    # 内存控制 - 每处理10页检查一次内存
                    if page_num > 0 and page_num % 10 == 0:
                        memory_info = self.streaming_processor.get_memory_usage_info()
                        if "rss_mb" in memory_info and memory_info["rss_mb"] > 500:  # 500MB内存限制
                            logger.warning(f"内存使用过高，停止处理更多页面: {memory_info['rss_mb']:.1f}MB")
                            break
            else:
                # 常规处理 - 小文件快速处理
                for page_num in range(total_pages):
                    page = doc[page_num]
                    text = page.get_text("text", sort=True)
                    
                    if text and text.strip():
                        cleaned_text = self._basic_text_cleanup(text)
                        if cleaned_text:
                            content_parts.append(f"[页面 {page_num + 1}]\n{cleaned_text}\n")
                    else:
                        content_parts.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
            
            total_doc_pages = len(doc)
            doc.close()
            
            if total_doc_pages > self.max_pages:
                content_parts.append(f"\n[注意: 文档共有 {total_doc_pages} 页，仅提取了前 {self.max_pages} 页]")
            
            if content_parts:
                full_content = "\n".join(content_parts)
                return full_content, None
            else:
                return None, "PDF文档中没有找到可提取的文本内容"
                
        except Exception as e:
            return None, f"快速文本提取失败: {str(e)}"
    
    def _hybrid_extraction(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        混合提取 - 文本提取 + 必要时OCR
        适用于部分文本、部分图像的文档
        """
        try:
            content_parts = []
            doc = fitz.open(file_path)
            
            total_pages = min(len(doc), self.max_pages)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # 尝试文本提取
                text = page.get_text("text", sort=True)
                
                if text and len(text.strip()) > 30:  # 有足够的文本内容
                    cleaned_text = self._basic_text_cleanup(text)
                    content_parts.append(f"[页面 {page_num + 1} - 文本]\n{cleaned_text}\n")
                else:
                    # 文本内容不足，标记为需要OCR
                    content_parts.append(f"[页面 {page_num + 1} - 需要OCR]\n(扫描内容或图像，需要OCR处理)\n")
            
            total_doc_pages = len(doc)
            doc.close()
            
            if total_doc_pages > self.max_pages:
                content_parts.append(f"\n[注意: 文档共有 {total_doc_pages} 页，仅提取了前 {self.max_pages} 页]")
            
            if content_parts:
                full_content = "\n".join(content_parts)
                return full_content, None
            else:
                return None, "混合提取未获得有效内容"
                
        except Exception as e:
            return None, f"混合提取失败: {str(e)}"
    
    def _prepare_for_ocr(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        为OCR准备内容 - 适用于扫描版PDF
        提取图像信息，为后续OCR处理做准备
        """
        try:
            content_parts = []
            doc = fitz.open(file_path)
            
            total_pages = min(len(doc), self.max_pages)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # 检查页面是否包含图像
                image_list = page.get_images()
                text = page.get_text()
                
                if image_list or (text and len(text.strip()) < 10):
                    # 这是图像页面或几乎无文本的页面
                    content_parts.append(f"[页面 {page_num + 1} - 图像内容]\n(扫描页面，需要OCR处理)\n")
                else:
                    # 尝试提取现有文本
                    cleaned_text = self._basic_text_cleanup(text) if text else ""
                    if cleaned_text:
                        content_parts.append(f"[页面 {page_num + 1}]\n{cleaned_text}\n")
                    else:
                        content_parts.append(f"[页面 {page_num + 1}]\n(需要OCR处理)\n")
            
            doc.close()
            
            if content_parts:
                full_content = "\n".join(content_parts)
                # 添加OCR提示
                full_content += "\n\n[提示: 此文档主要为扫描内容，建议使用OCR进行完整提取]"
                return full_content, None
            else:
                return None, "文档为扫描版，需要OCR处理"
                
        except Exception as e:
            return None, f"OCR准备失败: {str(e)}"
    
    def _extract_with_pdfplumber(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        使用pdfplumber提取内容（备用方法）
        """
        if not HAS_PDFPLUMBER:
            return None, "pdfplumber库不可用"
        
        try:
            content_parts = []
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    try:
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        
                        if text and text.strip():
                            cleaned_text = self._basic_text_cleanup(text)
                            content_parts.append(f"[页面 {page_num + 1}]\n{cleaned_text}\n")
                        else:
                            content_parts.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                            
                    except Exception as page_error:
                        logger.warning(f"pdfplumber页面 {page_num + 1} 提取失败: {page_error}")
                        content_parts.append(f"[页面 {page_num + 1}]\n(页面提取失败)\n")
                
                if len(pdf.pages) > self.max_pages:
                    content_parts.append(f"\n[注意: 文档共有 {len(pdf.pages)} 页，仅提取了前 {self.max_pages} 页]")
            
            if content_parts:
                full_content = "\n".join(content_parts)
                return full_content, None
            else:
                return None, "pdfplumber未提取到有效内容"
                
        except Exception as e:
            return None, f"pdfplumber提取失败: {str(e)}"
    
    def _extract_with_fallback(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        降级备用提取方法
        """
        logger.info(f"使用降级方法提取PDF: {file_path}")
        
        # 尝试pdfplumber
        if HAS_PDFPLUMBER:
            content, error = self._extract_with_pdfplumber(file_path)
            if content:
                return content, None
        
        # 最后尝试基础PyMuPDF
        if HAS_PYMUPDF:
            try:
                return self._fast_text_extraction(file_path)
            except:
                pass
        
        return None, "所有PDF提取方法都失败了"
    
    def _basic_text_cleanup(self, text: str) -> str:
        """
        基础文本清理 - 快速清理常见问题
        """
        if not text:
            return ""
        
        try:
            # 移除过多的空白字符
            import re
            
            # 替换多个连续空白字符
            text = re.sub(r'\s{3,}', '  ', text)
            
            # 规范化换行符
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # 移除行首行尾多余空白
            lines = text.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            
            return '\n'.join(cleaned_lines)
            
        except Exception:
            # 清理失败，返回原文本
            return text.strip()
    
    def get_extraction_stats(self, file_path: str) -> Dict[str, Any]:
        """
        获取PDF提取统计信息（用于调试和优化）
        """
        stats = {
            "file_path": file_path,
            "file_size_mb": 0,
            "total_pages": 0,
            "extraction_method": "unknown",
            "extraction_time": 0,
            "content_length": 0,
            "success": False,
            "analysis": {}
        }
        
        if not os.path.exists(file_path):
            return stats
        
        try:
            start_time = time.time()
            
            # 基本文件信息
            stats["file_size_mb"] = os.path.getsize(file_path) / (1024 * 1024)
            
            # 文档分析
            stats["analysis"] = self._analyze_pdf_document(file_path)
            stats["extraction_method"] = stats["analysis"]["recommended_method"]
            
            # 尝试提取
            content, error = self.extract_pdf_content(file_path)
            
            stats["extraction_time"] = time.time() - start_time
            stats["success"] = content is not None
            stats["content_length"] = len(content) if content else 0
            stats["error"] = error
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def is_pdf_file(self, file_path: str) -> bool:
        """检查是否为PDF文件"""
        return Path(file_path).suffix.lower() == '.pdf'