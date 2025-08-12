# -*- coding: utf-8 -*-
"""
智能编码检测工具
自动检测文本文件的编码格式并正确读取内容
"""
import os
import chardet
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EncodingDetector:
    """智能编码检测器"""
    
    # 常见的编码格式，按优先级排序
    COMMON_ENCODINGS = [
        'utf-8',
        'gbk',
        'gb2312',
        'gb18030',
        'big5',
        'latin1',
        'cp1252',
        'iso-8859-1',
        'ascii'
    ]
    
    @classmethod
    def detect_encoding(cls, file_path: str, sample_size: int = 8192) -> Tuple[str, float]:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            sample_size: 采样大小，默认8KB
            
        Returns:
            Tuple[encoding, confidence]: (编码名称, 置信度)
        """
        try:
            if not os.path.exists(file_path):
                return 'utf-8', 0.0
            
            # 读取文件的一部分进行编码检测
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
                
            if not raw_data:
                return 'utf-8', 1.0
            
            # 使用chardet检测编码
            result = chardet.detect(raw_data)
            detected_encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0.0)
            
            # 对检测结果进行修正和标准化
            if detected_encoding:
                detected_encoding = cls._normalize_encoding(detected_encoding.lower())
                
                # 如果置信度太低，使用经验规则
                if confidence < 0.7:
                    # 检查是否包含中文字符的字节模式
                    if cls._contains_chinese_patterns(raw_data):
                        # 尝试GBK编码
                        try:
                            raw_data.decode('gbk')
                            logger.info(f"检测到中文字符模式，建议使用GBK编码: {file_path}")
                            return 'gbk', 0.8
                        except UnicodeDecodeError:
                            pass
                
                logger.info(f"检测到文件编码: {file_path} -> {detected_encoding} (置信度: {confidence:.2f})")
                return detected_encoding, confidence
            else:
                logger.warning(f"无法检测文件编码，使用默认UTF-8: {file_path}")
                return 'utf-8', 0.5
                
        except Exception as e:
            logger.error(f"编码检测失败: {file_path} - {str(e)}")
            return 'utf-8', 0.0
    
    @classmethod
    def _normalize_encoding(cls, encoding: str) -> str:
        """标准化编码名称"""
        encoding = encoding.lower().replace('-', '').replace('_', '')
        
        # 编码名称映射
        encoding_map = {
            'gb2312': 'gbk',
            'gb18030': 'gbk',
            'chinese': 'gbk',
            'windows1252': 'cp1252',
            'iso88591': 'latin1',
            'usascii': 'ascii',
        }
        
        return encoding_map.get(encoding, encoding)
    
    @classmethod
    def _contains_chinese_patterns(cls, data: bytes) -> bool:
        """检查字节数据是否包含中文字符的模式"""
        try:
            # GBK编码中文字符的字节范围
            # 第一字节: 0x81-0xFE
            # 第二字节: 0x40-0xFE (除了0x7F)
            chinese_count = 0
            total_bytes = len(data)
            
            i = 0
            while i < total_bytes - 1:
                first_byte = data[i]
                second_byte = data[i + 1]
                
                # 检查是否符合GBK中文字符模式
                if (0x81 <= first_byte <= 0xFE and 
                    0x40 <= second_byte <= 0xFE and 
                    second_byte != 0x7F):
                    chinese_count += 1
                    i += 2  # 跳过这个双字节字符
                else:
                    i += 1
            
            # 如果中文字符占比超过5%，认为可能是中文编码
            chinese_ratio = chinese_count * 2 / total_bytes if total_bytes > 0 else 0
            return chinese_ratio > 0.05
            
        except Exception:
            return False
    
    @classmethod
    def read_file_with_encoding(cls, file_path: str, encoding: str = None) -> Tuple[Optional[str], Optional[str]]:
        """
        使用指定或检测的编码读取文件
        
        Args:
            file_path: 文件路径
            encoding: 指定编码，如果为None则自动检测
            
        Returns:
            Tuple[content, error]: (文件内容, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return None, f"文件不存在: {file_path}"
            
            # 如果没有指定编码，自动检测
            if encoding is None:
                encoding, confidence = cls.detect_encoding(file_path)
                logger.info(f"自动检测编码: {file_path} -> {encoding} (置信度: {confidence:.2f})")
            
            # 尝试使用检测的编码读取文件
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.info(f"成功读取文件: {file_path} (编码: {encoding})")
                return content, None
                
            except UnicodeDecodeError as e:
                logger.warning(f"使用编码 {encoding} 读取失败: {file_path} - {str(e)}")
                
                # 尝试其他常见编码
                for fallback_encoding in cls.COMMON_ENCODINGS:
                    if fallback_encoding == encoding:
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding=fallback_encoding) as f:
                            content = f.read()
                        logger.info(f"使用回退编码成功读取文件: {file_path} (编码: {fallback_encoding})")
                        return content, None
                        
                    except UnicodeDecodeError:
                        continue
                
                # 所有编码都失败，使用UTF-8并忽略错误
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                logger.warning(f"使用UTF-8忽略错误模式读取文件: {file_path}")
                return content, "文件编码可能不正确，部分字符可能丢失"
                
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
            return None, error_msg
    
    @classmethod
    def convert_file_encoding(cls, file_path: str, target_encoding: str = 'utf-8') -> Tuple[bool, Optional[str]]:
        """
        转换文件编码并保存
        
        Args:
            file_path: 文件路径
            target_encoding: 目标编码，默认UTF-8
            
        Returns:
            Tuple[success, error]: (是否成功, 错误信息)
        """
        try:
            # 读取原始内容
            content, error = cls.read_file_with_encoding(file_path)
            if error and content is None:
                return False, error
            
            # 创建备份文件
            backup_path = file_path + '.bak'
            if not os.path.exists(backup_path):
                with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            
            # 使用目标编码保存文件
            with open(file_path, 'w', encoding=target_encoding) as f:
                f.write(content)
            
            logger.info(f"文件编码转换成功: {file_path} -> {target_encoding}")
            return True, None
            
        except Exception as e:
            error_msg = f"编码转换失败: {str(e)}"
            logger.error(f"{error_msg} - 文件: {file_path}")
            return False, error_msg
    
    @classmethod
    def detect_encoding_from_bytes(cls, data: bytes) -> Tuple[str, float]:
        """
        从字节数据检测编码
        
        Args:
            data: 字节数据
            
        Returns:
            Tuple[encoding, confidence]: (编码名称, 置信度)
        """
        try:
            if not data:
                return 'utf-8', 1.0
            
            # 使用chardet检测编码
            result = chardet.detect(data)
            detected_encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0.0)
            
            # 对检测结果进行修正和标准化
            if detected_encoding:
                detected_encoding = cls._normalize_encoding(detected_encoding.lower())
                
                # 如果置信度太低，使用经验规则
                if confidence < 0.7:
                    # 检查是否包含中文字符的字节模式
                    if cls._contains_chinese_patterns(data):
                        # 尝试GBK编码
                        try:
                            data.decode('gbk')
                            logger.info("检测到中文字符模式，建议使用GBK编码")
                            return 'gbk', 0.8
                        except UnicodeDecodeError:
                            pass
                
                logger.info(f"检测到编码: {detected_encoding} (置信度: {confidence:.2f})")
                return detected_encoding, confidence
            else:
                logger.warning("无法检测编码，使用默认UTF-8")
                return 'utf-8', 0.5
                
        except Exception as e:
            logger.error(f"编码检测失败: {str(e)}")
            return 'utf-8', 0.0
    
    @classmethod
    def read_file_content_from_bytes(cls, data: bytes, encoding: str = None) -> Tuple[Optional[str], Optional[str]]:
        """
        从字节数据读取文本内容
        
        Args:
            data: 字节数据
            encoding: 指定编码，如果为None则自动检测
            
        Returns:
            Tuple[content, error]: (文件内容, 错误信息)
        """
        try:
            if not data:
                return "", None
            
            # 如果没有指定编码，自动检测
            if encoding is None:
                encoding, confidence = cls.detect_encoding_from_bytes(data)
                logger.info(f"自动检测编码: {encoding} (置信度: {confidence:.2f})")
            
            # 尝试使用检测的编码读取数据
            try:
                content = data.decode(encoding)
                logger.info(f"成功解码内容 (编码: {encoding})")
                return content, None
                
            except UnicodeDecodeError as e:
                logger.warning(f"使用编码 {encoding} 解码失败: {str(e)}")
                
                # 尝试其他常见编码
                for fallback_encoding in cls.COMMON_ENCODINGS:
                    if fallback_encoding == encoding:
                        continue
                        
                    try:
                        content = data.decode(fallback_encoding)
                        logger.info(f"使用回退编码成功解码: {fallback_encoding}")
                        return content, None
                        
                    except UnicodeDecodeError:
                        continue
                
                # 所有编码都失败，使用UTF-8并忽略错误
                content = data.decode('utf-8', errors='ignore')
                logger.warning("使用UTF-8忽略错误模式解码")
                return content, "编码可能不正确，部分字符可能丢失"
                
        except Exception as e:
            error_msg = f"读取内容失败: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    @classmethod
    def get_encoding_info(cls, file_path: str) -> dict:
        """
        获取文件编码信息
        
        Returns:
            包含编码信息的字典
        """
        try:
            encoding, confidence = cls.detect_encoding(file_path)
            
            # 尝试读取内容以验证编码
            content, error = cls.read_file_with_encoding(file_path, encoding)
            
            return {
                'file_path': file_path,
                'detected_encoding': encoding,
                'confidence': confidence,
                'readable': content is not None,
                'error': error,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'contains_chinese': cls._contains_chinese_patterns(
                    open(file_path, 'rb').read(1024) if os.path.exists(file_path) else b''
                )
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'detected_encoding': 'unknown',
                'confidence': 0.0,
                'readable': False,
                'error': str(e),
                'file_size': 0,
                'contains_chinese': False
            }