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
                            # 增强编码处理
                            cleaned_text = self._fix_text_encoding(text.strip())
                            text_content.append(f"[页面 {page_num + 1}]\n{cleaned_text}\n")
                        else:
                            text_content.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                            
                    except Exception as page_error:
                        logger.warning(f"页面 {page_num + 1} 提取失败: {page_error}")
                        text_content.append(f"[页面 {page_num + 1}]\n(页面提取失败: {str(page_error)})\n")
                
                if len(pdf.pages) > self.max_pages:
                    text_content.append(f"\n[注意: 文档共有 {len(pdf.pages)} 页，仅提取了前 {self.max_pages} 页]")
            
            if text_content:
                full_content = "\n".join(text_content)
                # 最终编码检查和清理
                full_content = self._final_text_cleanup(full_content)
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
                            # 增强编码处理
                            cleaned_text = self._fix_text_encoding(text.strip())
                            text_content.append(f"[页面 {page_num + 1}]\n{cleaned_text}\n")
                        else:
                            text_content.append(f"[页面 {page_num + 1}]\n(无文本内容)\n")
                            
                    except Exception as page_error:
                        logger.warning(f"页面 {page_num + 1} 提取失败: {page_error}")
                        text_content.append(f"[页面 {page_num + 1}]\n(页面提取失败: {str(page_error)})\n")
                
                if len(pdf_reader.pages) > self.max_pages:
                    text_content.append(f"\n[注意: 文档共有 {len(pdf_reader.pages)} 页，仅提取了前 {self.max_pages} 页]")
            
            if text_content:
                full_content = "\n".join(text_content)
                # 最终编码检查和清理
                full_content = self._final_text_cleanup(full_content)
                return full_content, None
            else:
                return None, "PDF文档中没有找到可提取的文本内容"
                
        except Exception as e:
            return None, f"PyPDF2提取失败: {str(e)}"
    
    def _fix_text_encoding(self, text: str) -> str:
        """修复文本编码问题"""
        if not text:
            return text
        
        try:
            # 方法1: 如果文本已经是正确的UTF-8，直接返回
            text.encode('utf-8').decode('utf-8')
            
            # 检查是否包含常见的编码错误模式
            if self._has_encoding_issues(text):
                # 尝试修复常见的编码问题
                fixed_text = self._fix_common_encoding_issues(text)
                if fixed_text != text:
                    logger.info("修复了文本编码问题")
                    return fixed_text
            
            return text
            
        except UnicodeError:
            # 如果UTF-8编码失败，尝试其他编码方式
            logger.warning("检测到UTF-8编码问题，尝试修复")
            return self._handle_encoding_error(text)
    
    def _has_encoding_issues(self, text: str) -> bool:
        """检查文本是否有编码问题"""
        # 检查常见的编码问题特征
        encoding_issues = [
            '�',  # 替换字符
            '\ufffd',  # Unicode替换字符
            '\x00',  # 空字符
        ]
        
        # 检查是否有大量连续的问号或特殊字符
        if '???' in text or '���' in text:
            return True
        
        # 检查是否有编码问题特征
        for issue in encoding_issues:
            if issue in text:
                return True
        
        # 检查中文字符是否显示异常
        if self._has_garbled_chinese(text):
            return True
        
        return False
    
    def _has_garbled_chinese(self, text: str) -> bool:
        """检查是否有乱码的中文字符"""
        import re
        
        # 检查是否有明显的中文乱码模式
        garbled_patterns = [
            r'[\\u00-\\u07][0-9a-fA-F]{4}',  # 类似 \u0000 的模式
            r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]{3,}',  # 连续非中英文字符
        ]
        
        for pattern in garbled_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _fix_common_encoding_issues(self, text: str) -> str:
        """修复常见的编码问题"""
        # 移除或替换问题字符
        text = text.replace('�', '')
        text = text.replace('\ufffd', '')
        text = text.replace('\x00', '')
        
        # 修复常见的Windows编码问题
        encoding_fixes = {
            'â€™': "'",  # 撇号
            'â€œ': '"',  # 左双引号
            'â€': '"',   # 右双引号
            'â€"': '—',  # 长破折号
            'â€¢': '•',  # 项目符号
        }
        
        for bad, good in encoding_fixes.items():
            text = text.replace(bad, good)
        
        return text
    
    def _handle_encoding_error(self, text: str) -> str:
        """处理编码错误"""
        try:
            # 尝试不同的编码解码方式
            if isinstance(text, str):
                # 如果已经是字符串，尝试重新编码处理
                byte_text = text.encode('latin1', errors='ignore')
                
                # 尝试常见编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'cp1252']:
                    try:
                        decoded_text = byte_text.decode(encoding, errors='ignore')
                        if decoded_text and not self._has_encoding_issues(decoded_text):
                            logger.info(f"使用{encoding}编码修复成功")
                            return decoded_text
                    except:
                        continue
            
            # 如果所有方法都失败，返回清理后的文本
            return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.error(f"编码修复失败: {e}")
            return text
    
    def _final_text_cleanup(self, text: str) -> str:
        """最终文本清理和格式化"""
        if not text:
            return text
        
        import re
        
        # 清理控制字符（保留常用的换行符、制表符等）
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        # 规范化空白字符
        text = re.sub(r'\r\n', '\n', text)  # Windows换行符转Unix
        text = re.sub(r'\r', '\n', text)    # Mac换行符转Unix
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格或制表符合并为单个空格
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行符合并为最多两个
        
        # 清理行首行尾空白
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        text = '\n'.join(cleaned_lines)
        
        # 确保UTF-8编码正确性
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            pass
        
        return text.strip()

    def is_pdf_file(self, file_path: str) -> bool:
        """检查是否为PDF文件"""
        return Path(file_path).suffix.lower() == '.pdf'