# -*- coding: utf-8 -*-
"""
智能文本处理器 - 文本矫正和格式结构恢复
优化OCR结果，恢复文档原始格式和结构
"""
import os
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class SmartTextProcessor:
    """
    智能文本处理器
    - OCR错误自动修正
    - 文档结构识别和恢复  
    - 格式标准化
    - 质量评估
    """
    
    def __init__(self):
        # 文本处理配置
        self.config = {
            "min_line_length": 5,       # 最小行长度
            "max_line_length": 200,     # 最大行长度  
            "paragraph_break_ratio": 0.6, # 段落分割比例
            "title_indicators": ["第", "章", "节", "条", "款", "项"],  # 标题指示词
            "list_indicators": ["1.", "2.", "3.", "一、", "二、", "三、", "（一）", "（二）"],  # 列表指示词
        }
        
        # 加载常见错误字典
        self.error_corrections = self._load_ocr_corrections()
        
        # 文档结构模式
        self.structure_patterns = self._compile_structure_patterns()
    
    def process_extracted_text(self, raw_text: str, doc_type: str = "general") -> Dict[str, Any]:
        """
        处理提取的文本
        
        Args:
            raw_text: 原始提取的文本
            doc_type: 文档类型 (general, legal, technical, report)
            
        Returns:
            处理结果字典
        """
        result = {
            "original_text": raw_text,
            "processed_text": "",
            "structure": {},
            "corrections_applied": 0,
            "quality_score": 0.0,
            "processing_steps": [],
            "warnings": []
        }
        
        if not raw_text or not raw_text.strip():
            result["warnings"].append("输入文本为空")
            return result
        
        try:
            # 步骤1: 基础清理
            text = self._basic_text_cleanup(raw_text)
            result["processing_steps"].append("基础文本清理")
            
            # 步骤2: OCR错误修正
            text, corrections = self._correct_ocr_errors(text, doc_type)
            result["corrections_applied"] = corrections
            result["processing_steps"].append(f"OCR错误修正 ({corrections}处)")
            
            # 步骤3: 格式标准化
            text = self._standardize_formatting(text)
            result["processing_steps"].append("格式标准化")
            
            # 步骤4: 结构识别
            structure = self._analyze_document_structure(text)
            result["structure"] = structure
            result["processing_steps"].append("文档结构分析")
            
            # 步骤5: 结构恢复
            text = self._restore_document_structure(text, structure)
            result["processing_steps"].append("文档结构恢复")
            
            # 步骤6: 最终优化
            text = self._final_text_optimization(text, doc_type)
            result["processing_steps"].append("最终文本优化")
            
            # 步骤7: 质量评估
            quality_score = self._evaluate_text_quality(text, raw_text)
            result["quality_score"] = quality_score
            result["processing_steps"].append(f"质量评估 ({quality_score:.1f}分)")
            
            result["processed_text"] = text
            
            logger.info(f"文本处理完成: 原文长度={len(raw_text)}, 处理后长度={len(text)}, 质量评分={quality_score:.1f}")
            
        except Exception as e:
            error_msg = f"文本处理失败: {str(e)}"
            logger.error(error_msg)
            result["warnings"].append(error_msg)
            result["processed_text"] = raw_text  # 返回原文
        
        return result
    
    def _basic_text_cleanup(self, text: str) -> str:
        """
        基础文本清理
        """
        if not text:
            return ""
        
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除不可见字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 规范化空白字符
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符合并
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行符合并
        
        # 移除行首行尾空白
        lines = []
        for line in text.split('\n'):
            cleaned_line = line.strip()
            lines.append(cleaned_line)
        
        return '\n'.join(lines)
    
    def _correct_ocr_errors(self, text: str, doc_type: str) -> Tuple[str, int]:
        """
        修正OCR错误
        """
        corrections_count = 0
        
        try:
            # 应用通用错误修正
            for wrong, correct in self.error_corrections["general"].items():
                if wrong in text:
                    old_text = text
                    text = text.replace(wrong, correct)
                    if text != old_text:
                        corrections_count += text.count(correct) - old_text.count(correct)
            
            # 应用文档类型特定的修正
            if doc_type in self.error_corrections:
                for wrong, correct in self.error_corrections[doc_type].items():
                    if wrong in text:
                        old_text = text
                        text = text.replace(wrong, correct)
                        if text != old_text:
                            corrections_count += 1
            
            # 智能上下文修正
            text, context_corrections = self._context_based_corrections(text)
            corrections_count += context_corrections
            
        except Exception as e:
            logger.warning(f"OCR错误修正失败: {e}")
        
        return text, corrections_count
    
    def _context_based_corrections(self, text: str) -> Tuple[str, int]:
        """
        基于上下文的智能修正
        """
        corrections = 0
        
        try:
            # 数字序列修正
            # 例如: "第1章" 不应该是 "第l章"
            number_patterns = [
                (r'第[Il|l]([0-9])', r'第\1'),  # 第l1章 -> 第1章
                (r'([0-9])[Il|l]([0-9])', r'\1\2'),  # 2l3 -> 23
                (r'([0-9])[O]([0-9])', r'\1o\2'),   # 2O3 -> 2o3 或 203
            ]
            
            for pattern, replacement in number_patterns:
                old_text = text
                text = re.sub(pattern, replacement, text)
                if text != old_text:
                    corrections += 1
            
            # 常见词汇修正
            common_words_corrections = [
                (r'公巳', '公司'),
                (r'有限公巳', '有限公司'),
                (r'档案馆', '档案馆'),
                (r'文档管理', '文档管理'),
                (r'系统', '系统'),
                (r'通知', '通知'),
                (r'关于', '关于'),
                (r'根据', '根据'),
                (r'要求', '要求'),
                (r'规定', '规定'),
                (r'办法', '办法'),
                (r'实施', '实施'),
                (r'管理', '管理'),
                (r'工作', '工作'),
                (r'安全', '安全'),
                (r'网络', '网络'),
                (r'数据', '数据'),
                (r'检查', '检查'),
                (r'监督', '监督')
            ]
            
            for pattern, replacement in common_words_corrections:
                if pattern in text and replacement not in text:
                    old_text = text
                    text = text.replace(pattern, replacement)
                    if text != old_text:
                        corrections += 1
            
        except Exception as e:
            logger.warning(f"上下文修正失败: {e}")
        
        return text, corrections
    
    def _standardize_formatting(self, text: str) -> str:
        """
        标准化格式
        """
        try:
            # 标准化标点符号
            punctuation_corrections = {
                # 中文标点
                ',': '，',
                ';': '；', 
                ':': '：',
                '!': '！',
                '?': '？',
                
                # 括号配对
                '(': '（',
                ')': '）',
                '[': '［',
                ']': '］',
            }
            
            # 只在中文环境中应用
            for eng, chn in punctuation_corrections.items():
                # 检查前后是否有中文字符
                pattern = f'([\u4e00-\u9fff]){re.escape(eng)}([\u4e00-\u9fff])'
                replacement = f'\\1{chn}\\2'
                text = re.sub(pattern, replacement, text)
            
            # 数字格式标准化
            text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)  # 保持小数点格式
            text = re.sub(r'(\d+),(\d{3})', r'\1，\2', text)  # 千分位逗号
            
            # 日期格式标准化
            date_patterns = [
                (r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1年\2月\3日'),
                (r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1年\2月\3日'),
                (r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\1年\2月\3日')
            ]
            
            for pattern, replacement in date_patterns:
                text = re.sub(pattern, replacement, text)
            
        except Exception as e:
            logger.warning(f"格式标准化失败: {e}")
        
        return text
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """
        分析文档结构
        """
        structure = {
            "type": "unknown",
            "sections": [],
            "paragraphs": 0,
            "lists": [],
            "tables": 0,
            "has_title": False,
            "title": "",
            "hierarchy_levels": 0
        }
        
        try:
            lines = text.split('\n')
            current_section = None
            paragraph_count = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 检测标题
                if self._is_title_line(line):
                    if not structure["has_title"]:
                        structure["has_title"] = True
                        structure["title"] = line
                    
                    current_section = {
                        "title": line,
                        "start_line": i,
                        "content_lines": 0,
                        "level": self._get_title_level(line)
                    }
                    structure["sections"].append(current_section)
                    continue
                
                # 检测列表项
                if self._is_list_item(line):
                    list_item = {
                        "content": line,
                        "line_number": i,
                        "type": self._get_list_type(line)
                    }
                    structure["lists"].append(list_item)
                    continue
                
                # 检测表格行
                if self._is_table_row(line):
                    structure["tables"] += 1
                    continue
                
                # 普通段落
                if len(line) > self.config["min_line_length"]:
                    paragraph_count += 1
                    if current_section:
                        current_section["content_lines"] += 1
            
            structure["paragraphs"] = paragraph_count
            structure["hierarchy_levels"] = len(set(s.get("level", 0) for s in structure["sections"]))
            
            # 判断文档类型
            if structure["sections"] and structure["lists"]:
                if any("第" in s["title"] for s in structure["sections"]):
                    structure["type"] = "legal"
                elif any("章" in s["title"] for s in structure["sections"]):
                    structure["type"] = "report"
                else:
                    structure["type"] = "structured"
            elif structure["paragraphs"] > 10:
                structure["type"] = "article"
            else:
                structure["type"] = "simple"
            
        except Exception as e:
            logger.warning(f"文档结构分析失败: {e}")
        
        return structure
    
    def _is_title_line(self, line: str) -> bool:
        """
        判断是否为标题行
        """
        if not line or len(line) < 2:
            return False
        
        # 标题特征
        title_patterns = [
            r'^第[一二三四五六七八九十\d]+[章节条款]',  # 第X章、第X节等
            r'^[一二三四五六七八九十]、',              # 一、二、等
            r'^\d+\.?\s*[^\d]',                     # 1. 或 1 开头
            r'^[\（\(][一二三四五六七八九十\d]+[\）\)]',  # （一）、（1）等
            r'^[A-Z]+\.?\s',                        # A. B. 等
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, line):
                return True
        
        # 全大写短行（可能是标题）
        if line.isupper() and len(line) < 50 and len(line.split()) < 8:
            return True
        
        # 居中短行（可能是标题）
        if len(line) < 30 and not line.endswith(('。', '！', '？', '.', '!', '?')):
            return True
        
        return False
    
    def _get_title_level(self, line: str) -> int:
        """
        获取标题级别
        """
        # 第X章 = 1级
        if re.match(r'^第[一二三四五六七八九十\d]+章', line):
            return 1
        # 第X节 = 2级  
        elif re.match(r'^第[一二三四五六七八九十\d]+节', line):
            return 2
        # 第X条 = 3级
        elif re.match(r'^第[一二三四五六七八九十\d]+条', line):
            return 3
        # 一、二、 = 2级
        elif re.match(r'^[一二三四五六七八九十]、', line):
            return 2
        # 数字编号 = 3级
        elif re.match(r'^\d+\.?\s', line):
            return 3
        # 括号编号 = 4级
        elif re.match(r'^[\（\(][一二三四五六七八九十\d]+[\）\)]', line):
            return 4
        else:
            return 1
    
    def _is_list_item(self, line: str) -> bool:
        """
        判断是否为列表项
        """
        list_patterns = [
            r'^[•·▪▫◦‣⁃]\s',           # 项目符号
            r'^\d+[\.、]\s',            # 数字列表
            r'^[一二三四五六七八九十][、．]\s', # 中文数字列表
            r'^[\（\(][一二三四五六七八九十\d]+[\）\)]\s', # 括号列表
            r'^[A-Za-z][\.、]\s',       # 字母列表
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _get_list_type(self, line: str) -> str:
        """
        获取列表类型
        """
        if re.match(r'^[•·▪▫◦‣⁃]\s', line):
            return "bullet"
        elif re.match(r'^\d+[\.、]\s', line):
            return "numbered"
        elif re.match(r'^[一二三四五六七八九十][、．]\s', line):
            return "chinese_numbered"
        elif re.match(r'^[\（\(][一二三四五六七八九十\d]+[\）\)]\s', line):
            return "parentheses"
        elif re.match(r'^[A-Za-z][\.、]\s', line):
            return "lettered"
        else:
            return "unknown"
    
    def _is_table_row(self, line: str) -> bool:
        """
        判断是否为表格行
        """
        # 简单的表格行检测
        separators = ['|', '\t', '  ', '│', '┃']
        separator_count = sum(line.count(sep) for sep in separators)
        
        return separator_count >= 2 and len(line) > 10
    
    def _restore_document_structure(self, text: str, structure: Dict) -> str:
        """
        恢复文档结构
        """
        try:
            lines = text.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    formatted_lines.append('')
                    continue
                
                # 格式化标题
                if self._is_title_line(line):
                    level = self._get_title_level(line)
                    if level == 1:
                        formatted_lines.append(f"\n\n{line}\n")
                    elif level == 2:
                        formatted_lines.append(f"\n{line}\n")
                    else:
                        formatted_lines.append(f"{line}\n")
                    continue
                
                # 格式化列表项
                if self._is_list_item(line):
                    formatted_lines.append(line)
                    continue
                
                # 格式化普通段落
                if len(line) > self.config["min_line_length"]:
                    # 检查是否需要与上一行合并
                    if (formatted_lines and 
                        formatted_lines[-1] and 
                        not formatted_lines[-1].endswith(('。', '！', '？', '.', '!', '?', '\n')) and
                        not self._is_title_line(formatted_lines[-1]) and
                        not self._is_list_item(line)):
                        formatted_lines[-1] += line
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"文档结构恢复失败: {e}")
            return text
    
    def _final_text_optimization(self, text: str, doc_type: str) -> str:
        """
        最终文本优化
        """
        try:
            # 移除多余的空行
            text = re.sub(r'\n{4,}', '\n\n\n', text)
            
            # 优化段落间距
            text = re.sub(r'\n\n+', '\n\n', text)
            
            # 移除行尾空格
            lines = []
            for line in text.split('\n'):
                lines.append(line.rstrip())
            
            text = '\n'.join(lines)
            
            # 确保文档以适当的方式结尾
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"最终文本优化失败: {e}")
            return text
    
    def _evaluate_text_quality(self, processed_text: str, original_text: str) -> float:
        """
        评估文本质量
        """
        try:
            score = 0.0
            
            # 基础分数（30分）
            if processed_text and processed_text.strip():
                score += 30
            
            # 长度合理性（10分）
            if len(processed_text) > len(original_text) * 0.8:
                score += 10
            
            # 中文字符比例（20分）
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', processed_text))
            if chinese_chars > 0:
                chinese_ratio = chinese_chars / len(processed_text)
                score += min(20, chinese_ratio * 40)  # 最高20分
            
            # 标点符号正确性（15分）
            punctuation_score = self._evaluate_punctuation(processed_text)
            score += punctuation_score
            
            # 结构完整性（15分）
            structure_score = self._evaluate_structure_quality(processed_text)
            score += structure_score
            
            # 可读性（10分）
            readability_score = self._evaluate_readability(processed_text)
            score += readability_score
            
            return min(100.0, score)
            
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            return 50.0  # 默认中等分数
    
    def _evaluate_punctuation(self, text: str) -> float:
        """
        评估标点符号质量
        """
        if not text:
            return 0.0
        
        # 检查标点符号配对
        brackets = {'（': '）', '(': ')', '[': ']', '【': '】', '"': '"', "'": "'"}
        score = 15.0
        
        for open_b, close_b in brackets.items():
            open_count = text.count(open_b)
            close_count = text.count(close_b)
            if abs(open_count - close_count) > 0:
                score -= 2  # 每个不配对减2分
        
        return max(0, score)
    
    def _evaluate_structure_quality(self, text: str) -> float:
        """
        评估结构质量
        """
        if not text:
            return 0.0
        
        score = 0.0
        lines = text.split('\n')
        
        # 检查是否有标题结构
        has_titles = any(self._is_title_line(line) for line in lines if line.strip())
        if has_titles:
            score += 5
        
        # 检查段落分布
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) > 5:
            score += 5
        
        # 检查是否有列表结构
        has_lists = any(self._is_list_item(line) for line in lines if line.strip())
        if has_lists:
            score += 5
        
        return score
    
    def _evaluate_readability(self, text: str) -> float:
        """
        评估可读性
        """
        if not text:
            return 0.0
        
        score = 0.0
        
        # 平均行长度合理性
        lines = [line for line in text.split('\n') if line.strip()]
        if lines:
            avg_length = sum(len(line) for line in lines) / len(lines)
            if 10 <= avg_length <= 100:  # 合理的行长度
                score += 5
        
        # 句子完整性（以句号结尾）
        sentences = re.split(r'[。！？.!?]', text)
        complete_sentences = len([s for s in sentences if len(s.strip()) > 5])
        if complete_sentences > 0:
            score += 5
        
        return score
    
    def _load_ocr_corrections(self) -> Dict[str, Dict[str, str]]:
        """
        加载OCR错误修正字典
        """
        return {
            "general": {
                # 常见字符误识别
                "O": "0",  # 字母O -> 数字0
                "l": "1",  # 小写l -> 数字1  
                "I": "1",  # 大写I -> 数字1
                "|": "1",  # 竖线 -> 数字1
                "S": "5",  # 在数字上下文中
                "G": "6",  # 在数字上下文中
                "B": "8",  # 在数字上下文中
                
                # 中文字符误识别
                "巳": "司",
                "戸": "户", 
                "仝": "同",
                "乂": "又",
                "丨": "一",
                "亍": "行",
                
                # 标点符号
                "，": "，",
                "。": "。",
                "；": "；",
                "：": "：",
                "！": "！",
                "？": "？",
            },
            
            "legal": {
                # 法律文档特有的修正
                "笫": "第",
                "苐": "第", 
                "弟": "第",
                "条敖": "条款",
                "法槼": "法规",
                "槼定": "规定",
                "実施": "实施",
            },
            
            "technical": {
                # 技术文档特有的修正
                "係统": "系统",
                "筦理": "管理",
                "網络": "网络",
                "數据": "数据",
                "軟件": "软件",
                "硬件": "硬件",
            }
        }
    
    def _compile_structure_patterns(self) -> Dict[str, List]:
        """
        编译文档结构模式
        """
        return {
            "title_patterns": [
                re.compile(r'^第[一二三四五六七八九十\d]+[章节条款]'),
                re.compile(r'^[一二三四五六七八九十]、'),
                re.compile(r'^\d+\.?\s*[^\d]'),
                re.compile(r'^[\（\(][一二三四五六七八九十\d]+[\）\)]'),
            ],
            
            "list_patterns": [
                re.compile(r'^[•·▪▫◦‣⁃]\s'),
                re.compile(r'^\d+[\.、]\s'),
                re.compile(r'^[一二三四五六七八九十][、．]\s'),
                re.compile(r'^[\（\(][一二三四五六七八九十\d]+[\）\)]\s'),
            ]
        }
    
    def get_processing_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取处理统计信息
        """
        original_text = result.get("original_text", "")
        processed_text = result.get("processed_text", "")
        
        stats = {
            "original_length": len(original_text),
            "processed_length": len(processed_text),
            "length_ratio": len(processed_text) / len(original_text) if original_text else 0,
            "corrections_applied": result.get("corrections_applied", 0),
            "quality_score": result.get("quality_score", 0),
            "processing_steps": len(result.get("processing_steps", [])),
            "warnings_count": len(result.get("warnings", [])),
            "structure_elements": sum([
                len(result.get("structure", {}).get("sections", [])),
                len(result.get("structure", {}).get("lists", [])),
                result.get("structure", {}).get("tables", 0)
            ])
        }
        
        # 处理效果评级
        if stats["quality_score"] >= 90:
            stats["grade"] = "优秀"
        elif stats["quality_score"] >= 80:
            stats["grade"] = "良好"
        elif stats["quality_score"] >= 70:
            stats["grade"] = "一般"
        else:
            stats["grade"] = "需要改进"
        
        return stats