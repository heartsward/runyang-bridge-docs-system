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
        """提取文件内容 - 简化版"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_ext = Path(file_path).suffix.lower()
            
            # 文本文件直接读取
            if file_ext in {'.txt', '.py', '.js', '.html', '.xml', '.yml', '.yaml', '.csv', '.rtf', 
                           '.conf', '.config', '.cfg', '.ini', '.properties', '.env'}:
                content, error = EncodingDetector.read_file_with_encoding(file_path)
                if content is not None:
                    return content
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
            
            # Markdown文件处理
            elif file_ext == '.md':
                content, error = EncodingDetector.read_file_with_encoding(file_path)
                if content is None:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                if markdown:
                    try:
                        html = markdown.markdown(content)
                        text = re.sub(r'<[^>]+>', '', html)
                        return content + "\n\n[纯文本内容]\n" + text
                    except Exception:
                        pass
                return content
            
            # JSON文件格式化读取
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        return json.dumps(data, indent=2, ensure_ascii=False)
                    except json.JSONDecodeError:
                        f.seek(0)
                        return f.read()
            
            # PDF文件处理 - 只使用LibreOffice
            elif file_ext == '.pdf':
                return self._extract_pdf_with_libreoffice_only(file_path)
            
            # Office文档处理 - 只使用LibreOffice转换为TXT
            elif file_ext in {'.xls', '.xlsx', '.doc', '.docx', '.ppt', '.pptx'}:
                # Excel文件检查是否为多工作表
                if file_ext in {'.xls', '.xlsx'}:
                    return self._extract_excel_with_multisheet_support(file_path)
                else:
                    return self._extract_office_with_libreoffice_only(file_path)
            
            # 图片文件处理 - OCR识别
            elif file_ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}:
                return self._extract_image_content_simple(file_path)
            
            return None
                    
        except Exception as e:
            print(f"提取文件内容失败 {file_path}: {str(e)}")
            return None
    
    def _extract_pdf_with_libreoffice_only(self, file_path: str) -> Optional[str]:
        """
        只使用LibreOffice处理PDF文件
        如果LibreOffice无法提取足够文本，则判断为图片PDF并使用OCR
        """
        try:
            print(f"[INFO] 开始PDF文件处理: {file_path}")
            
            # 尝试LibreOffice转换
            libreoffice_content = self._convert_with_libreoffice_simple(file_path)
            if libreoffice_content:
                text_length = len(libreoffice_content.strip())
                word_count = len(libreoffice_content.split())
                
                print(f"[INFO] LibreOffice PDF提取结果: {text_length}字符, {word_count}个词")
                
                # 如果提取到足够的文本内容，直接返回
                if text_length > 100 and word_count > 10:
                    print(f"[SUCCESS] LibreOffice成功提取PDF文本内容")
                    return f"=== PDF文档内容 ===\n\n{libreoffice_content}"
                
                # 如果文本很少，可能是图片PDF，尝试OCR
                print(f"[INFO] PDF文本较少，可能包含图片，尝试OCR识别")
                ocr_content = self._extract_pdf_with_ocr_simple(file_path)
                if ocr_content and len(ocr_content.strip()) > text_length:
                    print(f"[SUCCESS] OCR识别PDF图片内容成功")
                    return f"=== PDF文档内容 (OCR识别) ===\n\n{ocr_content}"
                elif libreoffice_content:
                    return f"=== PDF文档内容 ===\n\n{libreoffice_content}"
            else:
                # LibreOffice完全失败，尝试OCR
                print(f"[INFO] LibreOffice转换失败，尝试OCR识别")
                ocr_content = self._extract_pdf_with_ocr_simple(file_path)
                if ocr_content and len(ocr_content.strip()) > 50:
                    print(f"[SUCCESS] OCR识别PDF内容成功")
                    return f"=== PDF文档内容 (OCR识别) ===\n\n{ocr_content}"
                    
            print(f"[ERROR] PDF内容提取失败")
            return "PDF文件内容提取失败，可能为受保护的PDF或需要安装OCR组件"
            
        except Exception as e:
            print(f"[ERROR] PDF处理异常: {str(e)}")
            return f"PDF处理异常: {str(e)}"
    
    def _extract_office_with_libreoffice_only(self, file_path: str) -> Optional[str]:
        """
        只使用LibreOffice处理Office文档，转换为TXT格式
        Excel文件直接转换为TXT文本，不用CSV
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            print(f"[INFO] 使用LibreOffice处理Office文档: {file_path} ({file_ext})")
            
            content = self._convert_with_libreoffice_simple(file_path)
            if content:
                # 根据文件类型添加标识
                if file_ext in {'.xls', '.xlsx'}:
                    return f"=== Excel表格内容 (TXT格式) ===\n\n{content}"
                elif file_ext in {'.doc', '.docx'}:
                    return f"=== Word文档内容 ===\n\n{content}"
                elif file_ext in {'.ppt', '.pptx'}:
                    return f"=== PowerPoint演示文稿内容 ===\n\n{content}"
                else:
                    return f"=== Office文档内容 ===\n\n{content}"
            else:
                print(f"[ERROR] LibreOffice处理失败")
                return f"LibreOffice处理{file_ext}文件失败"
                
        except Exception as e:
            print(f"[ERROR] Office文档处理异常: {str(e)}")
            return f"Office文档处理异常: {str(e)}"
    
    def _convert_with_libreoffice_simple(self, file_path: str) -> Optional[str]:
        """
        使用LibreOffice转换文件的简化版本
        Excel文件优先使用CSV转换获得更好的表格格式
        """
        try:
            # 检查LibreOffice是否可用
            libreoffice_path = self._find_libreoffice_path()
            if not libreoffice_path:
                print("[WARNING] LibreOffice不可用")
                return None
            
            print(f"[DEBUG] 使用LibreOffice转换: {file_path}")
            file_ext = Path(file_path).suffix.lower()
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建安全的临时文件名（避免中文文件名导致LibreOffice转换失败）
                import uuid
                safe_name = str(uuid.uuid4())
                temp_input_file = os.path.join(temp_dir, f"{safe_name}{file_ext}")
                
                # 复制原文件到临时位置，使用安全文件名
                import shutil
                shutil.copy2(file_path, temp_input_file)
                print(f"[DEBUG] 创建临时文件: {safe_name}{file_ext}")
                
                # Excel文件优先使用CSV转换获得更好的表格格式
                if file_ext in {'.xls', '.xlsx'}:
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--invisible', 
                        '--nologo',
                        '--nofirststartwizard',
                        '--norestore',
                        '--nolockcheck',
                        '--nodefault',
                        '--convert-to', 'csv',
                        '--outdir', temp_dir,
                        temp_input_file
                    ]
                    
                    print(f"[DEBUG] 执行LibreOffice CSV转换")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        csv_file = os.path.join(temp_dir, f"{safe_name}.csv")
                        
                        # 如果精确文件名不存在，搜索临时目录中的csv文件
                        if not os.path.exists(csv_file):
                            csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
                            if csv_files:
                                csv_file = os.path.join(temp_dir, csv_files[0])
                                print(f"[INFO] 使用LibreOffice生成的CSV文件: {csv_files[0]}")
                        
                        if os.path.exists(csv_file):
                            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                                csv_content = f.read().strip()
                            
                            if csv_content:
                                print(f"[SUCCESS] LibreOffice CSV转换成功，内容长度: {len(csv_content)}")
                                # 转换CSV为可读文本格式
                                formatted_content = self._convert_csv_to_readable_text(csv_content)
                                print(f"[INFO] CSV格式化为文本，优化后长度: {len(formatted_content)}")
                                return formatted_content
                            else:
                                print(f"[WARNING] LibreOffice CSV转换文件为空")
                        else:
                            print(f"[WARNING] 未找到CSV转换输出文件: {csv_file}")
                    else:
                        print(f"[ERROR] LibreOffice CSV转换失败，返回码: {result.returncode}")
                        if result.stderr:
                            print(f"[ERROR] CSV转换错误信息: {result.stderr}")
                
                # 非Excel文件或Excel转换失败时，使用HTML转换
                else:
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--invisible', 
                        '--nologo',
                        '--nofirststartwizard',
                        '--norestore',
                        '--nolockcheck',
                        '--nodefault',
                        '--convert-to', 'html',
                        '--outdir', temp_dir,
                        temp_input_file
                    ]
                    
                    print(f"[DEBUG] 执行LibreOffice HTML转换")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        html_file = os.path.join(temp_dir, f"{safe_name}.html")
                        
                        # 如果精确文件名不存在，搜索临时目录中的html文件
                        if not os.path.exists(html_file):
                            html_files = [f for f in os.listdir(temp_dir) if f.endswith('.html')]
                            if html_files:
                                html_file = os.path.join(temp_dir, html_files[0])
                                print(f"[INFO] 使用LibreOffice生成的文件: {html_files[0]}")
                        
                        if os.path.exists(html_file):
                            # 读取HTML文件并清理标签
                            content, error = EncodingDetector.read_file_with_encoding(html_file)
                            if content is None:
                                # 如果检测失败，尝试常见编码
                                encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'windows-1252', 'iso-8859-1']
                                for encoding in encodings_to_try:
                                    try:
                                        with open(html_file, 'r', encoding=encoding, errors='ignore') as f:
                                            content = f.read().strip()
                                        if content:
                                            print(f"[INFO] 使用编码 {encoding} 成功读取文件")
                                            break
                                    except Exception:
                                        continue
                            else:
                                content = content.strip() if content else ''
                            
                            if content:
                                import re
                                
                                # 首先清理CSS样式块和其他不必要内容
                                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                
                                # 然后清理所有HTML标签，获得原始文本
                                text_content = re.sub(r'<[^>]+>', '', content)
                                
                                # 清理多余的空白字符
                                text_content = re.sub(r'[ \t]+', ' ', text_content)
                                text_content = re.sub(r'\n[ \t]*\n', '\n', text_content)
                                text_content = text_content.strip()
                                
                                print(f"[SUCCESS] LibreOffice HTML转换成功，内容长度: {len(text_content)}")
                                return text_content
                            else:
                                print(f"[WARNING] LibreOffice HTML转换文件为空")
                        else:
                            print(f"[WARNING] 未找到HTML转换输出文件: {html_file}")
                    else:
                        print(f"[ERROR] LibreOffice HTML转换失败，返回码: {result.returncode}")
                        if result.stderr:
                            print(f"[ERROR] HTML转换错误信息: {result.stderr}")
                
                return None
                shutil.copy2(file_path, temp_input_file)
                print(f"[DEBUG] 创建临时文件: {safe_name}{file_ext}")
                
                # Excel文件优先使用CSV转换获得更好的表格格式
                if file_ext in {'.xls', '.xlsx'}:
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--invisible', 
                        '--nologo',
                        '--nofirststartwizard',
                        '--norestore',
                        '--nolockcheck',
                        '--nodefault',
                        '--convert-to', 'csv',
                        '--outdir', temp_dir,
                        temp_input_file
                    ]
                else:
                    # 非Excel文件使用HTML格式转换（PDF更兼容），然后清理HTML标签
                    cmd = [
                        libreoffice_path,
                        '--headless',
                        '--invisible', 
                        '--nologo',
                        '--nofirststartwizard',
                        '--norestore',
                        '--nolockcheck',
                        '--nodefault',
                        '--convert-to', 'html',
                        '--outdir', temp_dir,
                        temp_input_file
                    ]
                
                print(f"[DEBUG] 执行LibreOffice转换")
                
                # 执行转换，设置60秒超时
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # Excel文件优先处理CSV转换结果
                    if file_ext in {'.xls', '.xlsx'}:
                        csv_file = os.path.join(temp_dir, f"{safe_name}.csv")
                        
                        # 如果精确文件名不存在，搜索临时目录中的csv文件
                        if not os.path.exists(csv_file):
                            csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
                            if csv_files:
                                csv_file = os.path.join(temp_dir, csv_files[0])
                                print(f"[INFO] 使用LibreOffice生成的CSV文件: {csv_files[0]}")
                        
                        if os.path.exists(csv_file):
                            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                                csv_content = f.read().strip()
                            
                            if csv_content:
                                print(f"[SUCCESS] LibreOffice CSV转换成功，内容长度: {len(csv_content)}")
                                # 转换CSV为可读文本格式
                                formatted_content = self._convert_csv_to_readable_text(csv_content)
                                print(f"[INFO] CSV格式化为文本，优化后长度: {len(formatted_content)}")
                                return formatted_content
                            else:
                                print(f"[WARNING] LibreOffice CSV转换文件为空")
                        else:
                            print(f"[WARNING] 未找到CSV转换输出文件: {csv_file}")
                    else:
                        # 非Excel文件处理HTML转换结果
                        html_file = os.path.join(temp_dir, f"{safe_name}.html")
                        
                        # 如果精确文件名不存在，搜索临时目录中的html文件
                        if not os.path.exists(html_file):
                            html_files = [f for f in os.listdir(temp_dir) if f.endswith('.html')]
                            if html_files:
                                html_file = os.path.join(temp_dir, html_files[0])
                                print(f"[INFO] 使用LibreOffice生成的文件: {html_files[0]}")
                        
                        if os.path.exists(html_file):
                            # 读取HTML文件并清理标签
                            content, error = EncodingDetector.read_file_with_encoding(html_file)
                            if content is None:
                                # 如果检测失败，尝试常见编码
                                encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'windows-1252', 'iso-8859-1']
                                for encoding in encodings_to_try:
                                    try:
                                        with open(html_file, 'r', encoding=encoding, errors='ignore') as f:
                                            content = f.read().strip()
                                        if content:
                                            print(f"[INFO] 使用编码 {encoding} 成功读取文件")
                                            break
                                    except Exception:
                                        continue
                            else:
                                content = content.strip() if content else ''
                            
                            if content:
                                # 针对LibreOffice生成的过度分割HTML内容进行智能处理
                                import re
                                
                                # 首先清理CSS样式块（<style>...</style>）
                                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                
                                # 清理其他不必要的标签内容
                                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
                                
                                # 然后清理所有HTML标签，获得原始文本
                                text_content = re.sub(r'<[^>]+>', '', content)
                                
                                # 清理多余的空白字符
                                text_content = re.sub(r'[ \t]+', ' ', text_content)
                                text_content = re.sub(r'\n[ \t]*\n', '\n', text_content)
                                
                                text_content = text_content.strip()
                                
                                print(f"[SUCCESS] LibreOffice HTML转换成功，内容长度: {len(text_content)}")
                                return text_content
                            else:
                                print(f"[WARNING] LibreOffice HTML转换文件为空")
                        else:
                            print(f"[WARNING] 未找到HTML转换输出文件: {html_file}")
                else:
                    print(f"[INFO] LibreOffice HTML转换失败，返回码: {result.returncode}")
                    if result.stderr:
                        print(f"[DEBUG] HTML转换错误信息: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"[ERROR] LibreOffice转换超时")
            return None
        except Exception as e:
            print(f"[ERROR] LibreOffice转换异常: {str(e)}")
            return None
    
    def _extract_excel_with_multisheet_support(self, file_path: str) -> Optional[str]:
        """
        Excel多工作表支持处理
        """
        try:
            print(f"[INFO] 开始Excel多工作表检测和处理: {file_path}")
            file_extension = file_path.lower().split('.')[-1]
            
            # 检查LibreOffice可用性
            libreoffice_path = self._find_libreoffice_path()
            if not libreoffice_path:
                print(f"[ERROR] LibreOffice未找到")
                return f"LibreOffice处理{file_extension}文件失败"
            
            # 1. 检测工作表结构
            sheet_names = self._detect_sheets_with_libreoffice(file_path)
            
            if not sheet_names:
                # 工作表检测失败，使用单工作表处理
                print("[WARNING] 工作表检测失败，使用单工作表处理")
                return self._extract_office_with_libreoffice_only(file_path)
            
            # 2. 根据工作表数量选择处理策略
            sheet_count = len(sheet_names)
            print(f"[INFO] 检测到 {sheet_count} 个工作表: {sheet_names}")
            
            if sheet_count == 1:
                # 单工作表：使用标准处理
                print("[INFO] 单工作表文件，使用标准处理")
                return self._extract_office_with_libreoffice_only(file_path)
            else:
                # 多工作表：使用多工作表处理
                print(f"[INFO] 多工作表文件，使用多工作表处理")
                result = self._extract_multisheet_with_libreoffice(file_path, sheet_names)
                
                if result and len(result.strip()) > 100:
                    print(f"[SUCCESS] 多工作表处理成功，内容长度: {len(result)}")
                    return result
                else:
                    print("[WARNING] 多工作表处理失败，降级为单工作表处理")
                    fallback_result = self._extract_office_with_libreoffice_only(file_path)
                    if fallback_result:
                        warning_info = f"⚠️ 多工作表处理失败，已降级为单工作表处理（仅显示第一个工作表：{sheet_names[0]}）\n\n"
                        return warning_info + fallback_result
                    else:
                        return f"Excel文件({file_extension})处理失败：多工作表处理和降级处理均失败，共{sheet_count}个工作表"
                        
        except Exception as e:
            print(f"[ERROR] Excel多工作表处理异常: {str(e)}")
            return f"Excel多工作表处理异常: {str(e)}"
    
    def _detect_sheets_with_libreoffice(self, file_path: str) -> List[str]:
        """
        使用LibreOffice检测Excel文件的所有工作表
        """
        try:
            libreoffice_path = self._find_libreoffice_path()
            if not libreoffice_path:
                print("[ERROR] LibreOffice未找到，无法进行工作表检测")
                return []
            
            import tempfile
            import xml.etree.ElementTree as ET
            import zipfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # 转换为ODS格式以获取完整工作表结构
                ods_file = os.path.join(temp_dir, "temp.ods")
                
                cmd = [
                    libreoffice_path,
                    '--headless',
                    '--invisible',
                    '--nologo',
                    '--nofirststartwizard',
                    '--norestore',
                    '--nolockcheck',
                    '--nodefault',
                    '--convert-to', 'ods',
                    '--outdir', temp_dir,
                    os.path.abspath(file_path)
                ]
                
                print(f"[DEBUG] LibreOffice工作表检测: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # 检查生成的ODS文件
                    generated_files = os.listdir(temp_dir)
                    ods_file = None
                    
                    for file in generated_files:
                        if file.endswith('.ods'):
                            ods_file = os.path.join(temp_dir, file)
                            break
                    
                    if ods_file and os.path.exists(ods_file):
                        # 解析ODS文件获取工作表信息
                        sheet_names = self._parse_ods_sheets(ods_file)
                        
                        if sheet_names:
                            print(f"[SUCCESS] LibreOffice检测到 {len(sheet_names)} 个工作表: {sheet_names}")
                            return sheet_names
                        else:
                            print("[WARNING] 未能从ODS文件解析出工作表信息")
                
                return []
                
        except subprocess.TimeoutExpired:
            print("[ERROR] LibreOffice工作表检测超时")
            return []
        except Exception as e:
            print(f"[ERROR] LibreOffice工作表检测异常: {str(e)}")
            return []
    
    def _parse_ods_sheets(self, ods_file: str) -> List[str]:
        """
        解析ODS文件获取工作表名称列表
        """
        try:
            import xml.etree.ElementTree as ET
            import zipfile
            
            sheet_names = []
            
            with zipfile.ZipFile(ods_file, 'r') as zip_ref:
                # ODS文件中的content.xml包含工作表结构信息
                try:
                    content_xml = zip_ref.read('content.xml').decode('utf-8')
                    
                    # 解析XML
                    root = ET.fromstring(content_xml)
                    
                    # 查找所有工作表元素
                    # ODS格式中工作表标签通常为 table:table
                    for elem in root.iter():
                        if elem.tag.endswith('table'):
                            # 获取工作表名称
                            name_attr = None
                            for attr_name, attr_value in elem.attrib.items():
                                if attr_name.endswith('name'):
                                    name_attr = attr_value
                                    break
                            
                            if name_attr and name_attr not in sheet_names:
                                sheet_names.append(name_attr)
                                print(f"[DEBUG] 发现工作表: {name_attr}")
                    
                    # 如果没有找到具名工作表，尝试查找table元素的数量
                    if not sheet_names:
                        table_count = 0
                        for elem in root.iter():
                            if elem.tag.endswith('table'):
                                table_count += 1
                        
                        # 为未命名工作表生成默认名称
                        for i in range(table_count):
                            sheet_names.append(f"Sheet{i+1}")
                        
                        print(f"[DEBUG] 生成默认工作表名称: {sheet_names}")
                        
                except Exception as e:
                    print(f"[ERROR] 解析ODS内容失败: {e}")
                    
            return sheet_names
            
        except Exception as e:
            print(f"[ERROR] 解析ODS文件失败: {e}")
            return []
    
    def _extract_multisheet_with_libreoffice(self, file_path: str, sheet_names: List[str]) -> Optional[str]:
        """
        使用LibreOffice处理多工作表Excel文件
        """
        try:
            print(f"[INFO] 开始LibreOffice多工作表处理，共 {len(sheet_names)} 个工作表")
            
            all_sheets_content = []
            successful_sheets = 0
            
            for sheet_index, sheet_name in enumerate(sheet_names):
                try:
                    print(f"[INFO] 处理工作表 {sheet_index + 1}/{len(sheet_names)}: '{sheet_name}'")
                    
                    # 尝试提取单个工作表
                    sheet_content = self._extract_single_sheet_via_ods(file_path, sheet_name, sheet_index)
                    
                    if sheet_content and len(sheet_content.strip()) > 10:
                        # 格式化工作表内容
                        if len(sheet_names) > 1:
                            formatted_content = f"\n=== 工作表: {sheet_name} ===\n\n{sheet_content}"
                        else:
                            formatted_content = sheet_content
                        
                        all_sheets_content.append(formatted_content)
                        successful_sheets += 1
                        print(f"[SUCCESS] 工作表 '{sheet_name}' 处理成功，内容长度: {len(formatted_content)}")
                    else:
                        print(f"[WARNING] 工作表 '{sheet_name}' 内容为空或处理失败")
                        if len(sheet_names) > 1:
                            all_sheets_content.append(f"\n=== 工作表: {sheet_name} ===\n\n工作表为空或处理失败\n")
                        
                except Exception as e:
                    print(f"[ERROR] 工作表 '{sheet_name}' 处理异常: {str(e)}")
                    if len(sheet_names) > 1:
                        all_sheets_content.append(f"\n=== 工作表: {sheet_name} ===\n\n工作表处理异常: {str(e)}\n")
            
            if all_sheets_content:
                # 生成最终内容
                if len(sheet_names) > 1:
                    summary = f"=== Excel表格内容 (多工作表) ===\n\n包含 {len(sheet_names)} 个工作表，成功处理 {successful_sheets} 个\n"
                    final_content = summary + "\n".join(all_sheets_content)
                else:
                    final_content = f"=== Excel表格内容 ===\n\n{''.join(all_sheets_content)}"
                
                print(f"[SUCCESS] 多工作表处理完成，最终内容长度: {len(final_content)}")
                return final_content
            else:
                print("[ERROR] 所有工作表处理失败")
                return None
                
        except Exception as e:
            print(f"[ERROR] 多工作表处理异常: {str(e)}")
            return None
    
    def _extract_single_sheet_via_ods(self, file_path: str, sheet_name: str, sheet_index: int) -> Optional[str]:
        """
        通过ODS中间格式提取特定工作表
        """
        try:
            libreoffice_path = self._find_libreoffice_path()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # 第一步：转换为ODS
                cmd = [
                    libreoffice_path,
                    '--headless',
                    '--convert-to', 'ods',
                    '--outdir', temp_dir,
                    os.path.abspath(file_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # 查找生成的ODS文件
                    ods_files = [f for f in os.listdir(temp_dir) if f.endswith('.ods')]
                    if ods_files:
                        ods_file = os.path.join(temp_dir, ods_files[0])
                        
                        # 第二步：解析ODS文件提取目标工作表数据
                        return self._parse_sheet_data_from_ods(ods_file, sheet_name, sheet_index)
                
                return None
                
        except Exception as e:
            print(f"[ERROR] 单工作表ODS提取异常: {str(e)}")
            return None
    
    def _parse_sheet_data_from_ods(self, ods_file: str, sheet_name: str, sheet_index: int) -> Optional[str]:
        """
        从ODS文件中解析特定工作表的数据
        """
        try:
            import xml.etree.ElementTree as ET
            import zipfile
            
            with zipfile.ZipFile(ods_file, 'r') as zip_ref:
                content_xml = zip_ref.read('content.xml').decode('utf-8')
                root = ET.fromstring(content_xml)
                
                current_table_index = 0
                target_table = None
                
                # 查找目标工作表
                for elem in root.iter():
                    if elem.tag.endswith('table'):
                        # 获取表格名称
                        table_name = None
                        for attr_name, attr_value in elem.attrib.items():
                            if attr_name.endswith('name'):
                                table_name = attr_value
                                break
                        
                        if not table_name:
                            table_name = f'Sheet{current_table_index + 1}'
                        
                        # 检查是否是目标工作表（按名称或索引匹配）
                        if table_name == sheet_name or current_table_index == sheet_index:
                            print(f"[DEBUG] 找到目标工作表: {table_name} (索引: {current_table_index})")
                            target_table = elem
                            break
                        
                        current_table_index += 1
                
                if target_table is not None:
                    # 提取表格数据
                    csv_rows = []
                    for row_elem in target_table.iter():
                        if row_elem.tag.endswith('table-row'):
                            row_cells = []
                            for cell_elem in row_elem.iter():
                                if cell_elem.tag.endswith('table-cell'):
                                    # 获取单元格文本内容
                                    cell_text = ''.join(cell_elem.itertext()).strip()
                                    row_cells.append(cell_text)
                            
                            if row_cells:  # 只添加非空行
                                csv_rows.append(row_cells)
                    
                    if csv_rows:
                        # 转换为CSV格式然后格式化为可读文本
                        csv_content = '\n'.join([','.join(row) for row in csv_rows])
                        formatted_content = self._convert_csv_to_readable_text(csv_content)
                        print(f"[SUCCESS] 工作表数据解析成功，行数: {len(csv_rows)}")
                        return formatted_content
                    else:
                        print(f"[WARNING] 工作表 '{sheet_name}' 无数据")
                        return None
                else:
                    print(f"[WARNING] 未找到目标工作表: {sheet_name}")
                    return None
                    
        except Exception as e:
            print(f"[ERROR] 解析工作表数据失败: {str(e)}")
            return None
    
    def _extract_pdf_with_ocr_simple(self, file_path: str) -> Optional[str]:
        """
        使用OCR识别PDF中的图片内容的简化版本
        只对被识别为图片的PDF使用OCR
        """
        try:
            print(f"[DEBUG] 尝试使用OCR识别PDF: {file_path}")
            
            # 检查OCR库是否可用
            try:
                import pytesseract
                from PIL import Image
                import pdf2image
            except ImportError as e:
                print(f"[WARNING] OCR库不可用: {e}")
                return None
            
            # 检查Tesseract是否安装
            try:
                pytesseract.get_tesseract_version()
            except:
                print("[WARNING] Tesseract不可用")
                return None
            
            # 将PDF转换为图片（只处理前3页）
            pages = pdf2image.convert_from_path(file_path, dpi=200, first_page=1, last_page=3)
            
            extracted_text = []
            for i, page in enumerate(pages):
                print(f"[DEBUG] OCR识别第{i+1}页")
                
                # 使用OCR识别文本
                text = pytesseract.image_to_string(page, lang='chi_sim+eng', config='--psm 6')
                if text.strip():
                    extracted_text.append(f"--- 第{i+1}页 ---\n{text.strip()}")
            
            if extracted_text:
                result = "\n\n".join(extracted_text)
                print(f"[SUCCESS] OCR识别成功，共{len(pages)}页，文本长度: {len(result)}")
                return result
            else:
                print(f"[WARNING] OCR未识别到文本")
                return None
                
        except Exception as e:
            print(f"[ERROR] PDF OCR处理异常: {str(e)}")
            return None
    
    def _extract_image_content_simple(self, file_path: str) -> Optional[str]:
        """
        使用OCR识别图片文件内容的简化版本
        """
        try:
            print(f"[DEBUG] 尝试使用OCR识别图片: {file_path}")
            
            # 检查OCR库是否可用
            try:
                import pytesseract
                from PIL import Image
            except ImportError as e:
                print(f"[WARNING] OCR库不可用: {e}")
                return None
            
            # 检查Tesseract是否安装
            try:
                pytesseract.get_tesseract_version()
            except:
                print("[WARNING] Tesseract不可用")
                return None
            
            # 打开图片文件
            with Image.open(file_path) as img:
                # 使用OCR识别文本
                text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 6')
                
                if text.strip():
                    print(f"[SUCCESS] 图片OCR识别成功，文本长度: {len(text)}")
                    return f"=== 图片OCR识别内容 ===\n\n{text.strip()}"
                else:
                    print(f"[WARNING] 图片OCR未识别到文本")
                    return "图片OCR未识别到文本内容"
                    
        except Exception as e:
            print(f"[ERROR] 图片OCR处理异常: {str(e)}")
            return f"图片OCR处理异常: {str(e)}"
    
    def _convert_csv_to_readable_text(self, csv_content: str) -> str:
        """
        将CSV内容转换为可读的文本表格格式
        专门用于Excel文件的文本格式化显示
        """
        try:
            import csv
            from io import StringIO
            
            # 解析CSV内容
            csv_reader = csv.reader(StringIO(csv_content))
            rows = list(csv_reader)
            
            if not rows:
                return csv_content
            
            # 计算每列的最大宽度
            col_widths = []
            for row in rows:
                for i, cell in enumerate(row):
                    # 确保col_widths有足够的列
                    while len(col_widths) <= i:
                        col_widths.append(0)
                    
                    # 计算中文字符宽度（中文字符占2个宽度单位）
                    cell_str = str(cell) if cell else ''
                    width = 0
                    for char in cell_str:
                        if '\u4e00' <= char <= '\u9fff':  # 中文字符
                            width += 2
                        else:
                            width += 1
                    
                    col_widths[i] = max(col_widths[i], width)
            
            # 设置合理的列宽限制 - 移除最大宽度限制以保持完整内容
            for i in range(len(col_widths)):
                col_widths[i] = max(col_widths[i], 8)   # 最小8个字符宽度
            
            # 生成表格
            formatted_lines = []
            
            for row_idx, row in enumerate(rows):
                # 生成表格行
                formatted_cells = []
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        cell_str = str(cell) if cell else ''
                        # 计算需要的填充空格
                        cell_width = 0
                        for char in cell_str:
                            if '\u4e00' <= char <= '\u9fff':
                                cell_width += 2
                            else:
                                cell_width += 1
                        
                        # 保持完整内容，不截断长文本
                        padding = max(0, col_widths[i] - cell_width)
                        if padding > 0:
                            cell_str += ' ' * padding
                        
                        formatted_cells.append(cell_str)
                
                # 用4个空格分隔列（确保前端CSS显示正确）
                formatted_lines.append('    '.join(formatted_cells))
            
            # 返回格式化的文本表格
            result = '\n'.join(formatted_lines)
            return result
            
        except Exception as e:
            print(f"[ERROR] CSV转文本格式化失败: {str(e)}")
            # 如果格式化失败，返回原始CSV内容的简单替换版本
            return csv_content.replace(',', '    ')  # 用4个空格替换逗号

    def _find_libreoffice_path(self) -> Optional[str]:
        """查找LibreOffice可执行文件路径"""
        # 常见的LibreOffice路径
        possible_paths = [
            r'C:\Program Files\LibreOffice\program\soffice.exe',      # Windows 64位
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe', # Windows 32位
            '/usr/bin/libreoffice',   # Linux 标准路径
            '/usr/bin/soffice',       # Linux 备用路径
            'soffice'                 # PATH环境变量
        ]
        
        # 快速检查
        for path in possible_paths:
            try:
                if path.startswith('/') or path.startswith('C:'):
                    # 绝对路径检查
                    if os.path.exists(path):
                        return path
                else:
                    # PATH环境变量检查
                    try:
                        subprocess.run([path, '--version'], capture_output=True, timeout=3)
                        return path
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
            except:
                continue
        
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