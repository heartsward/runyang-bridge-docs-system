import os
import uuid
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.crud import document as crud_document
from app.crud.asset import asset as asset_crud
from app.models.user import User
from app.models.asset import AssetStatus, AssetType, NetworkLocation
from app.schemas.document import Document, DocumentCreate
from app.schemas.asset import AssetCreate
from app.services.background_tasks import get_task_manager
from app.services.content_extractor import ContentExtractor
from app.services.document_analyzer import DocumentAnalyzer

router = APIRouter()


# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_size(file: UploadFile) -> int:
    """获取文件大小"""
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置到文件开头
    return file_size


@router.post("/upload", response_model=Document, summary="上传文档文件")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(None),
    tags: str = Form(None),  # 逗号分隔的标签字符串
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    上传文档文件并创建文档记录 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能上传文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以上传文档")
    
    # 检查文件类型
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # 检查文件大小
    file_size = get_file_size(file)
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
        )
    
    # 生成唯一文件名
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 处理标签
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # 创建文档记录
    document_data = DocumentCreate(
        title=title,
        description=description,
        category_id=category_id,
        tags=tag_list,
    )
    
    document = crud_document.create(db=db, obj_in=document_data, owner_id=current_user.id)
    
    # 更新文件相关信息
    document.file_path = file_path
    document.file_name = file.filename
    document.file_size = file_size
    document.file_type = file_extension
    document.mime_type = file.content_type
    
    db.commit()
    db.refresh(document)
    
    # 异步提取文档内容
    try:
        extractor = ContentExtractor()
        task_manager = get_task_manager()
        
        if extractor.is_supported_file(document.file_path):
            # 添加到后台任务队列
            task_id = task_manager.add_content_extraction_task(
                document_id=document.id,
                file_path=document.file_path,
                title=document.title
            )
            print(f"🔄 已添加内容提取任务: {document.title} - 任务ID: {task_id}")
            
            # 标记为正在提取
            document.content_extracted = None  # None表示正在提取中
            document.content_extraction_error = None
        else:
            document.content_extracted = False
            document.content_extraction_error = "不支持的文件格式"
            print(f"⚠️ 不支持的文件格式: {document.title}")
            
        db.commit()
        db.refresh(document)
            
    except Exception as e:
        # 任务添加失败不影响文档上传成功
        error_msg = f"添加提取任务失败: {str(e)}"
        print(f"❌ {error_msg} - 文档: {document.title}")
        document.content_extracted = False
        document.content_extraction_error = error_msg
        db.commit()
    
    # 自动触发智能分析
    try:
        analyzer = DocumentAnalyzer()
        
        analysis_result = analyzer.analyze_document(
            file_path=document.file_path,
            file_type=document.file_type,
            title=document.title
        )
        
        if analysis_result["success"]:
            # 更新AI分析结果
            document.ai_summary = analysis_result["summary"]
            document.ai_tags = [kw["keyword"] for kw in analysis_result["keywords"][:10]]
            document.confidence_score = analysis_result["document_type"]["confidence"]
            
            db.commit()
            db.refresh(document)
            
    except Exception as e:
        # 分析失败不影响文档上传成功
        print(f"自动分析文档失败: {str(e)}")
    
    return document


@router.get("/download/{document_id}", summary="下载文档文件")
def download_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """
    下载文档文件
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 增加下载次数
    user_id = current_user.id if current_user else None
    crud_document.increment_download_count(db=db, document_id=document_id, user_id=user_id)
    
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type='application/octet-stream'
    )


@router.post("/upload-multiple", response_model=List[Document], summary="批量上传文档")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    category_id: int = Form(None),
    description: str = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量上传文档文件 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能上传文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以上传文档")
    
    if len(files) > 10:  # 限制最多10个文件
        raise HTTPException(status_code=400, detail="最多只能同时上传10个文件")
    
    uploaded_documents = []
    
    for file in files:
        try:
            # 检查文件类型和大小
            if not allowed_file(file.filename):
                continue  # 跳过不支持的文件类型
            
            file_size = get_file_size(file)
            if file_size > settings.MAX_FILE_SIZE:
                continue  # 跳过过大的文件
            
            # 生成唯一文件名并保存
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # 处理标签
            tag_list = []
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # 创建文档记录
            document_data = DocumentCreate(
                title=file.filename.rsplit('.', 1)[0],  # 使用文件名作为标题
                description=description,
                category_id=category_id,
                tags=tag_list,
            )
            
            document = crud_document.create(db=db, obj_in=document_data, owner_id=current_user.id)
            
            # 更新文件信息
            document.file_path = file_path
            document.file_name = file.filename
            document.file_size = file_size
            document.file_type = file_extension
            document.mime_type = file.content_type
            
            db.commit()
            db.refresh(document)
            
            # 异步提取文档内容
            try:
                extractor = ContentExtractor()
                task_manager = get_task_manager()
                
                if extractor.is_supported_file(document.file_path):
                    # 添加到后台任务队列
                    task_manager.add_content_extraction_task(
                        document_id=document.id,
                        file_path=document.file_path,
                        title=document.title
                    )
                    # 标记为正在提取
                    document.content_extracted = None
                    document.content_extraction_error = None
                else:
                    document.content_extracted = False
                    document.content_extraction_error = "不支持的文件格式"
                    
                db.commit()
                db.refresh(document)
                    
            except Exception as e:
                # 任务添加失败不影响文档上传成功
                document.content_extracted = False
                document.content_extraction_error = f"添加提取任务失败: {str(e)}"
                db.commit()
            
            uploaded_documents.append(document)
            
        except Exception as e:
            # 记录错误但继续处理其他文件
            continue
    
    return uploaded_documents






