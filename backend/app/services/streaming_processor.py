# -*- coding: utf-8 -*-
"""
流式文件处理器 - 优化大文件内存使用
处理大型文档时避免内存溢出
"""
import os
import logging
import mmap
from typing import Optional, Iterator, Tuple, Generator
from pathlib import Path

logger = logging.getLogger(__name__)

class StreamingFileProcessor:
    """
    流式文件处理器
    - 内存映射大文件访问
    - 分块处理机制
    - 智能缓存策略
    """
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB默认块大小
        self.chunk_size = chunk_size
        self.max_memory_usage = 50 * 1024 * 1024  # 50MB内存限制
        
    def get_file_info(self, file_path: str) -> dict:
        """获取文件基本信息"""
        if not os.path.exists(file_path):
            return {"exists": False}
        
        stat = os.stat(file_path)
        
        return {
            "exists": True,
            "size": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "is_large": stat.st_size > self.max_memory_usage,
            "recommended_method": "streaming" if stat.st_size > self.max_memory_usage else "direct"
        }
    
    def read_text_file_streaming(self, file_path: str, encoding: str = 'utf-8') -> Iterator[str]:
        """
        流式读取文本文件
        适用于大型文本文件
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                while True:
                    chunk = file.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
                        
        except Exception as e:
            logger.error(f"流式读取文件失败: {file_path}, 错误: {e}")
            yield ""
    
    def read_text_file_mmap(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        使用内存映射读取文本文件
        适用于需要随机访问的大文件
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    # 读取文件内容
                    content = mmapped_file.read().decode(encoding, errors='ignore')
                    return content
                    
        except Exception as e:
            logger.error(f"内存映射读取失败: {file_path}, 错误: {e}")
            return None
    
    def read_text_file_smart(self, file_path: str, max_length: Optional[int] = None) -> Optional[str]:
        """
        智能读取文本文件
        根据文件大小自动选择最优方法
        """
        file_info = self.get_file_info(file_path)
        
        if not file_info["exists"]:
            return None
        
        try:
            # 小文件直接读取
            if file_info["size"] < self.max_memory_usage:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if max_length and len(content) > max_length:
                        return content[:max_length] + "\n\n[内容已截断...]"
                    return content
            
            # 大文件流式处理
            else:
                logger.info(f"大文件流式处理: {file_path} ({file_info['size_mb']:.2f}MB)")
                content_parts = []
                current_length = 0
                
                for chunk in self.read_text_file_streaming(file_path):
                    content_parts.append(chunk)
                    current_length += len(chunk)
                    
                    # 如果指定了最大长度且超过限制，截断
                    if max_length and current_length > max_length:
                        content = ''.join(content_parts)[:max_length]
                        return content + "\n\n[内容已截断...]"
                
                return ''.join(content_parts)
                
        except Exception as e:
            logger.error(f"智能文件读取失败: {file_path}, 错误: {e}")
            return None
    
    def process_large_pdf_pages(self, pdf_doc, max_pages: int = 100) -> Generator[Tuple[int, str], None, None]:
        """
        分批处理PDF页面
        避免一次性加载所有页面到内存
        """
        total_pages = len(pdf_doc)
        process_pages = min(total_pages, max_pages)
        
        logger.info(f"开始分批处理PDF页面: 总页数={total_pages}, 处理页数={process_pages}")
        
        for page_num in range(process_pages):
            try:
                page = pdf_doc[page_num]
                text = page.get_text("text", sort=True)
                
                # 基础清理
                if text:
                    text = self._clean_page_text(text)
                
                yield page_num, text
                
                # 释放页面引用（如果支持）
                if hasattr(page, 'close'):
                    page.close()
                    
            except Exception as e:
                logger.warning(f"处理页面 {page_num + 1} 失败: {e}")
                yield page_num, f"(页面处理失败: {str(e)})"
    
    def _clean_page_text(self, text: str) -> str:
        """
        清理单页文本内容
        快速清理，避免复杂操作
        """
        if not text:
            return ""
        
        try:
            # 移除过多空白
            import re
            text = re.sub(r'\s{4,}', '  ', text)  # 4个以上空格替换为2个
            text = re.sub(r'\n{4,}', '\n\n', text)  # 4个以上换行替换为2个
            
            # 移除行首行尾空白
            lines = []
            for line in text.split('\n'):
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
            
            return '\n'.join(lines)
            
        except Exception:
            return text.strip()
    
    def estimate_processing_time(self, file_path: str, processing_type: str = "pdf") -> dict:
        """
        估算处理时间
        帮助用户了解处理进度
        """
        file_info = self.get_file_info(file_path)
        
        if not file_info["exists"]:
            return {"error": "文件不存在"}
        
        # 基于经验的处理时间估算（秒）
        time_estimates = {
            "pdf_text": 0.1,  # 每MB文本PDF的处理时间
            "pdf_image": 2.0,  # 每MB图像PDF的处理时间
            "pdf_ocr": 10.0,   # 每MB需要OCR的PDF处理时间
            "text": 0.01,      # 每MB纯文本文件处理时间
            "office": 0.5      # 每MB Office文档处理时间
        }
        
        base_time = time_estimates.get(processing_type, 1.0)
        estimated_seconds = file_info["size_mb"] * base_time
        
        # 添加基础开销
        estimated_seconds += 2.0  # 2秒基础开销
        
        return {
            "file_size_mb": file_info["size_mb"],
            "processing_type": processing_type,
            "estimated_seconds": estimated_seconds,
            "estimated_minutes": estimated_seconds / 60,
            "is_large_file": file_info["is_large"],
            "recommended_method": file_info["recommended_method"]
        }
    
    def get_memory_usage_info(self) -> dict:
        """
        获取当前内存使用信息
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / (1024 * 1024),  # 实际物理内存使用
                "vms_mb": memory_info.vms / (1024 * 1024),  # 虚拟内存使用
                "percent": process.memory_percent(),         # 内存使用百分比
                "available_mb": psutil.virtual_memory().available / (1024 * 1024)
            }
        except ImportError:
            # 如果没有psutil，返回基础信息
            return {
                "message": "需要安装psutil库获取详细内存信息",
                "max_file_size_mb": self.max_memory_usage / (1024 * 1024)
            }
        except Exception as e:
            return {"error": f"获取内存信息失败: {e}"}
    
    def should_use_streaming(self, file_path: str) -> bool:
        """
        判断是否应该使用流式处理
        """
        file_info = self.get_file_info(file_path)
        return file_info.get("is_large", False)
    
    def optimize_chunk_size(self, file_size: int) -> int:
        """
        根据文件大小优化块大小
        """
        # 小文件使用较小的块
        if file_size < 1024 * 1024:  # 1MB以下
            return min(file_size, 64 * 1024)  # 64KB
        
        # 中等文件
        elif file_size < 10 * 1024 * 1024:  # 10MB以下
            return 256 * 1024  # 256KB
        
        # 大文件使用较大的块
        else:
            return 1024 * 1024  # 1MB