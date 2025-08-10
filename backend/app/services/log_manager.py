"""
日志管理服务
"""
import os
import logging
import json
import gzip
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import re

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(str, Enum):
    """日志分类"""
    SYSTEM = "system"
    ACCESS = "access"
    ERROR = "error"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    category: str
    message: str
    module: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class LogManager:
    """日志管理服务"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 日志文件配置
        self.log_files = {
            LogCategory.SYSTEM: self.log_dir / "system.log",
            LogCategory.ACCESS: self.log_dir / "access.log",
            LogCategory.ERROR: self.log_dir / "error.log",
            LogCategory.SECURITY: self.log_dir / "security.log",
            LogCategory.AUDIT: self.log_dir / "audit.log",
            LogCategory.PERFORMANCE: self.log_dir / "performance.log"
        }
        
        # 日志轮转配置
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_backup_count = 10
        self.retention_days = 30
        
        # 初始化日志记录器
        self._setup_loggers()
        
        # 日志格式
        self.log_format = {
            'timestamp': '%(asctime)s',
            'level': '%(levelname)s',
            'module': '%(name)s',
            'message': '%(message)s'
        }
    
    def _setup_loggers(self):
        """设置日志记录器"""
        # 创建自定义格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 为每个分类创建处理器
        self.loggers = {}
        for category, log_file in self.log_files.items():
            logger = logging.getLogger(f"app.{category.value}")
            logger.setLevel(logging.DEBUG)
            
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            self.loggers[category] = logger
    
    def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        module: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """记录日志"""
        try:
            # 创建日志条目
            log_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=level.value,
                category=category.value,
                message=message,
                module=module,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                extra_data=extra_data
            )
            
            # 获取对应的日志记录器
            logger = self.loggers.get(category)
            if not logger:
                logger = logging.getLogger("app.default")
            
            # 构建日志消息
            log_message = self._format_log_message(log_entry)
            
            # 根据级别记录日志
            if level == LogLevel.DEBUG:
                logger.debug(log_message)
            elif level == LogLevel.INFO:
                logger.info(log_message)
            elif level == LogLevel.WARNING:
                logger.warning(log_message)
            elif level == LogLevel.ERROR:
                logger.error(log_message)
            elif level == LogLevel.CRITICAL:
                logger.critical(log_message)
                
        except Exception as e:
            # 日志记录失败时使用标准日志
            logging.error(f"日志记录失败: {e}")
    
    def _format_log_message(self, log_entry: LogEntry) -> str:
        """格式化日志消息"""
        parts = [log_entry.message]
        
        if log_entry.user_id:
            parts.append(f"user_id={log_entry.user_id}")
        
        if log_entry.ip_address:
            parts.append(f"ip={log_entry.ip_address}")
        
        if log_entry.request_id:
            parts.append(f"request_id={log_entry.request_id}")
        
        if log_entry.extra_data:
            extra_str = json.dumps(log_entry.extra_data, ensure_ascii=False)
            parts.append(f"extra={extra_str}")
        
        return " | ".join(parts)
    
    def search_logs(
        self,
        category: Optional[LogCategory] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        keyword: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索日志"""
        try:
            results = []
            
            # 确定要搜索的日志文件
            if category:
                log_files = [self.log_files[category]]
            else:
                log_files = list(self.log_files.values())
            
            for log_file in log_files:
                if not log_file.exists():
                    continue
                
                file_results = self._search_log_file(
                    log_file, level, start_time, end_time, keyword, user_id
                )
                results.extend(file_results)
            
            # 按时间戳排序
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logging.error(f"搜索日志失败: {e}")
            return []
    
    def _search_log_file(
        self,
        log_file: Path,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        keyword: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """搜索单个日志文件"""
        results = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析日志行
                    log_data = self._parse_log_line(line)
                    if not log_data:
                        continue
                    
                    # 应用过滤器
                    if level and log_data.get('level') != level.value:
                        continue
                    
                    if start_time or end_time:
                        log_time = self._parse_timestamp(log_data.get('timestamp'))
                        if log_time:
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue
                    
                    if keyword and keyword.lower() not in line.lower():
                        continue
                    
                    if user_id and f"user_id={user_id}" not in line:
                        continue
                    
                    log_data['file'] = log_file.name
                    log_data['line_number'] = line_no
                    results.append(log_data)
        
        except Exception as e:
            logging.error(f"搜索日志文件 {log_file} 失败: {e}")
        
        return results
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        try:
            # 日志格式: 2025-08-05 12:00:00 - INFO - app.system - message | user_id=1 | ip=127.0.0.1
            parts = line.split(' - ', 3)
            if len(parts) < 4:
                return None
            
            timestamp = parts[0]
            level = parts[1]
            module = parts[2]
            message_part = parts[3]
            
            # 分离消息和额外数据
            message_parts = message_part.split(' | ')
            message = message_parts[0]
            
            log_data = {
                'timestamp': timestamp,
                'level': level,
                'module': module,
                'message': message,
                'raw_line': line
            }
            
            # 解析额外数据
            for part in message_parts[1:]:
                if '=' in part:
                    key, value = part.split('=', 1)
                    log_data[key] = value
            
            return log_data
            
        except Exception:
            return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None
        
        try:
            # 尝试多种时间格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def get_log_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            stats = {
                'total_entries': 0,
                'by_level': {},
                'by_category': {},
                'by_day': {},
                'top_errors': [],
                'file_sizes': {}
            }
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 统计各个日志文件
            for category, log_file in self.log_files.items():
                if not log_file.exists():
                    continue
                
                # 文件大小
                stats['file_sizes'][category.value] = log_file.stat().st_size
                
                # 分析日志内容
                file_stats = self._analyze_log_file(log_file, start_time, end_time)
                
                stats['total_entries'] += file_stats['total_entries']
                
                # 合并级别统计
                for level, count in file_stats['by_level'].items():
                    stats['by_level'][level] = stats['by_level'].get(level, 0) + count
                
                # 分类统计
                stats['by_category'][category.value] = file_stats['total_entries']
                
                # 合并每日统计
                for day, count in file_stats['by_day'].items():
                    stats['by_day'][day] = stats['by_day'].get(day, 0) + count
                
                # 收集错误信息
                stats['top_errors'].extend(file_stats['errors'])
            
            # 排序错误信息
            stats['top_errors'] = sorted(
                stats['top_errors'], 
                key=lambda x: x['count'], 
                reverse=True
            )[:10]
            
            return stats
            
        except Exception as e:
            logging.error(f"获取日志统计失败: {e}")
            return {}
    
    def _analyze_log_file(
        self, 
        log_file: Path, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """分析单个日志文件"""
        stats = {
            'total_entries': 0,
            'by_level': {},
            'by_day': {},
            'errors': []
        }
        
        error_messages = {}
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    log_data = self._parse_log_line(line)
                    if not log_data:
                        continue
                    
                    # 检查时间范围
                    log_time = self._parse_timestamp(log_data.get('timestamp'))
                    if log_time and (log_time < start_time or log_time > end_time):
                        continue
                    
                    stats['total_entries'] += 1
                    
                    # 级别统计
                    level = log_data.get('level', 'UNKNOWN')
                    stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
                    
                    # 每日统计
                    if log_time:
                        day = log_time.strftime('%Y-%m-%d')
                        stats['by_day'][day] = stats['by_day'].get(day, 0) + 1
                    
                    # 收集错误信息
                    if level in ['ERROR', 'CRITICAL']:
                        message = log_data.get('message', '')
                        # 简化错误信息（去除变量部分）
                        simplified_message = re.sub(r'\d+', '<NUMBER>', message)
                        simplified_message = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>', simplified_message)
                        
                        error_messages[simplified_message] = error_messages.get(simplified_message, 0) + 1
        
        except Exception as e:
            logging.error(f"分析日志文件 {log_file} 失败: {e}")
        
        # 转换错误统计
        stats['errors'] = [
            {'message': msg, 'count': count}
            for msg, count in error_messages.items()
        ]
        
        return stats
    
    def cleanup_old_logs(self):
        """清理旧日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for category, log_file in self.log_files.items():
                if not log_file.exists():
                    continue
                
                # 检查文件修改时间
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    # 压缩旧文件
                    self._compress_log_file(log_file)
            
            # 清理旧的压缩文件
            self._cleanup_compressed_logs()
            
        except Exception as e:
            logging.error(f"清理旧日志失败: {e}")
    
    def _compress_log_file(self, log_file: Path):
        """压缩日志文件"""
        try:
            compressed_file = log_file.with_suffix(f"{log_file.suffix}.{datetime.now().strftime('%Y%m%d')}.gz")
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # 清空原文件内容（但保持文件存在）
            log_file.write_text('', encoding='utf-8')
            
            logging.info(f"日志文件已压缩: {compressed_file}")
            
        except Exception as e:
            logging.error(f"压缩日志文件失败: {e}")
    
    def _cleanup_compressed_logs(self):
        """清理压缩日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for gz_file in self.log_dir.glob("*.gz"):
                file_mtime = datetime.fromtimestamp(gz_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    gz_file.unlink()
                    logging.info(f"已删除旧压缩日志: {gz_file}")
        
        except Exception as e:
            logging.error(f"清理压缩日志失败: {e}")
    
    def rotate_logs(self):
        """轮转日志"""
        try:
            for category, log_file in self.log_files.items():
                if not log_file.exists():
                    continue
                
                # 检查文件大小
                if log_file.stat().st_size > self.max_file_size:
                    self._rotate_log_file(log_file)
        
        except Exception as e:
            logging.error(f"轮转日志失败: {e}")
    
    def _rotate_log_file(self, log_file: Path):
        """轮转单个日志文件"""
        try:
            # 创建备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = log_file.with_suffix(f".{timestamp}{log_file.suffix}")
            
            # 移动当前文件到备份
            log_file.rename(backup_file)
            
            # 压缩备份文件
            self._compress_log_file(backup_file)
            backup_file.unlink()  # 删除未压缩的备份
            
            # 创建新的空日志文件
            log_file.touch()
            
            logging.info(f"日志文件已轮转: {log_file}")
            
        except Exception as e:
            logging.error(f"轮转日志文件失败: {e}")
    
    def export_logs(
        self,
        category: Optional[LogCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """导出日志"""
        try:
            logs = self.search_logs(
                category=category,
                start_time=start_time,
                end_time=end_time,
                limit=10000  # 增加导出限制
            )
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "filters": {
                    "category": category.value if category else "all",
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                },
                "total_entries": len(logs),
                "logs": logs
            }
            
            if format == "json":
                return {
                    "success": True,
                    "data": json.dumps(export_data, indent=2, ensure_ascii=False),
                    "filename": f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "content_type": "application/json"
                }
            else:
                return {"success": False, "error": "不支持的导出格式"}
                
        except Exception as e:
            logging.error(f"导出日志失败: {e}")
            return {"success": False, "error": str(e)}

# 全局日志管理器实例
log_manager = LogManager()

# 便捷的日志记录函数
def log_system(level: LogLevel, message: str, **kwargs):
    """记录系统日志"""
    log_manager.log(level, LogCategory.SYSTEM, message, **kwargs)

def log_access(message: str, **kwargs):
    """记录访问日志"""
    log_manager.log(LogLevel.INFO, LogCategory.ACCESS, message, **kwargs)

def log_error(message: str, **kwargs):
    """记录错误日志"""
    log_manager.log(LogLevel.ERROR, LogCategory.ERROR, message, **kwargs)

def log_security(level: LogLevel, message: str, **kwargs):
    """记录安全日志"""
    log_manager.log(level, LogCategory.SECURITY, message, **kwargs)

def log_audit(message: str, **kwargs):
    """记录审计日志"""
    log_manager.log(LogLevel.INFO, LogCategory.AUDIT, message, **kwargs)

def log_performance(message: str, **kwargs):
    """记录性能日志"""
    log_manager.log(LogLevel.INFO, LogCategory.PERFORMANCE, message, **kwargs)