import os
import uuid
import re
from typing import List, Optional
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

router = APIRouter()


# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_safe_filename(title: str, file_extension: str, upload_dir: str) -> str:
    """
    根据文档标题生成安全且唯一的文件名
    
    Args:
        title: 文档标题
        file_extension: 文件扩展名（不包含点号）
        upload_dir: 上传目录路径
    
    Returns:
        安全的唯一文件名
    """
    # 清理标题，保留安全字符（包括中文字符）
    def is_safe_char(c):
        # 允许ASCII字母、数字、常用标点
        if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_()[]（）【】":
            return True
        # 允许中文字符（CJK统一汉字）
        if '\u4e00' <= c <= '\u9fff':
            return True
        # 允许中文标点符号
        if c in '，。！？；：、""''《》':
            return True
        return False
    
    safe_title = "".join(c if is_safe_char(c) else "_" for c in title)
    
    # 移除连续的下划线和首尾下划线
    safe_title = re.sub(r'_+', '_', safe_title).strip('_')
    
    # 限制长度（避免文件名过长）- 修复长文件名处理
    max_title_length = 80  # 增加允许的最大长度
    if len(safe_title) > max_title_length:
        safe_title = safe_title[:max_title_length].rstrip('_')
    
    # 如果清理后的标题为空，使用默认名称
    if not safe_title:
        safe_title = "document"
    
    # 生成基础文件名
    base_filename = f"{safe_title}.{file_extension}"
    full_path = os.path.join(upload_dir, base_filename)
    
    # 修复冲突检测逻辑
    final_filename = base_filename
    
    # 检查文件是否已存在，如果存在则添加数字后缀
    counter = 1
    while os.path.exists(full_path):
        final_filename = f"{safe_title}_{counter}.{file_extension}"
        full_path = os.path.join(upload_dir, final_filename)
        counter += 1
        
        # 防止无限循环
        if counter > 9999:
            # 如果仍然冲突，回退到UUID方案
            final_filename = f"{safe_title}_{str(uuid.uuid4())[:8]}.{file_extension}"
            # 最终检查UUID方案是否也冲突
            uuid_full_path = os.path.join(upload_dir, final_filename)
            if os.path.exists(uuid_full_path):
                # 极端情况：使用完整UUID
                final_filename = f"{str(uuid.uuid4())}.{file_extension}"
            break
    
    return final_filename


def get_file_size(file: UploadFile) -> int:
    """获取文件大小"""
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置到文件开头
    return file_size


@router.post("/", response_model=Document, summary="上传文档文件")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),  # 逗号分隔的标签字符串
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    上传文档文件并创建文档记录 - 仅管理员可操作
    """
    # 调试：打印接收到的数据
    try:
        pass
        print(f"  文件名: {file.filename}")
        print(f"  标题: {repr(title)}")
        print(f"  描述: {repr(description)}")
        print(f"  分类ID: {repr(category_id)}")
        print(f"  标签: {repr(tags)}")
        print(f"  用户: {current_user.username if current_user else 'None'}")
    except Exception as debug_error:
        print(f"[ERROR] 调试输出失败: {debug_error}")
    
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
    
    # 生成基于标题的安全文件名
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    safe_filename = generate_safe_filename(title, file_extension, settings.UPLOAD_DIR)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    # 最终确认文件路径不冲突（防止并发上传问题）
    final_counter = 1
    original_safe_filename = safe_filename
    while os.path.exists(file_path):
        # 从原始文件名重新生成，避免重复后缀
        name_without_ext = original_safe_filename.rsplit('.', 1)[0]
        # 移除已有的数字后缀
        if '_' in name_without_ext and name_without_ext.split('_')[-1].isdigit():
            base_name = '_'.join(name_without_ext.split('_')[:-1])
        else:
            base_name = name_without_ext
        
        safe_filename = f"{base_name}_{final_counter}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        final_counter += 1
        
        # 防止无限循环
        if final_counter > 9999:
            safe_filename = f"{base_name}_{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
            break
    
    pass
    
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
    pass
    
    try:
        document_data = DocumentCreate(
            title=title,
            description=description,
            category_id=category_id,
            tags=tag_list,
        )
        pass
    except Exception as e:
        print(f"[ERROR] DocumentCreate对象创建失败: {e}")
        raise HTTPException(status_code=422, detail=f"数据验证失败: {str(e)}")
    
    try:
        document = crud_document.create(db=db, obj_in=document_data, owner_id=current_user.id)
        pass
    except Exception as e:
        print(f"[ERROR] 数据库记录创建失败: {e}")
        raise HTTPException(status_code=422, detail=f"数据库创建失败: {str(e)}")
    
    # 更新文件相关信息
    document.file_path = file_path
    document.file_name = safe_filename  # 使用基于标题生成的文件名，而不是原始文件名
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
            print(f"[INFO] 已添加内容提取任务: {document.title} - 任务ID: {task_id}")
            
            # 标记为正在提取
            document.content_extracted = None  # None表示正在提取中
            document.content_extraction_error = None
        else:
            document.content_extracted = False
            document.content_extraction_error = "不支持的文件格式"
            print(f"[WARNING] 不支持的文件格式: {document.title}")
            
        db.commit()
        db.refresh(document)
            
    except Exception as e:
        # 任务添加失败不影响文档上传成功
        error_msg = f"添加提取任务失败: {str(e)}"
        print(f"[ERROR] {error_msg} - 文档: {document.title}")
        document.content_extracted = False
        document.content_extraction_error = error_msg
        db.commit()
    
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
    
    # 创建响应并设置正确的中文文件名编码
    from urllib.parse import quote
    from fastapi.responses import FileResponse
    
    # 使用 UTF-8 编码中文文件名
    encoded_filename = quote(document.file_name.encode('utf-8'))
    
    response = FileResponse(
        path=document.file_path,
        media_type='application/octet-stream'
    )
    
    # 设置支持中文的 Content-Disposition 头
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    
    return response


@router.post("/multiple", response_model=List[Document], summary="批量上传文档")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
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
            
            # 生成基于文件名的安全文件名
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            file_title = file.filename.rsplit('.', 1)[0]  # 使用原文件名作为标题
            safe_filename = generate_safe_filename(file_title, file_extension, settings.UPLOAD_DIR)
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
            
            # 最终确认文件路径不冲突（防止并发上传问题）
            final_counter = 1
            original_safe_filename = safe_filename
            while os.path.exists(file_path):
                # 从原始文件名重新生成，避免重复后缀
                name_without_ext = original_safe_filename.rsplit('.', 1)[0]
                # 移除已有的数字后缀
                if '_' in name_without_ext and name_without_ext.split('_')[-1].isdigit():
                    base_name = '_'.join(name_without_ext.split('_')[:-1])
                else:
                    base_name = name_without_ext
                
                safe_filename = f"{base_name}_{final_counter}.{file_extension}"
                file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
                final_counter += 1
                
                # 防止无限循环
                if final_counter > 9999:
                    safe_filename = f"{base_name}_{uuid.uuid4()}.{file_extension}"
                    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
                    break
            
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
            document.file_name = safe_filename  # 使用基于标题生成的文件名，而不是原始文件名
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






