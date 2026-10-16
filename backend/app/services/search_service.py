# -*- coding: utf-8 -*-
"""
搜索服务 - 简化版

文件内容提取统一委托 ExtractionRouter（阶段十九：anydoc 首选引擎
+ 本地引擎安全网 + 多模态 AI 兜底）；只有图片/扫描件走 OCR/多模态 AI。
"""
import os
import re
import json
import html as html_lib
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

    def search_terms_in_text(
        self,
        text: str,
        terms: List[str],
        max_matches_per_term: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """多词联合搜索：一次遍历文本，同时匹配所有词（阶段二十·20.2）

        与 search_in_text 的差异：
        - 输入为词列表（已分词），单次逐行遍历完成全部词的匹配
        - 返回 {term: [match, ...]}，每词最多 max_matches_per_term 条
        - 某词零匹配时其值为空列表（调用方可据此判断命中词数）
        """
        if not text or not terms:
            return {t: [] for t in terms}

        # 预编译所有词的正则（去重，避免重复编译）
        unique_terms = list(dict.fromkeys(terms))
        patterns = {t: re.compile(re.escape(t), re.IGNORECASE) for t in unique_terms}

        results: Dict[str, List[Dict[str, Any]]] = {t: [] for t in unique_terms}
        done = set()

        for line_num, line in enumerate(text.split('\n'), 1):
            for term, pattern in patterns.items():
                if term in done:
                    continue
                if pattern.search(line):
                    results[term].append({
                        'line_number': line_num,
                        'content': line.strip(),
                        'keyword': term,
                    })
                    if len(results[term]) >= max_matches_per_term:
                        done.add(term)
            if len(done) == len(patterns):
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

    def highlight_terms(self, text: str, terms: List[str]) -> str:
        """多词联合高亮：每个命中词注入 <mark data-term="词">（阶段二十·20.5）

        - 长词优先，避免短词先吞掉长词（"交换机" 不会拆掉 "核心交换机"）
        - 大小写不敏感；重叠区间去重
        - mark 带 data-term 属性，供前端按词分组做分别导航
        - 29.3：**markdown 链接保护**——`[text](url)` 的 text 段正常高亮，URL 段完全跳过
          （避免 `href="#xxx<mark>...</mark>"` 破坏 markdown 链接语法，导致浏览器 native 跳转失效）
        - 29.6/29.8：**代码块 / 行内代码 段**用 sentinel 占位符（`@@HL@@<idx>@@<term>@@<text>@@HLEND@@`）
          替代 `<mark>` 标签插入——markdown-it 渲染 fenced code 时会 escape `<` `>` 为 `&lt;` `&gt;` 字面字符，
          直接插入 `<mark>` 会被 escape 成 `&lt;mark&gt;` 字面显示；sentinel 是不含 markdown 特殊字符
          的纯 ASCII 字符串，markdown-it 不解析（**关键**：`__` `**` 会被 markdown-it 当 bold delimiter
          配对破坏 sentinel 结构，用 `@@` 分隔避开），前端 markdown-it 渲染**之后**再做 sentinel→mark 还原
          （在 `sanitizeDocumentHtml` 内部统一处理）——实现"代码块内也高亮" + "不显示字面 <mark>"
        - 29.7：**完整 q 串整体高亮**——若多词查询的完整 `q.strip()` 串在原文中连续出现，
          把整段作为**单一** mark 插入（不按分词拆开），实现陈工期望的"ufw allow from" 3 词一个高亮块
        """
        if not text or not terms:
            return text
        unique_terms = list(dict.fromkeys(t for t in terms if t))
        if not unique_terms:
            return text

        # 29.3 + 29.6/29.8：识别"不可高亮区"——但 code 段从"完全跳过"改为"用 sentinel 插入"
        # 这样代码块内也能高亮(29.8 修陈工"代码块内连续词不被识别"问题)
        md_link_url_ranges: List[tuple] = []  # 链接 URL 段:仍完全跳过
        code_ranges: List[tuple] = []  # 代码块 + inline code:用 sentinel

        # 29.3：markdown 链接 `[text](url)` 的 URL 段
        md_link_pattern = re.compile(r'(!?)\[([^\]]*)\]\(([^)]*)\)')
        for m in md_link_pattern.finditer(text):
            md_link_url_ranges.append((m.start(3), m.end(3)))

        # 29.6/29.8：fenced code block
        fence_re = re.compile(r'(?:```|~~~)[^\n]*\n.*?\n(?:```|~~~)', re.DOTALL)
        for m in fence_re.finditer(text):
            code_ranges.append((m.start(), m.end()))

        # 29.6/29.8：inline code
        inline_code_re = re.compile(r'`[^`\n]+`')
        for m in inline_code_re.finditer(text):
            if any(not (m.end() <= s or m.start() >= e) for s, e in code_ranges):
                continue
            code_ranges.append((m.start(), m.end()))

        # 29.7：完整 q 串作为"长 term"加入，长词优先命中
        all_terms = list(unique_terms)
        if len(unique_terms) >= 2:
            phrase = ' '.join(unique_terms)
            if phrase not in all_terms and phrase.strip():
                all_terms.append(phrase)

        # 长词优先 + 按位置去重
        ordered = sorted(all_terms, key=len, reverse=True)
        patterns = [(t, re.compile(re.escape(t), re.IGNORECASE)) for t in ordered]
        taken: List[tuple] = []
        for term, pattern in patterns:
            for m in pattern.finditer(text):
                start, end = m.start(), m.end()
                if not m.group():
                    continue
                # 链接 URL 段:完全跳过(保护 markdown 链接语法)
                if any(not (end <= s or start >= e) for s, e in md_link_url_ranges):
                    continue
                # 已占用的区间去重
                if any(not (end <= s or start >= e) for s, e in taken):
                    continue
                taken.append((start, end))
        # 重新按位置输出：分段输出
        taken.sort()
        out: List[str] = []
        pos = 0
        sentinel_idx = 0
        for start, end in taken:
            out.append(text[pos:start])
            matched_text = text[start:end]
            in_code = any(not (end <= s or start >= e) for s, e in code_ranges)
            if in_code:
                # 29.8 修:代码块/inline code 段用 @@ 分隔的 sentinel(避开 markdown 的 __** delimiter)
                # 前端 markdown-it 渲染后,字符串里是 <pre><code>@@HL@@<idx>@@<term>@@<text>@@HLEND@@</code></pre>
                # 还原在 sanitizeDocumentHtml 内部统一处理
                # 属性值做 HTML 转义(虽然 sentinel 不含特殊字符,但保险起见)
                term_attr = html_lib.escape(matched_text.lower(), quote=True)
                out.append(f"@@HL@@{sentinel_idx}@@{term_attr}@@{matched_text}@@HLEND@@")
                sentinel_idx += 1
            else:
                # 普通段:用 <mark>
                term_attr = html_lib.escape(matched_text.lower(), quote=True)
                out.append(f'<mark data-term="{term_attr}">{matched_text}</mark>')
            pos = end
        out.append(text[pos:])
        return ''.join(out)

    @staticmethod
    def _find_all_occurrences(text: str, patterns: list) -> List[tuple]:
        """返回 [(start, end), ...]，按起点排序"""
        found: List[tuple] = []
        for term, pattern in patterns:
            for m in pattern.finditer(text):
                if m.group():
                    found.append((m.start(), m.end()))
        found.sort()
        return found

    def highlight_phrase(self, text: str, phrase: str) -> str:
        """29.9：完整 q 串整体高亮——只在 phrase 连续出现的位置插 mark,不重复按分词插

        与 highlight_terms 的差异:
        - highlight_terms 接受多个 term(分词),长词优先 + 按位置去重
        - highlight_phrase **只**接受 1 个 phrase,严格只插 phrase 命中的位置
        - 用于"完整 q 串在文档里连续出现"的场景——预览里只有 N 个整段 mark
        - 前端 ↑↓ 在整段之间跳(陈工期望的"整词上下选择"导航)

        复用 29.6/29.8 保护:
        - 链接 URL 段:原样(避免破坏 markdown 链接语法)
        - 代码块/inline code 段:用 sentinel 占位符(前端 markdown-it 渲染后还原为真 <mark>)
        - 普通段:<mark> 标签
        """
        if not text or not phrase:
            return text

        # 收集"不可高亮区":链接 URL 段、fenced code 段、inline code 段
        link_url_ranges: List[tuple] = []
        code_ranges: List[tuple] = []
        md_link_pattern = re.compile(r'(!?)\[([^\]]*)\]\(([^)]*)\)')
        for m in md_link_pattern.finditer(text):
            link_url_ranges.append((m.start(3), m.end(3)))
        fence_re = re.compile(r'(?:```|~~~)[^\n]*\n.*?\n(?:```|~~~)', re.DOTALL)
        for m in fence_re.finditer(text):
            code_ranges.append((m.start(), m.end()))
        inline_code_re = re.compile(r'`[^`\n]+`')
        for m in inline_code_re.finditer(text):
            if any(not (m.end() <= s or m.start() >= e) for s, e in code_ranges):
                continue
            code_ranges.append((m.start(), m.end()))  # 29.9:inline code 也算 code 段

        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        out: List[str] = []
        pos = 0
        sentinel_idx = 0
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            in_link_url = any(not (end <= s or start >= e) for s, e in link_url_ranges)
            if in_link_url:
                # 链接 URL 段:跳过(保护 markdown 链接语法)
                continue
            in_code = any(not (end <= s or start >= e) for s, e in code_ranges)
            out.append(text[pos:start])
            matched_text = text[start:end]
            term_attr = html_lib.escape(matched_text.lower(), quote=True)
            if in_code:
                # 29.8/29.9:代码块/inline code 段用 sentinel 占位符(避免 markdown-it escape)
                out.append(f"@@HL@@{sentinel_idx}@@{term_attr}@@{matched_text}@@HLEND@@")
                sentinel_idx += 1
            else:
                # 普通段:用 <mark>
                out.append(f'<mark data-term="{term_attr}">{matched_text}</mark>')
            pos = end
        out.append(text[pos:])
        return ''.join(out)
    
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