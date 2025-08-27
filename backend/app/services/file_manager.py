# -*- coding: utf-8 -*-
"""
文件管理服务
提供安全的文件操作，包括删除、备份、孤儿文件检测等功能
"""
import os
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import tempfile
import glob

logger = logging.getLogger(__name__)

class FileManagerService:
    """
    文件管理服务类
    提供安全的文件操作和管理功能
    """
    
    def __init__(self, uploads_dir: str = "uploads", backup_dir: str = "backups"):
        self.uploads_dir = Path(uploads_dir)
        self.backup_dir = Path(backup_dir)
        
        # 确保目录存在
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"文件管理器初始化完成 - 上传目录: {self.uploads_dir}, 备份目录: {self.backup_dir}")
    
    def safe_delete_file(self, file_path: str, backup_before_delete: bool = False) -> Dict[str, Any]:
        """
        安全删除文件
        
        Args:
            file_path: 要删除的文件路径
            backup_before_delete: 删除前是否备份
            
        Returns:
            删除操作的结果字典
        """
        result = {
            "success": False,
            "file_path": file_path,
            "existed": False,
            "deleted": False,
            "backed_up": False,
            "backup_path": None,
            "error": None,
            "file_size": 0
        }
        
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not file_path_obj.exists():
                result["error"] = "文件不存在"
                logger.warning(f"尝试删除不存在的文件: {file_path}")
                return result
            
            result["existed"] = True
            result["file_size"] = file_path_obj.stat().st_size
            
            # 检查文件是否在允许的目录内（安全检查）
            if not self._is_file_in_allowed_directory(file_path_obj):
                result["error"] = "文件路径不在允许的目录内"
                logger.error(f"尝试删除不安全路径的文件: {file_path}")
                return result
            
            # 备份文件（如果需要）
            if backup_before_delete:
                backup_result = self._backup_file(file_path_obj)
                if backup_result["success"]:
                    result["backed_up"] = True
                    result["backup_path"] = backup_result["backup_path"]
                    logger.info(f"文件已备份: {file_path} -> {backup_result['backup_path']}")
                else:
                    result["error"] = f"备份失败: {backup_result['error']}"
                    logger.error(f"文件备份失败: {file_path} - {backup_result['error']}")
                    return result
            
            # 删除文件
            file_path_obj.unlink()
            result["deleted"] = True
            result["success"] = True
            
            logger.info(f"文件删除成功: {file_path} (大小: {result['file_size']} 字节)")
            
        except PermissionError as e:
            result["error"] = f"权限不足: {str(e)}"
            logger.error(f"删除文件权限不足: {file_path} - {str(e)}")
        except Exception as e:
            result["error"] = f"删除失败: {str(e)}"
            logger.error(f"删除文件异常: {file_path} - {str(e)}")
        
        return result
    
    def detect_orphan_files(self, db_file_paths: List[str]) -> Dict[str, Any]:
        """
        检测孤儿文件
        
        Args:
            db_file_paths: 数据库中所有文档的文件路径列表
            
        Returns:
            孤儿文件检测结果
        """
        result = {
            "total_files": 0,
            "orphan_files": [],
            "orphan_count": 0,
            "orphan_total_size": 0,
            "valid_files": [],
            "scan_time": datetime.now().isoformat()
        }
        
        try:
            # 获取uploads目录中的所有文件
            upload_files = list(self.uploads_dir.glob("*"))
            upload_files = [f for f in upload_files if f.is_file()]  # 只要文件，不要目录
            
            result["total_files"] = len(upload_files)
            
            # 提取数据库路径中的文件名
            db_filenames = set()
            for db_path in db_file_paths:
                if db_path:
                    filename = os.path.basename(db_path)
                    db_filenames.add(filename)
            
            # 检查每个物理文件
            for file_path in upload_files:
                filename = file_path.name
                file_size = file_path.stat().st_size
                
                if filename not in db_filenames:
                    # 孤儿文件
                    result["orphan_files"].append({
                        "filename": filename,
                        "full_path": str(file_path),
                        "size": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2),
                        "modified_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                    result["orphan_total_size"] += file_size
                else:
                    # 有效文件
                    result["valid_files"].append({
                        "filename": filename,
                        "size": file_size
                    })
            
            result["orphan_count"] = len(result["orphan_files"])
            result["orphan_total_size_mb"] = round(result["orphan_total_size"] / (1024 * 1024), 2)
            
            logger.info(f"孤儿文件检测完成 - 总文件: {result['total_files']}, 孤儿文件: {result['orphan_count']}, 孤儿文件大小: {result['orphan_total_size_mb']}MB")
            
        except Exception as e:
            result["error"] = f"检测失败: {str(e)}"
            logger.error(f"孤儿文件检测异常: {str(e)}")
        
        return result
    
    def cleanup_orphan_files(self, orphan_files: List[Dict[str, Any]], backup_before_delete: bool = True) -> Dict[str, Any]:
        """
        清理孤儿文件
        
        Args:
            orphan_files: 要清理的孤儿文件列表
            backup_before_delete: 删除前是否备份
            
        Returns:
            清理操作结果
        """
        result = {
            "total_files": len(orphan_files),
            "deleted_files": [],
            "failed_files": [],
            "backed_up_files": [],
            "total_size_freed": 0,
            "cleanup_time": datetime.now().isoformat()
        }
        
        try:
            for orphan_file in orphan_files:
                file_path = orphan_file["full_path"]
                file_size = orphan_file["size"]
                
                delete_result = self.safe_delete_file(file_path, backup_before_delete)
                
                if delete_result["success"]:
                    result["deleted_files"].append({
                        "filename": orphan_file["filename"],
                        "size": file_size,
                        "backed_up": delete_result["backed_up"],
                        "backup_path": delete_result.get("backup_path")
                    })
                    result["total_size_freed"] += file_size
                    
                    if delete_result["backed_up"]:
                        result["backed_up_files"].append(orphan_file["filename"])
                else:
                    result["failed_files"].append({
                        "filename": orphan_file["filename"],
                        "error": delete_result["error"]
                    })
            
            result["deleted_count"] = len(result["deleted_files"])
            result["failed_count"] = len(result["failed_files"])
            result["total_size_freed_mb"] = round(result["total_size_freed"] / (1024 * 1024), 2)
            result["success"] = result["failed_count"] == 0
            
            logger.info(f"孤儿文件清理完成 - 删除: {result['deleted_count']}, 失败: {result['failed_count']}, 释放空间: {result['total_size_freed_mb']}MB")
            
        except Exception as e:
            result["error"] = f"清理失败: {str(e)}"
            logger.error(f"孤儿文件清理异常: {str(e)}")
        
        return result
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """
        获取存储使用情况
        
        Returns:
            存储使用统计
        """
        result = {
            "uploads_dir": str(self.uploads_dir),
            "backup_dir": str(self.backup_dir),
            "uploads_total_size": 0,
            "uploads_file_count": 0,
            "backup_total_size": 0,
            "backup_file_count": 0,
            "scan_time": datetime.now().isoformat()
        }
        
        try:
            # 统计uploads目录
            upload_files = list(self.uploads_dir.glob("*"))
            upload_files = [f for f in upload_files if f.is_file()]
            
            result["uploads_file_count"] = len(upload_files)
            result["uploads_total_size"] = sum(f.stat().st_size for f in upload_files)
            result["uploads_total_size_mb"] = round(result["uploads_total_size"] / (1024 * 1024), 2)
            
            # 统计backup目录
            if self.backup_dir.exists():
                backup_files = list(self.backup_dir.glob("**/*"))
                backup_files = [f for f in backup_files if f.is_file()]
                
                result["backup_file_count"] = len(backup_files)
                result["backup_total_size"] = sum(f.stat().st_size for f in backup_files)
                result["backup_total_size_mb"] = round(result["backup_total_size"] / (1024 * 1024), 2)
            
            logger.info(f"存储使用统计 - 上传文件: {result['uploads_file_count']}个({result['uploads_total_size_mb']}MB), 备份文件: {result['backup_file_count']}个({result.get('backup_total_size_mb', 0)}MB)")
            
        except Exception as e:
            result["error"] = f"统计失败: {str(e)}"
            logger.error(f"存储使用统计异常: {str(e)}")
        
        return result
    
    def _backup_file(self, file_path: Path) -> Dict[str, Any]:
        """
        备份文件到备份目录
        
        Args:
            file_path: 要备份的文件路径
            
        Returns:
            备份操作结果
        """
        result = {"success": False, "backup_path": None, "error": None}
        
        try:
            # 生成备份文件名：原文件名_时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            # 复制文件到备份目录
            shutil.copy2(file_path, backup_path)
            
            result["success"] = True
            result["backup_path"] = str(backup_path)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _is_file_in_allowed_directory(self, file_path: Path) -> bool:
        """
        检查文件是否在允许的目录内（安全检查）
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否在允许的目录内
        """
        try:
            # 解析路径以防止路径遍历攻击
            resolved_file = file_path.resolve()
            resolved_uploads = self.uploads_dir.resolve()
            
            # 检查文件是否在uploads目录或其子目录内
            return str(resolved_file).startswith(str(resolved_uploads))
        except Exception:
            return False