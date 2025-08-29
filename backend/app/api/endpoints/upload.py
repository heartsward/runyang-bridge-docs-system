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
    """检查文件扩展名是否允许 - 安全增强版本"""
    if not filename or '.' not in filename:
        return False
    
    # 防止路径遍历攻击
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    return file_extension in [ext.strip().lower() for ext in allowed_extensions]


def validate_file_content(file: UploadFile) -> bool:
    """验证文件内容（魔术字节检测） - 优化版本"""
    # 文件魔术字节签名
    MAGIC_SIGNATURES = {
        'pdf': [b'%PDF'],
        'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
        'docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'xlsx': [b'PK\x03\x04'],
        'xls': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
        'jpg': [b'\xff\xd8\xff'],
        'jpeg': [b'\xff\xd8\xff'],
        'png': [b'\x89PNG\r\n\x1a\n'],
    }
    
    # 读取文件前512字节用于检测
    original_position = file.file.tell()
    file.file.seek(0)
    file_header = file.file.read(512)
    file.file.seek(original_position)
    
    if not file_header:
        return False
    
    # 获取文件扩展名
    if not file.filename or '.' not in file.filename:
        return False
    
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    
    # 特殊处理文本文件（TXT, CSV）
    if file_extension in ['txt', 'csv', 'md']:
        return _validate_text_file(file_header)
    
    # 检查其他文件类型的魔术字节
    if file_extension in MAGIC_SIGNATURES:
        expected_signatures = MAGIC_SIGNATURES[file_extension]
        
        # 检查是否匹配任何一个预期的魔术字节
        for signature in expected_signatures:
            if file_header.startswith(signature):
                return True
        
        return False
    
    # 对于不在列表中的扩展名，默认拒绝
    return False


def _validate_text_file(file_header: bytes) -> bool:
    """验证文本文件内容"""
    # 检查常见的BOM标记
    bom_signatures = [
        b'\xff\xfe',        # UTF-16 LE
        b'\xfe\xff',        # UTF-16 BE  
        b'\xef\xbb\xbf',    # UTF-8 BOM
    ]
    
    # 如果有BOM标记，直接通过
    for bom in bom_signatures:
        if file_header.startswith(bom):
            return True
    
    # 对于无BOM的文件，进行内容检测
    try:
        # 尝试多种编码方式解码
        encodings = ['utf-8', 'ascii', 'gbk', 'utf-16']
        
        for encoding in encodings:
            try:
                decoded_content = file_header.decode(encoding)
                
                # 检查内容是否主要是可打印字符
                if _is_likely_text_content(decoded_content):
                    return True
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 如果所有编码都失败，进行二进制内容检查
        return _is_safe_binary_content(file_header)
        
    except Exception:
        return False


def _is_likely_text_content(content: str) -> bool:
    """检查内容是否像文本文件"""
    if not content:
        return True  # 空文件认为是合法文本文件
    
    # 计算可打印字符的比例（更宽松的标准）
    printable_chars = sum(1 for char in content if char.isprintable() or char in '\r\n\t\x0b\x0c')
    printable_ratio = printable_chars / len(content)
    
    # 降低门槛：如果80%以上是可打印字符，认为是文本文件
    return printable_ratio >= 0.8


def _is_safe_binary_content(file_header: bytes) -> bool:
    """检查二进制内容是否安全（用于无法解码的文件）"""
    # 检查是否包含危险的可执行文件标记
    dangerous_signatures = [
        b'MZ',              # DOS/Windows executable
        b'\x7fELF',         # ELF executable  
        b'\xca\xfe\xba\xbe', # Mach-O executable
        b'<?php',           # PHP script
        b'<script',         # JavaScript
        b'#!/bin/',         # Shell script
        b'#!/usr/bin/',     # Shell script
    ]
    
    # 如果包含危险签名，拒绝
    for signature in dangerous_signatures:
        if signature in file_header.lower():
            return False
    
    # 检查二进制内容的可打印字符比例
    try:
        printable_bytes = sum(1 for byte in file_header if 32 <= byte <= 126 or byte in [9, 10, 13, 11, 12])
        if len(file_header) > 0:
            printable_ratio = printable_bytes / len(file_header)
            # 降低门槛：如果60%以上是可打印ASCII，可能是文本文件
            return printable_ratio >= 0.6
    except Exception:
        pass
    
    return False


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
    
    # 检查文件类型和安全性
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # 验证文件内容（魔术字节检测）
    if not validate_file_content(file):
        # 为调试提供更详细的错误信息
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'
        print(f"[DEBUG] 文件验证失败: {file.filename}, 扩展名: {file_extension}")
        
        # 读取文件头部用于调试
        file.file.seek(0)
        file_header = file.file.read(100)
        file.file.seek(0)
        print(f"[DEBUG] 文件头部 (前100字节): {file_header[:50]!r}...")
        
        raise HTTPException(
            status_code=400,
            detail="文件内容与扩展名不匹配或包含恶意内容"
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
    current_user: User = Depends(get_current_active_user),  # 要求用户登录
):
    """
    下载文档文件 - 需要登录
    """
    # 验证用户权限
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="用户账户未激活")
    
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 验证文件路径安全性（防止路径遍历）
    if not document.file_path or '..' in document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在或路径无效")
    
    # 确保文件在允许的上传目录内
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(document.file_path)
    if not file_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="不允许访问此文件")
    
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
            
            # 验证文件内容
            if not validate_file_content(file):
                continue  # 跳过恶意文件
            
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






