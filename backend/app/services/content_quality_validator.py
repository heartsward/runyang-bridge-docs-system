# -*- coding: utf-8 -*-
"""
内容质量验证器 - 评估和验证提取内容的质量
确保文档内容提取的准确性和完整性
"""
import os
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentQualityValidator:
    """
    内容质量验证器
    - 提取质量评估
    - 内容完整性验证  
    - 准确性检测
    - 性能指标收集
    """
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 90,    # 优秀
            "good": 75,         # 良好  
            "acceptable": 60,   # 可接受
            "poor": 40          # 较差
        }
        
        # 质量检测配置
        self.validation_config = {
            "min_content_length": 10,           # 最小内容长度
            "max_corruption_ratio": 0.3,       # 最大损坏比例
            "min_chinese_ratio": 0.1,          # 最小中文比例（针对中文文档）
            "max_error_density": 0.05,         # 最大错误密度
            "min_structure_score": 0.3,        # 最小结构得分
            "expected_improvement": 0.15        # 期望的处理改进比例
        }
        
        # 内容检验模式
        self.validation_patterns = self._compile_validation_patterns()
        
        # 性能指标历史记录
        self.performance_history = []
    
    def validate_extraction_result(self, 
                                 original_file: str,
                                 extracted_content: str, 
                                 extraction_method: str,
                                 processing_time: float) -> Dict[str, Any]:
        """
        验证提取结果
        
        Args:
            original_file: 原始文件路径
            extracted_content: 提取的内容
            extraction_method: 提取方法
            processing_time: 处理时间
            
        Returns:
            验证结果字典
        """
        validation_result = {
            "file_path": original_file,
            "extraction_method": extraction_method,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            
            # 质量指标
            "quality_score": 0.0,
            "quality_grade": "unknown",
            "completeness_score": 0.0,
            "accuracy_score": 0.0,
            "structure_score": 0.0,
            "readability_score": 0.0,
            
            # 内容统计
            "content_length": len(extracted_content) if extracted_content else 0,
            "word_count": 0,
            "line_count": 0,
            "paragraph_count": 0,
            "chinese_char_count": 0,
            "english_word_count": 0,
            
            # 质量问题
            "issues": [],
            "warnings": [],
            "suggestions": [],
            
            # 性能指标
            "processing_speed": 0.0,  # 字符/秒
            "memory_efficiency": "unknown",
            "success": False
        }
        
        try:
            if not extracted_content or not extracted_content.strip():
                validation_result["issues"].append("提取内容为空")
                validation_result["quality_score"] = 0.0
                validation_result["quality_grade"] = "failed"
                return validation_result
            
            # 基本内容统计
            self._calculate_content_statistics(extracted_content, validation_result)
            
            # 完整性评估
            completeness_score = self._assess_content_completeness(extracted_content, original_file)
            validation_result["completeness_score"] = completeness_score
            
            # 准确性评估
            accuracy_score = self._assess_content_accuracy(extracted_content)
            validation_result["accuracy_score"] = accuracy_score
            
            # 结构质量评估
            structure_score = self._assess_structure_quality(extracted_content)
            validation_result["structure_score"] = structure_score
            
            # 可读性评估
            readability_score = self._assess_readability(extracted_content)
            validation_result["readability_score"] = readability_score
            
            # 计算综合质量分数
            quality_score = self._calculate_overall_quality_score(
                completeness_score, accuracy_score, structure_score, readability_score
            )
            validation_result["quality_score"] = quality_score
            validation_result["quality_grade"] = self._get_quality_grade(quality_score)
            
            # 性能指标
            if processing_time > 0:
                validation_result["processing_speed"] = len(extracted_content) / processing_time
            
            # 质量问题检测
            self._detect_quality_issues(extracted_content, validation_result)
            
            # 生成改进建议
            self._generate_improvement_suggestions(validation_result)
            
            # 成功标记
            validation_result["success"] = quality_score >= self.quality_thresholds["poor"]
            
            logger.info(f"内容质量验证完成: {original_file}, "
                       f"质量评分={quality_score:.1f}, "
                       f"评级={validation_result['quality_grade']}")
            
        except Exception as e:
            error_msg = f"质量验证失败: {str(e)}"
            logger.error(error_msg)
            validation_result["issues"].append(error_msg)
            validation_result["quality_score"] = 0.0
            validation_result["quality_grade"] = "error"
        
        # 记录性能历史
        self._record_performance_metrics(validation_result)
        
        return validation_result
    
    def _calculate_content_statistics(self, content: str, result: Dict[str, Any]):
        """
        计算内容统计信息
        """
        result["content_length"] = len(content)
        result["line_count"] = len(content.split('\n'))
        
        # 计算段落数（以空行分隔）
        paragraphs = re.split(r'\n\s*\n', content.strip())
        result["paragraph_count"] = len([p for p in paragraphs if p.strip()])
        
        # 中文字符统计
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        result["chinese_char_count"] = len(chinese_chars)
        
        # 英文单词统计
        english_words = re.findall(r'\b[a-zA-Z]+\b', content)
        result["english_word_count"] = len(english_words)
        
        # 总词数（中文字符 + 英文单词）
        result["word_count"] = result["chinese_char_count"] + result["english_word_count"]
    
    def _assess_content_completeness(self, content: str, original_file: str) -> float:
        """
        评估内容完整性
        """
        score = 100.0
        
        try:
            # 基于长度的完整性评估
            if len(content) < self.validation_config["min_content_length"]:
                score -= 40  # 内容太短
            
            # 基于文件大小的合理性检查
            if os.path.exists(original_file):
                file_size = os.path.getsize(original_file)
                size_mb = file_size / (1024 * 1024)
                
                # 预期的内容长度（基于文件大小的经验值）
                if file_size > 0:
                    expected_min_length = min(500, file_size / 1000)  # 粗略估算
                    if len(content) < expected_min_length:
                        score -= 20  # 内容明显少于预期
            
            # 截断检测
            truncation_indicators = [
                "[内容过长，已截断...]",
                "[内容已截断]",  
                "...继续阅读",
                "内容省略"
            ]
            
            for indicator in truncation_indicators:
                if indicator in content:
                    score -= 15  # 发现截断标记
                    break
            
            # 内容结构完整性
            has_beginning = len(content) > 50  # 有足够的开头内容
            has_ending = not content.strip().endswith(('...', '…', '未完'))  # 有合理的结尾
            
            if not has_beginning:
                score -= 10
            if not has_ending:
                score -= 10
            
        except Exception as e:
            logger.warning(f"完整性评估失败: {e}")
            score -= 20
        
        return max(0.0, min(100.0, score))
    
    def _assess_content_accuracy(self, content: str) -> float:
        """
        评估内容准确性
        """
        score = 100.0
        
        try:
            # OCR错误模式检测
            ocr_error_patterns = [
                r'[Il|l]{2,}',          # 连续的 I、l、| 字符（可能是OCR误识别）
                r'[0O]{3,}',            # 连续的 0、O 字符
                r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,;:!?()[]{}"\'-]{3,}',  # 连续的特殊字符
                r'\*{5,}',              # 连续的星号（替换字符）
                r'[\x00-\x1f\x7f-\x9f]',  # 控制字符
            ]
            
            error_count = 0
            for pattern in ocr_error_patterns:
                matches = re.findall(pattern, content)
                error_count += len(matches)
            
            # 计算错误密度
            if len(content) > 0:
                error_density = error_count / len(content)
                if error_density > self.validation_config["max_error_density"]:
                    score -= min(50, error_density * 1000)  # 错误密度惩罚
            
            # 乱码检测
            corruption_indicators = [
                '口口',  # 常见乱码
                '□□',
                '??',
                '锘?',
                '鎴?',
            ]
            
            corruption_count = sum(content.count(indicator) for indicator in corruption_indicators)
            if corruption_count > 0:
                corruption_ratio = corruption_count / len(content)
                if corruption_ratio > self.validation_config["max_corruption_ratio"]:
                    score -= 30  # 严重乱码
            
            # 语法合理性检查（简单）
            # 检查标点符号配对
            brackets = ['（）', '()', '[]', '【】', '""', "''"]
            for bracket_pair in brackets:
                open_char, close_char = bracket_pair[0], bracket_pair[-1]
                open_count = content.count(open_char)
                close_count = content.count(close_char)
                if abs(open_count - close_count) > len(content) // 100:  # 1%的容错
                    score -= 5  # 标点符号不配对
            
        except Exception as e:
            logger.warning(f"准确性评估失败: {e}")
            score -= 20
        
        return max(0.0, min(100.0, score))
    
    def _assess_structure_quality(self, content: str) -> float:
        """
        评估结构质量
        """
        score = 0.0
        
        try:
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            if not non_empty_lines:
                return 0.0
            
            # 基础结构分析
            # 1. 段落结构 (30分)
            paragraphs = re.split(r'\n\s*\n', content.strip())
            meaningful_paragraphs = [p for p in paragraphs if len(p.strip()) > 20]
            
            if len(meaningful_paragraphs) > 0:
                score += 20  # 有段落结构
                if len(meaningful_paragraphs) > 3:
                    score += 10  # 多段落结构更好
            
            # 2. 标题结构 (25分)
            title_patterns = [
                r'^第[一二三四五六七八九十\d]+[章节条款]',
                r'^[一二三四五六七八九十]、',
                r'^\d+\.?\s*[^\d]',
                r'^[\（\(][一二三四五六七八九十\d]+[\）\)]',
            ]
            
            title_count = 0
            for line in non_empty_lines:
                for pattern in title_patterns:
                    if re.match(pattern, line.strip()):
                        title_count += 1
                        break
            
            if title_count > 0:
                score += 15  # 有标题结构
                if title_count > 2:
                    score += 10  # 多级标题更好
            
            # 3. 列表结构 (20分)
            list_patterns = [
                r'^[•·▪▫◦‣⁃]\s',
                r'^\d+[\.、]\s',
                r'^[一二三四五六七八九十][、．]\s',
                r'^[A-Za-z][\.、]\s',
            ]
            
            list_count = 0
            for line in non_empty_lines:
                for pattern in list_patterns:
                    if re.match(pattern, line.strip()):
                        list_count += 1
                        break
            
            if list_count > 0:
                score += 10
                if list_count > 3:
                    score += 10
            
            # 4. 格式一致性 (15分)
            # 检查行长度分布
            line_lengths = [len(line.strip()) for line in non_empty_lines if len(line.strip()) > 5]
            if line_lengths:
                import statistics
                try:
                    mean_length = statistics.mean(line_lengths)
                    std_length = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
                    
                    # 合理的长度分布
                    if 20 <= mean_length <= 100 and std_length < mean_length:
                        score += 15
                    elif 10 <= mean_length <= 150:
                        score += 8
                except:
                    score += 5  # 基础分
            
            # 5. 完整性 (10分)
            # 检查是否有合理的开头和结尾
            first_line = non_empty_lines[0] if non_empty_lines else ""
            last_line = non_empty_lines[-1] if non_empty_lines else ""
            
            if len(first_line) > 5:
                score += 5  # 有合理开头
            
            if last_line and not last_line.endswith(('...', '…', '未完', '待续')):
                score += 5  # 有合理结尾
        
        except Exception as e:
            logger.warning(f"结构质量评估失败: {e}")
        
        return max(0.0, min(100.0, score))
    
    def _assess_readability(self, content: str) -> float:
        """
        评估可读性
        """
        score = 0.0
        
        try:
            if not content or len(content.strip()) < 10:
                return 0.0
            
            # 1. 字符组成合理性 (30分)
            total_chars = len(content)
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            english_chars = len(re.findall(r'[a-zA-Z]', content))
            digits = len(re.findall(r'\d', content))
            punctuation = len(re.findall(r'[.,;:!?，。；：！？]', content))
            
            # 中文文档的合理字符分布
            if chinese_chars > 0:
                chinese_ratio = chinese_chars / total_chars
                if 0.3 <= chinese_ratio <= 0.9:  # 合理的中文比例
                    score += 20
                elif 0.1 <= chinese_ratio <= 0.95:
                    score += 15
                else:
                    score += 5
                
                # 标点符号比例
                punct_ratio = punctuation / total_chars
                if 0.02 <= punct_ratio <= 0.15:  # 合理的标点比例
                    score += 10
            
            # 2. 句子完整性 (25分)
            sentences = re.split(r'[。！？.!?]', content)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
            
            if meaningful_sentences:
                score += 15
                
                # 平均句子长度
                avg_sentence_length = sum(len(s) for s in meaningful_sentences) / len(meaningful_sentences)
                if 10 <= avg_sentence_length <= 100:  # 合理句子长度
                    score += 10
            
            # 3. 段落结构 (20分)
            paragraphs = re.split(r'\n\s*\n', content.strip())
            meaningful_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
            
            if meaningful_paragraphs:
                score += 10
                
                # 段落长度分布
                if len(meaningful_paragraphs) > 1:
                    avg_paragraph_length = sum(len(p) for p in meaningful_paragraphs) / len(meaningful_paragraphs)
                    if 50 <= avg_paragraph_length <= 500:
                        score += 10
            
            # 4. 格式规范性 (25分)
            # 检查空白字符使用
            excessive_spaces = re.findall(r' {3,}', content)
            excessive_newlines = re.findall(r'\n{4,}', content)
            
            if len(excessive_spaces) < len(content) // 100:  # 少于1%的过多空格
                score += 10
            
            if len(excessive_newlines) < len(content) // 200:  # 少于0.5%的过多换行
                score += 10
            
            # 检查编码问题
            try:
                content.encode('utf-8')
                score += 5  # 编码正常
            except:
                pass  # 编码有问题，不加分
            
        except Exception as e:
            logger.warning(f"可读性评估失败: {e}")
        
        return max(0.0, min(100.0, score))
    
    def _calculate_overall_quality_score(self, completeness: float, accuracy: float, 
                                       structure: float, readability: float) -> float:
        """
        计算综合质量分数
        """
        # 权重分配
        weights = {
            "completeness": 0.35,    # 完整性权重35%
            "accuracy": 0.35,        # 准确性权重35%
            "structure": 0.15,       # 结构权重15%
            "readability": 0.15      # 可读性权重15%
        }
        
        weighted_score = (
            completeness * weights["completeness"] +
            accuracy * weights["accuracy"] +
            structure * weights["structure"] +
            readability * weights["readability"]
        )
        
        return round(weighted_score, 1)
    
    def _get_quality_grade(self, score: float) -> str:
        """
        根据分数获取质量等级
        """
        if score >= self.quality_thresholds["excellent"]:
            return "优秀"
        elif score >= self.quality_thresholds["good"]:
            return "良好"
        elif score >= self.quality_thresholds["acceptable"]:
            return "可接受"
        elif score >= self.quality_thresholds["poor"]:
            return "较差"
        else:
            return "失败"
    
    def _detect_quality_issues(self, content: str, result: Dict[str, Any]):
        """
        检测质量问题
        """
        issues = []
        warnings = []
        
        # 内容长度问题
        if len(content) < 50:
            issues.append("内容过短，可能提取不完整")
        elif len(content) > 500000:  # 500KB
            warnings.append("内容过长，可能包含重复或无关信息")
        
        # 乱码检测
        corruption_patterns = [
            (r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,;:!?()[]{}"\'-]{10,}', "检测到疑似乱码内容"),
            (r'\*{10,}', "发现大量替换字符，原文可能有识别问题"),
            (r'口{5,}', "发现大量口字符，可能是字体缺失"),
        ]
        
        for pattern, message in corruption_patterns:
            if re.search(pattern, content):
                issues.append(message)
        
        # 结构问题
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) < 3:
            warnings.append("文档结构简单，可能缺少段落分割")
        
        # 编码问题
        try:
            content.encode('utf-8').decode('utf-8')
        except:
            issues.append("存在字符编码问题")
        
        result["issues"].extend(issues)
        result["warnings"].extend(warnings)
    
    def _generate_improvement_suggestions(self, result: Dict[str, Any]):
        """
        生成改进建议
        """
        suggestions = []
        
        # 基于质量分数的建议
        if result["quality_score"] < 60:
            suggestions.append("建议重新提取文档内容或尝试其他提取方法")
        
        if result["completeness_score"] < 70:
            suggestions.append("内容可能不完整，建议检查原文档是否为扫描版或需要OCR处理")
        
        if result["accuracy_score"] < 70:
            suggestions.append("发现较多识别错误，建议使用图像预处理或调整OCR参数")
        
        if result["structure_score"] < 50:
            suggestions.append("文档结构识别效果不佳，建议进行格式恢复处理")
        
        if result["readability_score"] < 60:
            suggestions.append("文档可读性有待提升，建议进行文本规范化处理")
        
        # 基于处理时间的建议
        if result["processing_time"] > 60:  # 超过1分钟
            suggestions.append("处理时间较长，建议优化文档预处理或考虑分块处理")
        
        result["suggestions"] = suggestions
    
    def _record_performance_metrics(self, result: Dict[str, Any]):
        """
        记录性能指标
        """
        metrics = {
            "timestamp": result["timestamp"],
            "file_path": result["file_path"],
            "extraction_method": result["extraction_method"],
            "quality_score": result["quality_score"],
            "processing_time": result["processing_time"],
            "processing_speed": result.get("processing_speed", 0),
            "content_length": result["content_length"],
            "success": result["success"]
        }
        
        # 保留最近100条记录
        self.performance_history.append(metrics)
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
    
    def _compile_validation_patterns(self) -> Dict[str, List]:
        """
        编译验证模式
        """
        return {
            "error_patterns": [
                re.compile(r'[Il|l]{3,}'),  # 连续相似字符
                re.compile(r'[0O]{3,}'),
                re.compile(r'\*{5,}'),      # 连续替换字符
                re.compile(r'口{3,}'),      # 连续缺失字符
            ],
            
            "corruption_patterns": [
                re.compile(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,;:!?()[]{}"\'-]{5,}'),
                re.compile(r'[\x00-\x1f\x7f-\x9f]+'),  # 控制字符
            ]
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能汇总统计
        """
        if not self.performance_history:
            return {"message": "暂无性能数据"}
        
        recent_records = self.performance_history[-20:]  # 最近20条记录
        
        # 计算统计指标
        quality_scores = [r["quality_score"] for r in recent_records]
        processing_times = [r["processing_time"] for r in recent_records if r["processing_time"] > 0]
        success_count = sum(1 for r in recent_records if r["success"])
        
        summary = {
            "total_validations": len(recent_records),
            "success_rate": success_count / len(recent_records) * 100,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "quality_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 90),
                "good": sum(1 for s in quality_scores if 75 <= s < 90),
                "acceptable": sum(1 for s in quality_scores if 60 <= s < 75),
                "poor": sum(1 for s in quality_scores if s < 60),
            }
        }
        
        return summary
    
    def export_validation_report(self, results: List[Dict[str, Any]], output_file: str):
        """
        导出验证报告
        """
        try:
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "total_validations": len(results),
                "summary": {
                    "average_quality": sum(r["quality_score"] for r in results) / len(results) if results else 0,
                    "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100 if results else 0,
                },
                "validations": results,
                "performance_summary": self.get_performance_summary()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"验证报告已导出: {output_file}")
            
        except Exception as e:
            logger.error(f"导出验证报告失败: {e}")