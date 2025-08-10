"""
系统监控服务
"""
import os
import psutil
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    uptime_seconds: int

@dataclass
class ApplicationMetrics:
    """应用指标数据类"""
    timestamp: str
    response_time_avg: float
    error_rate: float
    requests_per_minute: int
    active_users: int
    database_connections: int
    cache_hit_rate: float
    queue_size: int

class SystemMonitor:
    """系统监控服务"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[ApplicationMetrics] = []
        self.max_history_size = 1440  # 24小时的分钟数
        
        # 阈值配置
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0,
            'response_time_warning': 1000.0,  # ms
            'response_time_critical': 3000.0,  # ms
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.10   # 10%
        }
        
        # 网络统计初始值
        self.last_network_stats = psutil.net_io_counters()
        self.last_network_time = time.time()
    
    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # 网络使用情况
            current_network = psutil.net_io_counters()
            current_time = time.time()
            
            time_delta = current_time - self.last_network_time
            if time_delta > 0:
                sent_delta = current_network.bytes_sent - self.last_network_stats.bytes_sent
                recv_delta = current_network.bytes_recv - self.last_network_stats.bytes_recv
                
                network_sent_mb = (sent_delta / time_delta) / (1024**2)
                network_recv_mb = (recv_delta / time_delta) / (1024**2)
            else:
                network_sent_mb = 0
                network_recv_mb = 0
            
            self.last_network_stats = current_network
            self.last_network_time = current_time
            
            # 网络连接数
            try:
                connections = len(psutil.net_connections())
            except (psutil.PermissionError, psutil.AccessDenied):
                connections = 0
            
            # 系统运行时间
            uptime_seconds = int(time.time() - self.start_time)
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=round(disk_percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                network_sent_mb=round(network_sent_mb, 2),
                network_recv_mb=round(network_recv_mb, 2),
                active_connections=connections,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0, memory_percent=0, memory_used_gb=0, memory_total_gb=0,
                disk_percent=0, disk_used_gb=0, disk_total_gb=0,
                network_sent_mb=0, network_recv_mb=0, active_connections=0,
                uptime_seconds=0
            )
    
    def get_application_metrics(self, db: Session) -> ApplicationMetrics:
        """获取应用指标"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 数据库连接数（模拟）
            database_connections = self._get_database_connections(db)
            
            # 活跃用户数（最近15分钟有活动的用户）
            active_users = self._get_active_users(db)
            
            # 错误率（模拟）
            error_rate = self._calculate_error_rate()
            
            # 平均响应时间（模拟）
            response_time_avg = self._calculate_avg_response_time()
            
            # 每分钟请求数（模拟）
            requests_per_minute = self._calculate_requests_per_minute()
            
            # 缓存命中率（模拟）
            cache_hit_rate = self._calculate_cache_hit_rate()
            
            # 队列大小（模拟）
            queue_size = 0
            
            return ApplicationMetrics(
                timestamp=timestamp,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                requests_per_minute=requests_per_minute,
                active_users=active_users,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                queue_size=queue_size
            )
            
        except Exception as e:
            logger.error(f"获取应用指标失败: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                response_time_avg=0, error_rate=0, requests_per_minute=0,
                active_users=0, database_connections=0, cache_hit_rate=0,
                queue_size=0
            )
    
    def collect_metrics(self, db: Session):
        """收集指标"""
        # 收集系统指标
        system_metrics = self.get_system_metrics()
        self.metrics_history.append(system_metrics)
        
        # 收集应用指标
        app_metrics = self.get_application_metrics(db)
        self.app_metrics_history.append(app_metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
        
        if len(self.app_metrics_history) > self.max_history_size:
            self.app_metrics_history.pop(0)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        if not self.metrics_history:
            return {
                "status": "unknown",
                "message": "无监控数据"
            }
        
        latest_metrics = self.metrics_history[-1]
        latest_app_metrics = self.app_metrics_history[-1] if self.app_metrics_history else None
        
        issues = []
        warnings = []
        
        # 检查系统指标
        if latest_metrics.cpu_percent > self.thresholds['cpu_critical']:
            issues.append(f"CPU使用率过高: {latest_metrics.cpu_percent:.1f}%")
        elif latest_metrics.cpu_percent > self.thresholds['cpu_warning']:
            warnings.append(f"CPU使用率较高: {latest_metrics.cpu_percent:.1f}%")
        
        if latest_metrics.memory_percent > self.thresholds['memory_critical']:
            issues.append(f"内存使用率过高: {latest_metrics.memory_percent:.1f}%")
        elif latest_metrics.memory_percent > self.thresholds['memory_warning']:
            warnings.append(f"内存使用率较高: {latest_metrics.memory_percent:.1f}%")
        
        if latest_metrics.disk_percent > self.thresholds['disk_critical']:
            issues.append(f"磁盘使用率过高: {latest_metrics.disk_percent:.1f}%")
        elif latest_metrics.disk_percent > self.thresholds['disk_warning']:
            warnings.append(f"磁盘使用率较高: {latest_metrics.disk_percent:.1f}%")
        
        # 检查应用指标
        if latest_app_metrics:
            if latest_app_metrics.error_rate > self.thresholds['error_rate_critical']:
                issues.append(f"错误率过高: {latest_app_metrics.error_rate:.2%}")
            elif latest_app_metrics.error_rate > self.thresholds['error_rate_warning']:
                warnings.append(f"错误率较高: {latest_app_metrics.error_rate:.2%}")
            
            if latest_app_metrics.response_time_avg > self.thresholds['response_time_critical']:
                issues.append(f"响应时间过长: {latest_app_metrics.response_time_avg:.0f}ms")
            elif latest_app_metrics.response_time_avg > self.thresholds['response_time_warning']:
                warnings.append(f"响应时间较长: {latest_app_metrics.response_time_avg:.0f}ms")
        
        # 确定整体状态
        if issues:
            status = "critical"
            message = f"发现 {len(issues)} 个严重问题"
        elif warnings:
            status = "warning"
            message = f"发现 {len(warnings)} 个警告"
        else:
            status = "healthy"
            message = "系统运行正常"
        
        return {
            "status": status,
            "message": message,
            "issues": issues,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics_history:
            return {"error": "无监控数据"}
        
        # 计算时间范围
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        filtered_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        filtered_app_metrics = [
            m for m in self.app_metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not filtered_metrics:
            return {"error": "指定时间范围内无数据"}
        
        # 计算系统指标统计
        cpu_values = [m.cpu_percent for m in filtered_metrics]
        memory_values = [m.memory_percent for m in filtered_metrics]
        disk_values = [m.disk_percent for m in filtered_metrics]
        
        system_summary = {
            "cpu": {
                "avg": round(sum(cpu_values) / len(cpu_values), 2),
                "max": round(max(cpu_values), 2),
                "min": round(min(cpu_values), 2)
            },
            "memory": {
                "avg": round(sum(memory_values) / len(memory_values), 2),
                "max": round(max(memory_values), 2),
                "min": round(min(memory_values), 2)
            },
            "disk": {
                "avg": round(sum(disk_values) / len(disk_values), 2),
                "max": round(max(disk_values), 2),
                "min": round(min(disk_values), 2)
            }
        }
        
        # 计算应用指标统计
        app_summary = {}
        if filtered_app_metrics:
            response_times = [m.response_time_avg for m in filtered_app_metrics]
            error_rates = [m.error_rate for m in filtered_app_metrics]
            
            app_summary = {
                "response_time": {
                    "avg": round(sum(response_times) / len(response_times), 2),
                    "max": round(max(response_times), 2),
                    "min": round(min(response_times), 2)
                },
                "error_rate": {
                    "avg": round(sum(error_rates) / len(error_rates), 4),
                    "max": round(max(error_rates), 4),
                    "min": round(min(error_rates), 4)
                }
            }
        
        return {
            "time_range_hours": hours,
            "data_points": len(filtered_metrics),
            "system_metrics": system_summary,
            "application_metrics": app_summary,
            "latest_health": self.get_health_status()
        }
    
    def export_metrics(self, hours: int = 24, format: str = "json") -> Dict[str, Any]:
        """导出指标数据"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 过滤数据
            filtered_system = [
                asdict(m) for m in self.metrics_history
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
            
            filtered_app = [
                asdict(m) for m in self.app_metrics_history
                if datetime.fromisoformat(m.timestamp) >= cutoff_time
            ]
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "time_range_hours": hours,
                "system_metrics": filtered_system,
                "application_metrics": filtered_app
            }
            
            if format == "json":
                return {
                    "success": True,
                    "data": json.dumps(export_data, indent=2),
                    "filename": f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "content_type": "application/json"
                }
            else:
                return {"success": False, "error": "不支持的导出格式"}
                
        except Exception as e:
            logger.error(f"导出指标失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 私有方法
    def _get_database_connections(self, db: Session) -> int:
        """获取数据库连接数"""
        try:
            # 对于SQLite，连接数通常很少，这里返回一个模拟值
            return 1
        except Exception:
            return 0
    
    def _get_active_users(self, db: Session) -> int:
        """获取活跃用户数"""
        try:
            # 获取最近15分钟有活动的用户数
            cutoff_time = datetime.now() - timedelta(minutes=15)
            
            result = db.execute(text("""
                SELECT COUNT(DISTINCT user_id) 
                FROM (
                    SELECT user_id FROM document_views 
                    WHERE created_at >= :cutoff_time
                    UNION
                    SELECT user_id FROM asset_views 
                    WHERE created_at >= :cutoff_time
                    UNION
                    SELECT user_id FROM search_logs 
                    WHERE created_at >= :cutoff_time
                ) active_users
                WHERE user_id IS NOT NULL
            """), {"cutoff_time": cutoff_time}).scalar()
            
            return result or 0
            
        except Exception as e:
            logger.warning(f"获取活跃用户数失败: {e}")
            return 0
    
    def _calculate_error_rate(self) -> float:
        """计算错误率（模拟）"""
        # 这里可以集成实际的错误日志分析
        # 目前返回一个模拟的低错误率
        import random
        return random.uniform(0.01, 0.03)
    
    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间（模拟）"""
        # 这里可以集成实际的响应时间统计
        # 目前返回一个模拟值
        import random
        return random.uniform(100, 500)
    
    def _calculate_requests_per_minute(self) -> int:
        """计算每分钟请求数（模拟）"""
        # 这里可以集成实际的请求统计
        # 目前返回一个模拟值
        import random
        return random.randint(10, 100)
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率（模拟）"""
        # 这里可以集成实际的缓存统计
        # 目前返回一个模拟的高命中率
        import random
        return random.uniform(0.85, 0.95)

# 全局监控服务实例
system_monitor = SystemMonitor()