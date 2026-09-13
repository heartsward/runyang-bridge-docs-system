# -*- coding: utf-8 -*-
"""
搜索服务 - 简化版
只使用LibreOffice处理Office文档和PDF，Excel直接转换为TXT，只有图片和图片PDF使用OCR
"""
import os
import re
import json
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

# 导入智能编码检测工具
from app.utils.encoding_detector import EncodingDetector

try:
    import markdown
except ImportError:
    markdown = None

class SearchService:
    """文件内容搜索服务 - 简化版"""
    
    def __init__(self):
        self.supported_extensions = {
            # 文本文件
            '.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.xml', '.yml', '.yaml',
            # 配置文件
            '.conf', '.config', '.cfg', '.ini', '.properties', '.env',
            # Office文档
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # 其他文档
            '.rtf', '.odt', '.ods', '.odp'
        }
    
    def search_in_text(self, text: str, keyword: str, quick_mode: bool = False) -> List[Dict[str, Any]]:
        """在文本内容中搜索关键词"""
        return self._search_in_text(text, keyword, quick_mode)
    
    def search_in_file(self, file_path: str, keyword: str, quick_mode: bool = False) -> List[Dict[str, Any]]:
        """在文件中搜索关键词"""
        try:
            if not os.path.exists(file_path):
                return []
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_extensions:
                return []
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            
            if quick_mode:
                if file_ext == '.pptx':  # PowerPoint始终跳过
                    return []
                if file_size > 1024 * 1024:  # 大于1MB时跳过
                    return []
            
            if file_size > 2 * 1024 * 1024:  # 大于2MB的文件
                if quick_mode:
                    return []
                # 对大文件只读取前10000字符
                content = self.extract_file_content_partial(file_path, max_chars=10000)
            else:
                # 读取文件内容
                content = self.extract_file_content(file_path)
            
            if not content:
                return []
            
            return self._search_in_text(content, keyword, quick_mode)
            
        except Exception as e:
            print(f"搜索文件 {file_path} 失败: {str(e)}")
            return []
    
    def _search_in_text(self, text: str, keyword: str, quick_mode: bool = False) -> List[Dict[str, Any]]:
        """在文本中搜索关键词"""
        if not text or not keyword:
            return []
        
        results = []
        lines = text.split('\n')
        
        # 创建不区分大小写的正则表达式
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            if pattern.search(line):
                results.append({
                    'line_number': line_num,
                    'content': line.strip(),
                    'keyword': keyword
                })
                
                # 快速模式只返回前10个结果
                if quick_mode and len(results) >= 10:
                    break
        
        return results
    
    def extract_file_content(self, file_path: str) -> Optional[str]:
        """提取文件内容（阶段四：统一走新路由器）

        旧版本：分别调用 LibreOffice/PyPDF/OCR 各自的 helper
        新版本：统一调用 ExtractionRouter（app.services.extraction）
        """
        try:
            if not os.path.exists(file_path):
                return None

            # 阶段四：统一走新路由器（Xlsx/Docx/Text/Pdf/Image 五种 extractor）
            from app.services.extraction import ExtractionRouter
            result = ExtractionRouter().extract(file_path)
            return result.markdown if result.is_success else None

        except Exception as e:
            print(f"提取文件内容失败 {file_path}: {str(e)}")
            return None
    
    
    def extract_file_content_partial(self, file_path: str, max_chars: int = 10000) -> Optional[str]:
        """提取文件内容的前N个字符，用于大文件快速搜索"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_ext = Path(file_path).suffix.lower()
            
            # 对于文本文件，直接读取前N个字符
            if file_ext in {'.txt', '.py', '.js', '.html', '.xml', '.yml', '.yaml', '.csv', '.rtf', 
                           '.conf', '.config', '.cfg', '.ini', '.properties', '.env', '.md'}:
                detected_encoding, confidence = EncodingDetector.detect_encoding(file_path)
                try:
                    with open(file_path, 'r', encoding=detected_encoding) as f:
                        content = f.read(max_chars)
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(max_chars)
                
                if len(content) == max_chars:
                    # 截断到最后一个完整的行
                    last_newline = content.rfind('\n')
                    if last_newline > 0:
                        content = content[:last_newline]
                return content
            
            # JSON文件部分读取
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(max_chars)
                    return content
            
            # 对于复杂文件类型，跳过部分读取
            else:
                return None
                
        except Exception as e:
            print(f"部分提取文件内容失败 {file_path}: {str(e)}")
            return None
    
    def highlight_text(self, text: str, keyword: str) -> str:
        """在文本中高亮关键词"""
        try:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            return pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)
        except Exception:
            return text
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': Path(file_path).suffix.lower()
            }
        except Exception:
            return {}