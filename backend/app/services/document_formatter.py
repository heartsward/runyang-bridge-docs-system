# -*- coding: utf-8 -*-
"""
智能文档格式化器
根据文档类型进行智能排版，提升预览阅读体验
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """文档类型枚举"""
    GENERAL = "general"
    PDF = "pdf" 
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    TECHNICAL = "technical"
    LEGAL = "legal"
    REPORT = "report"
    CODE = "code"

class FormatMode(Enum):
    """格式化模式"""
    ORIGINAL = "original"      # 原始格式
    FORMATTED = "formatted"    # 格式化视图
    COMPACT = "compact"        # 紧凑视图
    STRUCTURED = "structured"  # 结构化视图

class DocumentFormatter:
    """
    智能文档格式化器
    提供多种格式化模式，优化文档预览体验
    """
    
    def __init__(self):
        # 初始化格式化规则
        self._init_formatting_rules()
        
        # 性能统计
        self.stats = {
            "total_formatted": 0,
            "successful_formats": 0,
            "failed_formats": 0,
            "average_processing_time": 0.0
        }
    
    def _init_formatting_rules(self):
        """初始化格式化规则"""
        # 标题识别模式
        self.title_patterns = [
            r'^第[一二三四五六七八九十\d]+章\s+(.+)$',           # 第X章
            r'^第[一二三四五六七八九十\d]+节\s+(.+)$',           # 第X节  
            r'^[一二三四五六七八九十]+、\s*(.+)$',                # 一、二、三、
            r'^[\d]+\.[\d]*\s+(.+)$',                           # 1.1, 2.3等
            r'^[\d]+\.\s+(.+)$',                                # 1. 2. 3.等
            r'^（[一二三四五六七八九十]+）\s*(.+)$',             # （一）（二）等
            r'^[\d]+）\s*(.+)$',                                # 1）2）等
            r'^\s*#+\s+(.+)$',                                  # Markdown标题
        ]
        
        # 列表识别模式
        self.list_patterns = [
            r'^[\s]*[•·▪▫◦‣⁃]\s+(.+)$',                        # 项目符号
            r'^[\s]*[-*+]\s+(.+)$',                             # 破折号列表
            r'^[\s]*[\d]+[\.)]\s+(.+)$',                        # 数字列表
            r'^[\s]*[a-zA-Z][\.)]\s+(.+)$',                     # 字母列表
        ]
        
        # 段落识别规则
        self.paragraph_rules = {
            'min_length': 10,        # 最小段落长度
            'max_line_length': 120,  # 最大行长度
            'indent_threshold': 2,   # 缩进阈值
        }
        
        # 表格识别模式
        self.table_patterns = [
            r'[│┃|]\s*[^│┃|]+\s*[│┃|]',                        # 表格边框
            r'\t[^\t]+\t',                                       # Tab分隔
            r'[^,]+,[^,]+,',                                     # CSV格式
        ]
    
    def format_document(self, 
                       content: str, 
                       doc_type: DocumentType = DocumentType.GENERAL,
                       format_mode: FormatMode = FormatMode.FORMATTED,
                       options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化文档内容
        
        Args:
            content: 原始文档内容
            doc_type: 文档类型
            format_mode: 格式化模式
            options: 格式化选项
            
        Returns:
            格式化结果字典
        """
        import time
        start_time = time.time()
        self.stats["total_formatted"] += 1
        
        try:
            if not content or not content.strip():
                return self._create_empty_result("内容为空")
            
            # 基础选项设置
            default_options = {
                'max_line_length': 100,
                'preserve_whitespace': True,
                'enhance_tables': True,
                'add_navigation': True,
                'highlight_keywords': False
            }
            if options:
                default_options.update(options)
            options = default_options
            
            # 根据模式选择处理策略
            if format_mode == FormatMode.ORIGINAL:
                formatted_content = self._format_original(content)
            elif format_mode == FormatMode.COMPACT:
                formatted_content = self._format_compact(content, doc_type, options)
            elif format_mode == FormatMode.STRUCTURED:
                formatted_content = self._format_structured(content, doc_type, options)
            else:  # FormatMode.FORMATTED (default)
                formatted_content = self._format_enhanced(content, doc_type, options)
            
            # 生成文档结构
            structure = self._analyze_document_structure(formatted_content)
            
            # 统计信息
            processing_time = time.time() - start_time
            self._update_stats(processing_time, True)
            
            result = {
                "original_content": content,
                "formatted_content": formatted_content,
                "document_type": doc_type.value,
                "format_mode": format_mode.value,
                "structure": structure,
                "statistics": {
                    "original_length": len(content),
                    "formatted_length": len(formatted_content),
                    "processing_time": processing_time,
                    "lines_count": len(formatted_content.split('\n')),
                    "paragraphs_count": len(structure.get('paragraphs', [])),
                    "headings_count": len(structure.get('headings', [])),
                    "tables_count": len(structure.get('tables', [])),
                },
                "options_used": options,
                "success": True,
                "error": None
            }
            
            self.stats["successful_formats"] += 1
            return result
            
        except Exception as e:
            self.stats["failed_formats"] += 1
            logger.error(f"文档格式化失败: {str(e)}")
            return self._create_error_result(str(e), content)
    
    def _format_enhanced(self, content: str, doc_type: DocumentType, options: Dict[str, Any]) -> str:
        """增强格式化模式 - 默认推荐模式"""
        # 步骤1: 基础文本清理
        content = self._clean_text(content)
        
        # 步骤2: 根据文档类型进行专门处理
        if doc_type == DocumentType.PDF:
            content = self._format_pdf_content(content, options)
        elif doc_type == DocumentType.WORD:
            content = self._format_word_content(content, options)
        elif doc_type == DocumentType.EXCEL:
            content = self._format_excel_content(content, options)
        elif doc_type == DocumentType.TECHNICAL:
            content = self._format_technical_content(content, options)
        elif doc_type == DocumentType.LEGAL:
            content = self._format_legal_content(content, options)
        elif doc_type == DocumentType.REPORT:
            content = self._format_report_content(content, options)
        else:
            content = self._format_general_content(content, options)
        
        # 步骤3: 通用增强
        content = self._enhance_formatting(content, options)
        
        return content
    
    def _format_pdf_content(self, content: str, options: Dict[str, Any]) -> str:
        """PDF文档专用格式化"""
        lines = content.split('\n')
        formatted_lines = []
        
        current_page = 1
        in_header = False
        in_footer = False
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # 识别页面分隔符
            if line.startswith('[页面') or line.startswith('[第') and '页]' in line:
                formatted_lines.append(f'\n📄 {line}\n' + '─' * 60)
                current_page += 1
                continue
            
            # 识别标题
            if self._is_title_line(line):
                formatted_lines.append(f'\n## {line}\n')
                continue
            
            # 识别列表
            if self._is_list_item(line):
                formatted_lines.append(f'  • {self._clean_list_item(line)}')
                continue
            
            # 普通段落
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_excel_content(self, content: str, options: Dict[str, Any]) -> str:
        """Excel文档专用格式化 - 保持原有表格格式，避免破坏LibreOffice的格式化"""
        # 对于Excel文档，我们的LibreOffice处理器已经生成了高质量的格式化内容
        # 包括Unicode表格边框、完整的分析报告结构等
        # 为了保持这些精心设计的格式，我们避免进一步的格式化处理
        
        # 检查是否包含我们的高质量格式标识
        quality_indicators = [
            'Excel文件完整分析报告' in content,  # 我们的报告标题
            '┌' in content and '│' in content,      # Unicode表格边框
            'LibreOffice处理' in content,           # LibreOffice处理标识
            '工作表导航目录' in content              # 导航结构
        ]
        
        # 如果包含高质量格式标识，直接返回，避免任何破坏
        if any(quality_indicators):
            return content
        
        # 只有在内容质量不佳时才进行基础格式化
        return content
    
    def _format_word_content(self, content: str, options: Dict[str, Any]) -> str:
        """Word文档专用格式化"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # 标题处理
            if self._is_title_line(line):
                level = self._get_title_level(line)
                if level == 1:
                    formatted_lines.append(f'\n# {line}\n')
                elif level == 2:
                    formatted_lines.append(f'\n## {line}\n')
                elif level == 3:
                    formatted_lines.append(f'\n### {line}\n')
                else:
                    formatted_lines.append(f'\n#### {line}\n')
                continue
            
            # 列表处理
            if self._is_list_item(line):
                indent_level = self._get_list_indent_level(line)
                indent = '  ' * indent_level
                formatted_lines.append(f'{indent}• {self._clean_list_item(line)}')
                continue
            
            # 普通段落
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_technical_content(self, content: str, options: Dict[str, Any]) -> str:
        """技术文档专用格式化"""
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            # 代码块识别
            if self._is_code_line(line):
                if not in_code_block:
                    formatted_lines.append('```')
                    in_code_block = True
                formatted_lines.append(original_line)  # 保持原始缩进
                continue
            
            if in_code_block and (not line or self._is_text_line(line)):
                in_code_block = False
                formatted_lines.append('```\n')
            
            # API或配置项
            if self._is_api_line(line):
                formatted_lines.append(f'🔧 **{line}**')
                continue
            
            # 技术术语高亮
            line = self._highlight_technical_terms(line)
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_legal_content(self, content: str, options: Dict[str, Any]) -> str:
        """法律文档专用格式化"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # 条款编号
            if self._is_legal_clause(line):
                formatted_lines.append(f'\n⚖️ **{line}**\n')
                continue
            
            # 法律术语标识
            line = self._highlight_legal_terms(line)
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_general_content(self, content: str, options: Dict[str, Any]) -> str:
        """通用文档格式化"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # 标题识别
            if self._is_title_line(line):
                formatted_lines.append(f'## {line}')
                formatted_lines.append('─' * min(40, len(line)))
                continue
            
            # 列表识别
            if self._is_list_item(line):
                formatted_lines.append(f'• {self._clean_list_item(line)}')
                continue
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_structured(self, content: str, doc_type: DocumentType, options: Dict[str, Any]) -> str:
        """结构化格式模式 - 生成文档大纲和结构化视图"""
        # 先进行增强格式化
        enhanced_content = self._format_enhanced(content, doc_type, options)
        
        # 生成结构化视图
        structure = self._analyze_document_structure(enhanced_content)
        
        # 构建结构化输出
        structured_parts = []
        
        # 文档概览
        structured_parts.append("📋 文档结构概览")
        structured_parts.append("=" * 30)
        
        # 添加统计信息
        stats = [
            f"📄 总字符数: {len(content):,}",
            f"📝 段落数量: {len(structure.get('paragraphs', []))}",
            f"📑 标题数量: {len(structure.get('headings', []))}",
            f"📊 表格数量: {len(structure.get('tables', []))}",
            f"📋 列表数量: {len(structure.get('lists', []))}"
        ]
        structured_parts.extend(stats)
        structured_parts.append("")
        
        # 标题大纲
        headings = structure.get('headings', [])
        if headings:
            structured_parts.append("🗂️ 文档大纲")
            structured_parts.append("-" * 20)
            for i, heading in enumerate(headings, 1):
                level = heading.get('level', 1)
                indent = '  ' * (level - 1)
                structured_parts.append(f"{indent}{i}. {heading.get('text', '')}")
            structured_parts.append("")
        
        # 完整内容
        structured_parts.append("📖 完整内容")
        structured_parts.append("=" * 30)
        structured_parts.append(enhanced_content)
        
        return '\n'.join(structured_parts)
    
    def _format_compact(self, content: str, doc_type: DocumentType, options: Dict[str, Any]) -> str:
        """紧凑格式模式 - 移除多余空白，提高信息密度"""
        # 基础清理
        content = self._clean_text(content)
        
        # 移除多余空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 合并短行
        lines = content.split('\n')
        merged_lines = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged_lines.append('')
                continue
            
            # 如果是标题或列表项，单独成行
            if self._is_title_line(line) or self._is_list_item(line):
                if current_paragraph:
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged_lines.append(line)
                continue
            
            # 短行合并到段落
            if len(line) < 80 and not self._is_standalone_line(line):
                current_paragraph.append(line)
            else:
                if current_paragraph:
                    merged_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged_lines.append(line)
        
        # 处理最后的段落
        if current_paragraph:
            merged_lines.append(' '.join(current_paragraph))
        
        return '\n'.join(merged_lines)
    
    def _format_original(self, content: str) -> str:
        """原始格式模式 - 最小化处理，保持原貌"""
        # 只进行基本的编码清理
        return content.strip()
    
    def _enhance_formatting(self, content: str, options: Dict[str, Any]) -> str:
        """通用格式增强"""
        if not options.get('preserve_whitespace', True):
            # 清理多余空白
            content = re.sub(r'[ \t]+', ' ', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 添加导航链接（如果需要）
        if options.get('add_navigation', False):
            content = self._add_navigation_links(content)
        
        return content
    
    def _analyze_document_structure(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """分析文档结构"""
        structure = {
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'tables': [],
            'code_blocks': []
        }
        
        lines = content.split('\n')
        current_line_num = 0
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 标题检测
            if self._is_title_line(line_stripped):
                structure['headings'].append({
                    'text': line_stripped,
                    'level': self._get_title_level(line_stripped),
                    'line_number': line_num + 1
                })
                continue
            
            # 列表检测
            if self._is_list_item(line_stripped):
                structure['lists'].append({
                    'text': self._clean_list_item(line_stripped),
                    'indent_level': self._get_list_indent_level(line),
                    'line_number': line_num + 1
                })
                continue
            
            # 表格检测
            if self._is_table_content(line_stripped):
                structure['tables'].append({
                    'text': line_stripped,
                    'line_number': line_num + 1
                })
                continue
            
            # 代码块检测
            if self._is_code_line(line_stripped):
                structure['code_blocks'].append({
                    'text': line_stripped,
                    'line_number': line_num + 1
                })
                continue
            
            # 普通段落
            if len(line_stripped) > 10:  # 忽略太短的行
                structure['paragraphs'].append({
                    'text': line_stripped[:100] + ('...' if len(line_stripped) > 100 else ''),
                    'length': len(line_stripped),
                    'line_number': line_num + 1
                })
        
        return structure
    
    # 辅助方法
    def _is_title_line(self, line: str) -> bool:
        """检测是否为标题行"""
        for pattern in self.title_patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _get_title_level(self, line: str) -> int:
        """获取标题级别"""
        if re.match(r'^第[一二三四五六七八九十\d]+章', line):
            return 1
        elif re.match(r'^第[一二三四五六七八九十\d]+节', line):
            return 2
        elif re.match(r'^[一二三四五六七八九十]+、', line):
            return 2
        elif re.match(r'^[\d]+\.[\d]+', line):
            return 3
        elif re.match(r'^[\d]+\.', line):
            return 2
        elif re.match(r'^（[一二三四五六七八九十]+）', line):
            return 3
        elif re.match(r'^#+', line):
            return line.count('#')
        return 2
    
    def _is_list_item(self, line: str) -> bool:
        """检测是否为列表项"""
        for pattern in self.list_patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _clean_list_item(self, line: str) -> str:
        """清理列表项，移除标记符号"""
        for pattern in self.list_patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        return line
    
    def _get_list_indent_level(self, line: str) -> int:
        """获取列表缩进级别"""
        leading_spaces = len(line) - len(line.lstrip())
        return leading_spaces // 4  # 假设每级缩进4个空格
    
    def _is_table_content(self, line: str) -> bool:
        """检测是否为表格内容"""
        for pattern in self.table_patterns:
            if re.search(pattern, line):
                return True
        
        # 额外检测：多个分隔符
        separators = ['|', '│', '\t', '  ']
        separator_count = sum(line.count(sep) for sep in separators)
        return separator_count >= 2
    
    def _is_code_line(self, line: str) -> bool:
        """检测是否为代码行"""
        code_indicators = [
            line.strip().startswith(('def ', 'class ', 'import ', 'from ')),
            re.match(r'^\s*[a-zA-Z_]\w*\s*[:=]', line),
            re.match(r'^\s*[{}()\[\]<>]', line),
            line.count('{') + line.count('}') + line.count('(') + line.count(')') >= 2
        ]
        return any(code_indicators)
    
    def _is_text_line(self, line: str) -> bool:
        """检测是否为普通文本行"""
        return not self._is_code_line(line) and len(line.strip()) > 0
    
    def _is_api_line(self, line: str) -> bool:
        """检测是否为API相关行"""
        api_patterns = [
            r'GET|POST|PUT|DELETE|PATCH',
            r'/api/',
            r'http[s]?://',
            r'@\w+',  # 注解
            r'def \w+\(',  # 函数定义
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in api_patterns)
    
    def _is_legal_clause(self, line: str) -> bool:
        """检测是否为法律条款"""
        legal_patterns = [
            r'^第[一二三四五六七八九十\d]+条',
            r'^第[一二三四五六七八九十\d]+款',
            r'^第[一二三四五六七八九十\d]+项',
            r'^[一二三四五六七八九十]+、.*[规定|办法|条例|法|规]'
        ]
        return any(re.match(pattern, line) for pattern in legal_patterns)
    
    def _is_standalone_line(self, line: str) -> bool:
        """检测是否为独立行（不应该合并的行）"""
        standalone_indicators = [
            self._is_title_line(line),
            self._is_list_item(line),
            self._is_table_content(line),
            line.endswith('：') or line.endswith(':'),
            line.startswith('注：') or line.startswith('备注：'),
            len(line) > 100  # 长行保持独立
        ]
        return any(standalone_indicators)
    
    def _highlight_technical_terms(self, line: str) -> str:
        """高亮技术术语"""
        tech_terms = [
            'API', 'HTTP', 'HTTPS', 'JSON', 'XML', 'SQL', 'URL', 'URI',
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
            '配置', '参数', '接口', '协议', '算法', '数据库'
        ]
        
        for term in tech_terms:
            line = re.sub(f'\\b{term}\\b', f'`{term}`', line, flags=re.IGNORECASE)
        
        return line
    
    def _highlight_legal_terms(self, line: str) -> str:
        """高亮法律术语"""
        legal_terms = [
            '法律', '法规', '条例', '办法', '规定', '通知', '公告',
            '应当', '必须', '禁止', '不得', '违反', '责任', '义务', '权利'
        ]
        
        for term in legal_terms:
            if term in line:
                line = line.replace(term, f'**{term}**')
        
        return line
    
    def _add_navigation_links(self, content: str) -> str:
        """添加导航链接"""
        # 简单实现：在每个标题前添加锚点
        lines = content.split('\n')
        result_lines = []
        
        for line in lines:
            if self._is_title_line(line.strip()):
                # 生成锚点ID
                anchor_id = re.sub(r'[^\w\s-]', '', line.strip()).replace(' ', '-').lower()
                result_lines.append(f'<a name="{anchor_id}"></a>')
                result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _clean_text(self, text: str) -> str:
        """基础文本清理 - 保护表格边框字符"""
        # 检查是否包含精心格式化的表格内容
        if '┌' in text or '│' in text or '└' in text:
            # 如果包含Unicode表格边框，只做最小清理，避免破坏格式
            # 只清理明显的垃圾字符，保留所有表格相关字符
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)  # 只移除控制字符
            text = re.sub(r'\n[ \t]+\n', '\n\n', text)  # 清理空白行
            return text.strip()
        
        # 对于没有表格格式的普通文本进行常规清理
        # 添加Unicode表格边框字符到允许列表
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u2500-\u257f.,;:!?()\[\]{}\"\'\-=+*/<>@#$%^&~`|\\]', ' ', text)
        
        # 清理多余空白
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'\n[ \t]+', '\n', text)
        
        return text.strip()
    
    def _update_stats(self, processing_time: float, success: bool):
        """更新性能统计"""
        if success:
            old_avg = self.stats["average_processing_time"]
            old_count = self.stats["successful_formats"]
            if old_count > 0:
                self.stats["average_processing_time"] = (old_avg * (old_count - 1) + processing_time) / old_count
            else:
                self.stats["average_processing_time"] = processing_time
    
    def _create_empty_result(self, message: str) -> Dict[str, Any]:
        """创建空结果"""
        return {
            "original_content": "",
            "formatted_content": "",
            "document_type": DocumentType.GENERAL.value,
            "format_mode": FormatMode.ORIGINAL.value,
            "structure": {},
            "statistics": {},
            "options_used": {},
            "success": False,
            "error": message
        }
    
    def _create_error_result(self, error: str, original_content: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "original_content": original_content,
            "formatted_content": original_content,  # 失败时返回原内容
            "document_type": DocumentType.GENERAL.value,
            "format_mode": FormatMode.ORIGINAL.value,
            "structure": {},
            "statistics": {"error": error},
            "options_used": {},
            "success": False,
            "error": error
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total = self.stats["total_formatted"]
        return {
            **self.stats,
            "success_rate": (self.stats["successful_formats"] / total * 100) if total > 0 else 0,
            "failure_rate": (self.stats["failed_formats"] / total * 100) if total > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_formatted": 0,
            "successful_formats": 0,
            "failed_formats": 0,
            "average_processing_time": 0.0
        }