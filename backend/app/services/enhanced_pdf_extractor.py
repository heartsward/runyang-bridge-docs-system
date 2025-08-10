# -*- coding: utf-8 -*-
"""
增强的PDF内容提取器
"""
import os
import logging
from typing import Optional, Tuple
from pathlib import Path

# 导入PDF处理库
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)

class EnhancedPDFExtractor:
    """增强的PDF内容提取器"""
    
    def __init__(self):
        self.max_pages = 100  # 最大处理页数
        
    def extract_pdf_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取PDF文档内容
        
        Returns:
            Tuple[content, error]: (提取的内容, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return None, f"文件不存在: {file_path}"
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            logger.info(f"开始提取PDF内容: {file_path} ({size_mb:.2f}MB)")
            
            # 方法1: 使用pdfplumber (更准确)
            if pdfplumber:
                content, error = self._extract_with_pdfplumber(file_path)
                if content:
                    return content, error
                logger.warning(f"pdfplumber提取失败: {error}")
            
            # 方法2: 使用PyPDF2 (备用)
            if PyPDF2:
                content, error = self._extract_with_pypdf2(file_path)
                if content:
                    return content, error
                logger.warning(f"PyPDF2提取失败: {error}")
            
            return None, "所有PDF提取方法都失败了，请检查是否安装了pdfplumber或PyPDF2库"
            
        except Exception as e:
            error_msg = f"PDF内容提取异常: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _extract_with_pdfplumber(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用pdfplumber提取PDF内容"""
        try:
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    try:
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        
                        if text and text.strip():
                            text_content.append(f"[页面 {page_num + 1}]\n{text.strip()}\n")
                        else:
                            text_content.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                            
                    except Exception as page_error:
                        logger.warning(f"页面 {page_num + 1} 提取失败: {page_error}")
                        text_content.append(f"[页面 {page_num + 1}]\n(页面提取失败: {str(page_error)})\n")
                
                if len(pdf.pages) > self.max_pages:
                    text_content.append(f"\n[注意: 文档共有 {len(pdf.pages)} 页，仅提取了前 {self.max_pages} 页]")
            
            if text_content:
                full_content = "\n".join(text_content)
                return full_content, None
            else:
                return None, "PDF文档中没有找到可提取的文本内容"
                
        except Exception as e:
            return None, f"pdfplumber提取失败: {str(e)}"
    
    def _extract_with_pypdf2(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """使用PyPDF2提取PDF内容"""
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = min(len(pdf_reader.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if text and text.strip():
                            text_content.append(f"[页面 {page_num + 1}]\n{text.strip()}\n")
                        else:
                            text_content.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                            
                    except Exception as page_error:
                        logger.warning(f"页面 {page_num + 1} 提取失败: {page_error}")
                        text_content.append(f"[页面 {page_num + 1}]\n(页面提取失败: {str(page_error)})\n")
                
                if len(pdf_reader.pages) > self.max_pages:
                    text_content.append(f"\n[注意: 文档共有 {len(pdf_reader.pages)} 页，仅提取了前 {self.max_pages} 页]")
            
            if text_content:
                full_content = "\n".join(text_content)
                return full_content, None
            else:
                return None, "PDF文档中没有找到可提取的文本内容"
                
        except Exception as e:
            return None, f"PyPDF2提取失败: {str(e)}"
    
    def is_pdf_file(self, file_path: str) -> bool:
        """检查是否为PDF文件"""
        return Path(file_path).suffix.lower() == '.pdf'