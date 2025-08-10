# -*- coding: utf-8 -*-
"""
数据库任务管理器 - 适配数据库存储
"""
import os
import json
import time
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

# 导入数据库和模型
from app.db.database import SessionLocal
from app import crud

logger = logging.getLogger(__name__)

class DatabaseTaskManager:
    """数据库任务管理器 - 与数据库存储配合"""
    
    def __init__(self, content_extractor=None):
        self.content_extractor = content_extractor
        self.task_queue = []
        self.is_running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        
        # 创建任务状态存储目录
        self.task_dir = Path("./task_status")
        self.task_dir.mkdir(exist_ok=True)
        
    def start_worker(self):
        """启动后台任务处理器"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("数据库任务处理器已启动")
    
    def stop_worker(self):
        """停止后台任务处理器"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("数据库任务处理器已停止")
    
    def add_content_extraction_task(self, document_id: int, file_path: str, title: str) -> str:
        """添加内容提取任务"""
        task_id = f"extract_{document_id}_{int(time.time())}"
        
        task = {
            "task_id": task_id,
            "task_type": "content_extraction",
            "document_id": document_id,
            "file_path": file_path,
            "title": title,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "progress": 0
        }
        
        # 保存任务状态
        self._save_task_status(task_id, task)
        
        # 添加到队列
        with self.lock:
            self.task_queue.append(task)
        
        logger.info(f"已添加内容提取任务: {task_id} - {title}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        status_file = self.task_dir / f"{task_id}.json"
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取任务状态失败: {e}")
        return None
    
    def get_document_extraction_status(self, document_id: int) -> Optional[Dict[str, Any]]:
        """获取文档的提取状态"""
        # 查找最新的提取任务
        for task_file in sorted(self.task_dir.glob(f"extract_{document_id}_*.json"), reverse=True):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                    return {
                        "task_id": task_data["task_id"],
                        "status": task_data["status"],
                        "progress": task_data.get("progress", 0),
                        "error": task_data.get("error"),
                        "created_at": task_data["created_at"],
                        "completed_at": task_data.get("completed_at")
                    }
            except Exception:
                continue
        return None
    
    def _save_task_status(self, task_id: str, task_data: Dict[str, Any]):
        """保存任务状态"""
        status_file = self.task_dir / f"{task_id}.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务状态失败: {e}")
    
    def _worker_loop(self):
        """后台任务处理循环"""
        logger.info("数据库任务处理循环已启动")
        
        while self.is_running:
            try:
                task = None
                
                # 从队列获取任务
                with self.lock:
                    if self.task_queue:
                        task = self.task_queue.pop(0)
                
                if task:
                    self._process_task(task)
                else:
                    # 没有任务时短暂休眠
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"后台任务处理异常: {e}")
                time.sleep(5)  # 出错时等待5秒
    
    def _process_task(self, task: Dict[str, Any]):
        """处理单个任务"""
        task_id = task["task_id"]
        task_type = task["task_type"]
        
        logger.info(f"开始处理任务: {task_id} - {task_type}")
        
        # 更新任务状态为进行中
        task["status"] = "processing"
        task["started_at"] = datetime.utcnow().isoformat()
        task["progress"] = 10
        self._save_task_status(task_id, task)
        
        try:
            if task_type == "content_extraction":
                self._process_content_extraction(task)
            else:
                raise ValueError(f"未知任务类型: {task_type}")
                
        except Exception as e:
            logger.error(f"任务处理失败: {task_id} - {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.utcnow().isoformat()
            self._save_task_status(task_id, task)
    
    def _process_content_extraction(self, task: Dict[str, Any]):
        """处理内容提取任务 - 数据库版本"""
        document_id = task["document_id"]
        file_path = task["file_path"]
        title = task["title"]
        task_id = task["task_id"]
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")
        
        # 更新进度
        task["progress"] = 30
        self._save_task_status(task_id, task)
        
        # 检查是否支持提取
        if not self.content_extractor or not self.content_extractor.is_supported_file(file_path):
            raise Exception("不支持的文件格式或提取器不可用")
        
        # 更新进度
        task["progress"] = 50
        self._save_task_status(task_id, task)
        
        # 开始提取内容
        logger.info(f"开始提取文档内容: {title}")
        content, error = self.content_extractor.extract_content(file_path)
        
        # 更新进度
        task["progress"] = 80
        self._save_task_status(task_id, task)
        
        # 更新数据库中的文档
        db = SessionLocal()
        try:
            # 获取文档
            document_obj = crud.document.get(db, id=document_id)
            if not document_obj:
                raise Exception(f"数据库中找不到文档: {document_id}")
            
            if content:
                # 更新文档内容
                update_data = {
                    "content": content,
                    "content_extracted": True,
                    "extraction_error": None
                }
                crud.document.update(db, db_obj=document_obj, obj_in=update_data)
                db.commit()
                
                logger.info(f"内容提取成功: {title}, 内容长度: {len(content)}")
                
                # 任务成功
                task["status"] = "completed"
                task["result"] = {
                    "content_length": len(content),
                    "extraction_success": True
                }
            else:
                # 更新失败状态
                update_data = {
                    "content_extracted": False,
                    "extraction_error": error or "内容提取失败"
                }
                crud.document.update(db, db_obj=document_obj, obj_in=update_data)
                db.commit()
                
                logger.warning(f"内容提取失败: {title}, 错误: {error}")
                
                # 任务失败
                task["status"] = "failed"
                task["error"] = error or "内容提取失败"
                
        except Exception as e:
            db.rollback()
            logger.error(f"更新数据库失败: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
        finally:
            db.close()
        
        # 完成任务
        task["progress"] = 100
        task["completed_at"] = datetime.utcnow().isoformat()
        self._save_task_status(task_id, task)
        
        logger.info(f"任务完成: {task_id}")