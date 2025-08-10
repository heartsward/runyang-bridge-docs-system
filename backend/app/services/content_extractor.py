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
from app.services.enhanced_pdf_extractor import EnhancedPDFExtractor

logger = logging.getLogger(__name__)

class ContentExtractor:
    """文档内容提取器"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.pdf_extractor = EnhancedPDFExtractor()
        
    def extract_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取文档内容
        
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
            
            # 检查文件类型
            file_ext = Path(file_path).suffix.lower()
            
            # 对PDF文件使用增强提取器
            if file_ext == '.pdf':
                content, error = self.pdf_extractor.extract_pdf_content(file_path)
                if error:
                    logger.warning(f"PDF提取警告: {error}")
                if not content:
                    return None, error or "PDF内容提取失败"
            else:
                # 其他文件类型使用原有的搜索服务
                content = self.search_service.extract_file_content(file_path)
            
            if content:
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
                    
                    # 清理无效字符
                    content = content.replace('\x00', '')  # 移除空字符
                    content = ''.join(char for char in content if ord(char) >= 32 or char in '\t\n\r')
                    
                    # 限制内容长度
                    max_content_length = 1000000  # 1MB文本内容
                    if len(content) > max_content_length:
                        content = content[:max_content_length] + "\n\n[内容过长，已截断...]"
                    
                    logger.info(f"内容提取成功: {file_path}, 内容长度: {len(content)}")
                    return content, None
                    
                except Exception as encoding_error:
                    logger.error(f"内容编码处理失败: {encoding_error}")
                    return None, f"内容编码处理失败: {str(encoding_error)}"
            else:
                return None, "无法提取文件内容"
                
        except Exception as e:
            error_msg = f"内容提取失败: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
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
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'
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