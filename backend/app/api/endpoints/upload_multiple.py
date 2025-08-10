from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.document import Document

router = APIRouter()

@router.post("/upload-multiple", response_model=List[Document], summary="批量上传文档")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    description: str = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量上传文档文件 - 仅管理员可操作
    """
    # 检查权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以上传文档")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="最多只能同时上传10个文件")
    
    # 简化版本：只返回文件信息
    results = []
    for file in files:
        # 创建一个简单的响应
        doc_info = {
            "id": 999,  # 临时ID
            "title": file.filename.rsplit('.', 1)[0] if file.filename else "未知文件",
            "description": description,
            "file_name": file.filename,
            "file_size": file.size if hasattr(file, 'size') else 0,
            "file_type": file.filename.rsplit('.', 1)[-1] if file.filename and '.' in file.filename else "unknown",
            "tags": tags.split(',') if tags else [],
            "status": "uploaded",
            "content_extracted": None,
            "ai_summary": None,
            "created_at": "2025-08-06T12:00:00",
            "updated_at": None,
            "owner": {"username": current_user.username, "full_name": "管理员"}
        }
        results.append(doc_info)
    
    return results

@router.get("/test", summary="测试端点")
async def test_endpoint():
    """测试端点"""
    return {"message": "多文件上传路由器工作正常"}