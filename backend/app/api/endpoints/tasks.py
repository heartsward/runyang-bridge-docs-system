# -*- coding: utf-8 -*-
"""
后台任务API端点
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.background_tasks import get_task_manager
from app.crud import document as crud_document

router = APIRouter()

@router.get("/status/{task_id}", summary="获取任务状态")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取指定任务的状态"""
    task_manager = get_task_manager()
    status = task_manager.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status

@router.get("/document/{document_id}/extraction-status", summary="获取文档提取状态")
def get_document_extraction_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取文档的内容提取状态"""
    # 检查文档是否存在
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    task_manager = get_task_manager()
    status = task_manager.get_document_extraction_status(document_id)
    
    # 如果没有后台任务，检查数据库中的提取状态
    if not status:
        if document.content_extracted is True:
            return {
                "status": "completed",
                "progress": 100,
                "content_length": len(document.content) if document.content else 0,
                "extraction_success": True
            }
        elif document.content_extracted is False:
            return {
                "status": "failed",
                "progress": 0,
                "error": document.content_extraction_error,
                "extraction_success": False
            }
        else:
            return {
                "status": "pending",
                "progress": 0,
                "extraction_success": None
            }
    
    return status

@router.post("/document/{document_id}/retry-extraction", summary="重新提取文档内容")
def retry_document_extraction(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重新提取文档内容"""
    # 检查权限：只有管理员才能操作
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以操作")
    
    # 检查文档是否存在
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path:
        raise HTTPException(status_code=400, detail="文档没有关联文件")
    
    # 重置提取状态
    document.content = None
    document.content_extracted = None
    document.content_extraction_error = None
    db.commit()
    
    # 添加提取任务
    task_manager = get_task_manager()
    task_id = task_manager.add_content_extraction_task(
        document_id=document.id,
        file_path=document.file_path,
        title=document.title
    )
    
    return {
        "message": "已添加到提取队列",
        "task_id": task_id,
        "document_id": document.id
    }