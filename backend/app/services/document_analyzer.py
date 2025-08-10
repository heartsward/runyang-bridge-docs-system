# -*- coding: utf-8 -*-
"""
文档内容智能分析服务
使用jieba和scikit-learn进行中文文档分析
"""
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np


class DocumentAnalyzer:
    """文档内容智能分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 设置jieba静默模式
        jieba.setLogLevel(20)
        
        # 预定义的运维文档类型关键词
        self.doc_type_keywords = {
            "配置文档": [
                "配置", "设置", "参数", "config", "configuration", "setting", 
                "环境变量", "yml", "yaml", "json", "xml", "ini", "conf",
                "网络配置", "系统配置", "应用配置", "数据库配置"
            ],
            "操作手册": [
                "操作", "步骤", "流程", "手册", "指南", "教程", "使用说明",
                "安装", "部署", "升级", "维护", "备份", "恢复", "重启"
            ],
            "故障处理": [
                "故障", "问题", "错误", "异常", "error", "exception", "bug",
                "排查", "诊断", "修复", "解决", "处理", "troubleshoot",
                "日志", "监控", "告警", "报警"
            ],
            "网络文档": [
                "网络", "路由", "交换", "防火墙", "VPN", "IP", "DNS", "DHCP",
                "VLAN", "子网", "网段", "端口", "协议", "TCP", "UDP", "HTTP"
            ],
            "安全文档": [
                "安全", "权限", "认证", "授权", "加密", "密码", "证书", "SSL",
                "TLS", "防护", "漏洞", "补丁", "安全策略", "访问控制"
            ],
            "监控文档": [
                "监控", "告警", "指标", "性能", "资源", "CPU", "内存", "磁盘",
                "带宽", "流量", "负载", "阈值", "图表", "dashboard"
            ],
            "备份文档": [
                "备份", "还原", "恢复", "快照", "镜像", "归档", "同步",
                "增量", "全量", "定时", "策略", "存储"
            ]
        }
        
        # 停用词列表
        self.stop_words = {
            "的", "是", "在", "了", "和", "有", "要", "为", "与", "及", "等",
            "但", "或", "而", "以", "将", "从", "到", "由", "被", "把", "给",
            "这", "那", "其", "它", "他", "她", "我", "你", "您", "们",
            "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
            "上", "下", "中", "内", "外", "前", "后", "左", "右", "东", "西", "南", "北"
        }
    
    def extract_content_from_file(self, file_path: str, file_type: str) -> str:
        """从文件中提取文本内容"""
        try:
            if file_type.lower() in ['txt', 'md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_type.lower() in ['csv']:
                import pandas as pd
                df = pd.read_csv(file_path)
                return df.to_string()
            elif file_type.lower() in ['xlsx', 'xls']:
                import pandas as pd
                df = pd.read_excel(file_path)
                return df.to_string()
            elif file_type.lower() in ['json']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                # 尝试作为文本文件读取
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"提取文件内容失败: {str(e)}")
            return ""
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """提取关键词"""
        try:
            # 使用jieba的TF-IDF算法提取关键词
            keywords_with_scores = jieba.analyse.extract_tags(
                text, topK=top_k, withWeight=True, allowPOS=('n', 'nz', 'v', 'vn', 'a', 'ad', 'an')
            )
            
            return [
                {
                    "keyword": keyword,
                    "weight": float(score),
                    "type": "tfidf"
                }
                for keyword, score in keywords_with_scores
            ]
        except Exception as e:
            print(f"关键词提取失败: {str(e)}")
            return []
    
    def classify_document_type(self, text: str, keywords: List[str] = None) -> Dict[str, Any]:
        """分类文档类型"""
        try:
            # 如果没有提供关键词，则提取关键词
            if keywords is None:
                keyword_data = self.extract_keywords(text, top_k=20)
                keywords = [kw["keyword"] for kw in keyword_data]
            
            # 计算每种文档类型的匹配分数
            type_scores = {}
            
            for doc_type, type_keywords in self.doc_type_keywords.items():
                score = 0
                matched_keywords = []
                
                # 检查关键词匹配
                for keyword in keywords:
                    for type_keyword in type_keywords:
                        if type_keyword in keyword.lower() or keyword.lower() in type_keyword:
                            score += 1
                            matched_keywords.append(keyword)
                            break
                
                # 检查文本中的直接匹配
                text_lower = text.lower()
                for type_keyword in type_keywords:
                    count = text_lower.count(type_keyword)
                    score += count * 0.1  # 直接匹配权重较低
                
                if score > 0:
                    type_scores[doc_type] = {
                        "score": score,
                        "matched_keywords": list(set(matched_keywords)),
                        "confidence": min(score / 10.0, 1.0)  # 归一化置信度
                    }
            
            # 如果没有匹配到任何类型，返回"其他"
            if not type_scores:
                return {
                    "predicted_type": "其他",
                    "confidence": 0.1,
                    "all_scores": {},
                    "matched_keywords": []
                }
            
            # 选择得分最高的类型
            best_type = max(type_scores.keys(), key=lambda x: type_scores[x]["score"])
            
            return {
                "predicted_type": best_type,
                "confidence": type_scores[best_type]["confidence"],
                "all_scores": type_scores,
                "matched_keywords": type_scores[best_type]["matched_keywords"]
            }
            
        except Exception as e:
            print(f"文档分类失败: {str(e)}")
            return {
                "predicted_type": "其他",
                "confidence": 0.0,
                "all_scores": {},
                "matched_keywords": []
            }
    
    def extract_technical_entities(self, text: str) -> Dict[str, List[str]]:
        """提取技术实体（IP地址、域名、端口等）"""
        entities = {
            "ip_addresses": [],
            "domains": [],
            "urls": [],
            "ports": [],
            "file_paths": [],
            "commands": [],
            "config_keys": []
        }
        
        try:
            # IP地址模式
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            entities["ip_addresses"] = list(set(re.findall(ip_pattern, text)))
            
            # 域名模式
            domain_pattern = r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+\b'
            potential_domains = re.findall(domain_pattern, text)
            entities["domains"] = list(set([domain[0] + domain[1] for domain in potential_domains if len(domain[0] + domain[1]) > 3]))
            
            # URL模式
            url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+|ftp://[^\s<>"{}|\\^`[\]]+'
            entities["urls"] = list(set(re.findall(url_pattern, text)))
            
            # 端口模式
            port_pattern = r':(\d{1,5})\b'
            potential_ports = re.findall(port_pattern, text)
            entities["ports"] = list(set([port for port in potential_ports if 1 <= int(port) <= 65535]))
            
            # 文件路径模式
            path_pattern = r'[/\\](?:[^/\\:\*\?"<>\|\s]+[/\\])*[^/\\:\*\?"<>\|\s]*'
            entities["file_paths"] = list(set(re.findall(path_pattern, text)))
            
            # 常见命令模式
            command_pattern = r'\b(systemctl|service|docker|kubectl|nginx|apache|mysql|redis|git|ssh|scp|rsync|tar|zip|unzip|grep|awk|sed|cat|tail|head|ps|netstat|lsof|iptables)\s+\S+'
            entities["commands"] = list(set(re.findall(command_pattern, text, re.IGNORECASE)))
            
            # 配置项模式
            config_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]\s*[^\s\n]+'
            entities["config_keys"] = list(set([match.split('=')[0].split(':')[0].strip() for match in re.findall(config_pattern, text)]))
            
        except Exception as e:
            print(f"技术实体提取失败: {str(e)}")
        
        return entities
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文档的相似度"""
        try:
            # 使用jieba分词
            words1 = jieba.lcut(text1)
            words2 = jieba.lcut(text2)
            
            # 过滤停用词
            words1 = [word for word in words1 if word not in self.stop_words and len(word) > 1]
            words2 = [word for word in words2 if word not in self.stop_words and len(word) > 1]
            
            if not words1 or not words2:
                return 0.0
            
            # 创建TF-IDF向量
            vectorizer = TfidfVectorizer()
            corpus = [' '.join(words1), ' '.join(words2)]
            
            tfidf_matrix = vectorizer.fit_transform(corpus)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"相似度计算失败: {str(e)}")
            return 0.0
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """生成文档摘要"""
        try:
            # 简单的摘要生成：提取前几句话
            sentences = re.split(r'[。！？\n]', text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
            
            if len(sentences) <= max_sentences:
                return '。'.join(sentences) + '。'
            
            # 选择最具代表性的句子（包含更多关键词的句子）
            keywords = [kw["keyword"] for kw in self.extract_keywords(text, top_k=10)]
            
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                score = sum(1 for keyword in keywords if keyword in sentence)
                sentence_scores.append((score, i, sentence))
            
            # 按分数排序，选择前几句
            sentence_scores.sort(reverse=True)
            selected_sentences = sentence_scores[:max_sentences]
            
            # 按原始顺序排序
            selected_sentences.sort(key=lambda x: x[1])
            
            summary = '。'.join([s[2] for s in selected_sentences])
            return summary + '。' if summary else text[:200] + '...'
            
        except Exception as e:
            print(f"摘要生成失败: {str(e)}")
            return text[:200] + '...' if len(text) > 200 else text
    
    def analyze_document(self, file_path: str, file_type: str, title: str = "") -> Dict[str, Any]:
        """综合分析文档"""
        try:
            # 提取文本内容
            content = self.extract_content_from_file(file_path, file_type)
            
            if not content:
                return {
                    "success": False,
                    "error": "无法提取文件内容",
                    "keywords": [],
                    "document_type": {"predicted_type": "其他", "confidence": 0.0},
                    "technical_entities": {},
                    "summary": "",
                    "content_length": 0
                }
            
            # 如果内容太长，截取前5000字符进行分析
            analysis_content = content[:5000] if len(content) > 5000 else content
            
            # 提取关键词
            keywords = self.extract_keywords(analysis_content, top_k=15)
            
            # 分类文档类型
            doc_type = self.classify_document_type(analysis_content, [kw["keyword"] for kw in keywords])
            
            # 提取技术实体
            entities = self.extract_technical_entities(analysis_content)
            
            # 生成摘要
            summary = self.generate_summary(analysis_content, max_sentences=3)
            
            return {
                "success": True,
                "keywords": keywords,
                "document_type": doc_type,
                "technical_entities": entities,
                "summary": summary,
                "content_length": len(content),
                "analysis_metadata": {
                    "analyzer_version": "1.0",
                    "analysis_time": "2025-01-29",
                    "content_analyzed_length": len(analysis_content)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"文档分析失败: {str(e)}",
                "keywords": [],
                "document_type": {"predicted_type": "其他", "confidence": 0.0},
                "technical_entities": {},
                "summary": "",
                "content_length": 0
            }