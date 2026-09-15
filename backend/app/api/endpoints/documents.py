from typing import List, Optional, Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
import os
from app.core.deps import get_db, get_current_active_user
from app.crud import document as crud_document
from app.models.user import User
from app.models.document import Document as DocumentModel
from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentList,
    Category, CategoryCreate, CategoryUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-filename", summary="检查文件名是否存在")
async def check_filename(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """检查文件名是否已存在"""
    # 重要修复：使用与上传时相同的文件名处理逻辑
    from app.api.endpoints.upload import generate_safe_filename
    import os
    
    # 分离文件名和扩展名
    if '.' in filename:
        title = filename.rsplit('.', 1)[0]
        extension = filename.rsplit('.', 1)[1].lower()
    else:
        title = filename
        extension = 'txt'  # 默认扩展名
    
    # 使用相同的安全文件名生成逻辑
    safe_filename = generate_safe_filename(title, extension, '')
    # 移除路径部分，只保留文件名
    safe_filename = os.path.basename(safe_filename)
    
    print(f"[DEBUG] 冲突检查: 原始={filename}, 安全文件名={safe_filename}")
    
    # 查询所有同名文档（使用处理后的安全文件名）
    existing_docs = db.query(DocumentModel).filter(DocumentModel.file_name == safe_filename).all()
    
    if existing_docs:
        # 返回详细的冲突信息
        existing_documents = []
        for doc in existing_docs:
            existing_documents.append({
                "id": doc.id,
                "title": doc.title,
                "file_name": doc.file_name,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        return {
            "exists": True,
            "count": len(existing_docs),
            "filename": filename,
            "safe_filename": safe_filename,  # 添加处理后的安全文件名
            "existing_documents": existing_documents
        }
    else:
        return {
            "exists": False,
            "count": 0,
            "filename": filename,
            "safe_filename": safe_filename,  # 添加处理后的安全文件名
            "existing_documents": []
        }

# 文档相关接口
@router.get("/", response_model=DocumentList, summary="获取文档列表")
def read_documents(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档列表（需登录）
    """
    documents = crud_document.get_multi(
        db, skip=skip, limit=limit, 
        category_id=category_id, status=status
    )
    total_count = crud_document.count(db, category_id=category_id, status=status)
    
    return DocumentList(
        items=documents,
        total=total_count,
        page=skip // limit + 1 if limit > 0 else 1,
        per_page=limit,
        pages=(total_count + limit - 1) // limit if limit > 0 else 1
    )


@router.post("/", response_model=Document, summary="创建文档")
def create_document(
    *,
    db: Session = Depends(get_db),
    document_in: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新文档 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能创建文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以创建文档")
    
    document = crud_document.create(db=db, obj_in=document_in, owner_id=current_user.id)
    return document


@router.get("/{document_id}", response_model=Document, summary="获取文档详情")
def read_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    获取指定文档的详细信息
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 增加查看次数
    user_id = current_user.id if current_user else None
    crud_document.increment_view_count(db=db, document_id=document_id, user_id=user_id)
    
    return document


@router.put("/{document_id}", response_model=Document, summary="更新文档")
def update_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # 逗号分隔的标签字符串
    current_user: User = Depends(get_current_active_user),
):
    """
    更新文档信息 - 支持FormData格式
    """
    # 调试：打印接收到的数据
    try:
        print(f"[DEBUG] 文档更新API接收到的数据:")
        print(f"  文档ID: {document_id}")
        print(f"  标题: {repr(title)}")
        print(f"  描述: {repr(description)}")
        print(f"  标签: {repr(tags)}")
        print(f"  用户: {current_user.username if current_user else 'None'}")
    except Exception as debug_error:
        print(f"[ERROR] 调试输出失败: {debug_error}")
    
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if document.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 处理标签
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # 创建更新数据
    update_data = DocumentUpdate(
        title=title,
        description=description,
        tags=tag_list
    )
    
    document = crud_document.update(db=db, db_obj=document, obj_in=update_data)
    return document


@router.delete("/{document_id}", summary="删除文档")
def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    backup_before_delete: bool = Query(False, description="删除前是否备份文件"),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除文档 - 仅管理员可操作
    使用原子性删除机制，确保数据库记录和物理文件同时删除
    """
    # 检查权限：只有管理员才能删除文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以删除文档")
    
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 使用新的原子性删除方法
    delete_result = crud_document.delete_with_file(
        db=db, 
        id=document_id, 
        backup_before_delete=backup_before_delete
    )
    
    if not delete_result["success"]:
        raise HTTPException(
            status_code=500, 
            detail=f"文档删除失败: {delete_result['error']}"
        )
    
    # 构建成功响应
    response = {
        "message": "文档删除成功",
        "document_id": document_id,
        "document_title": delete_result["document"]["title"],
        "file_deleted": delete_result["file_deleted"],
        "document_deleted": delete_result["document_deleted"]
    }
    
    # 如果有文件操作结果，添加相关信息
    if delete_result["file_result"]:
        file_result = delete_result["file_result"]
        response["file_info"] = {
            "existed": file_result["existed"],
            "backed_up": file_result["backed_up"],
            "backup_path": file_result.get("backup_path"),
            "file_size": file_result["file_size"]
        }
    
    return response


# 文件管理相关接口
@router.get("/orphan-files/detect", summary="检测孤儿文件")
def detect_orphan_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    检测uploads目录中的孤儿文件 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能检测孤儿文件
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以检测孤儿文件")
    
    try:
        from app.services.file_manager import FileManagerService
        
        # 获取数据库中所有文档的文件路径
        documents = db.query(Document).all()
        db_file_paths = [doc.file_path for doc in documents if doc.file_path]
        
        # 检测孤儿文件
        file_manager = FileManagerService()
        result = file_manager.detect_orphan_files(db_file_paths)
        
        return {
            "message": "孤儿文件检测完成",
            "scan_time": result["scan_time"],
            "summary": {
                "total_files": result["total_files"],
                "orphan_count": result["orphan_count"],
                "orphan_total_size_mb": result.get("orphan_total_size_mb", 0),
                "valid_files": len(result["valid_files"])
            },
            "orphan_files": result["orphan_files"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测孤儿文件失败: {str(e)}")


@router.delete("/orphan-files/cleanup", summary="清理孤儿文件")
def cleanup_orphan_files(
    backup_before_delete: bool = Query(True, description="删除前是否备份文件"),
    confirm: bool = Query(False, description="确认执行清理操作"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    清理uploads目录中的孤儿文件 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能清理孤儿文件
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以清理孤儿文件")
    
    # 安全确认
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="请设置confirm=true以确认执行清理操作"
        )
    
    try:
        from app.services.file_manager import FileManagerService
        
        # 获取数据库中所有文档的文件路径
        documents = db.query(Document).all()
        db_file_paths = [doc.file_path for doc in documents if doc.file_path]
        
        # 检测孤儿文件
        file_manager = FileManagerService()
        detect_result = file_manager.detect_orphan_files(db_file_paths)
        
        if detect_result["orphan_count"] == 0:
            return {
                "message": "没有发现孤儿文件",
                "orphan_count": 0,
                "total_size_freed_mb": 0
            }
        
        # 清理孤儿文件
        cleanup_result = file_manager.cleanup_orphan_files(
            detect_result["orphan_files"], 
            backup_before_delete=backup_before_delete
        )
        
        return {
            "message": "孤儿文件清理完成",
            "cleanup_time": cleanup_result["cleanup_time"],
            "summary": {
                "total_files": cleanup_result["total_files"],
                "deleted_count": cleanup_result["deleted_count"],
                "failed_count": cleanup_result["failed_count"],
                "total_size_freed_mb": cleanup_result["total_size_freed_mb"],
                "backed_up_count": len(cleanup_result["backed_up_files"])
            },
            "deleted_files": cleanup_result["deleted_files"],
            "failed_files": cleanup_result["failed_files"],
            "backed_up_files": cleanup_result["backed_up_files"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理孤儿文件失败: {str(e)}")


@router.get("/storage/usage", summary="获取存储使用情况")
def get_storage_usage(
    current_user: User = Depends(get_current_active_user),
):
    """
    获取存储使用情况统计 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能查看存储使用情况
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以查看存储使用情况")
    
    try:
        from app.services.file_manager import FileManagerService
        
        file_manager = FileManagerService()
        result = file_manager.get_storage_usage()
        
        return {
            "message": "存储使用情况统计",
            "scan_time": result["scan_time"],
            "uploads": {
                "directory": result["uploads_dir"],
                "file_count": result["uploads_file_count"],
                "total_size_mb": result.get("uploads_total_size_mb", 0)
            },
            "backups": {
                "directory": result["backup_dir"],
                "file_count": result["backup_file_count"],
                "total_size_mb": result.get("backup_total_size_mb", 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取存储使用情况失败: {str(e)}")


@router.get("/search/", response_model=List[Document], summary="搜索文档")
def search_documents(
    query: str = Query(..., description="搜索关键词"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    搜索文档
    """
    documents = crud_document.search(db=db, query=query, skip=skip, limit=limit)
    return documents


@router.get("/popular/", response_model=List[Document], summary="获取热门文档")
def read_popular_documents(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    获取热门文档列表
    """
    documents = crud_document.get_popular(db=db, limit=limit)
    return documents


# 分类相关接口
@router.get("/categories/", response_model=List[Category], summary="获取分类列表")
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取分类列表
    """
    categories = crud_document.get_categories(db, skip=skip, limit=limit)
    return categories


@router.post("/categories/", response_model=Category, summary="创建分类")
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新分类
    """
    category = crud_document.create_category(
        db=db, obj_in=category_in, creator_id=current_user.id
    )
    return category


@router.put("/categories/{category_id}", response_model=Category, summary="更新分类")
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    更新分类信息
    """
    category = crud_document.get_category(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category = crud_document.update_category(db=db, db_obj=category, obj_in=category_in)
    return category


@router.delete("/categories/{category_id}", summary="删除分类")
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    删除分类
    """
    category = crud_document.get_category(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category = crud_document.delete_category(db=db, id=category_id)
    return {"message": "分类删除成功"}


@router.get("/{document_id}/download", summary="下载文档")
def download_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    下载文档文件
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    # 增加下载次数
    user_id = current_user.id if current_user else None
    crud_document.increment_download_count(db=db, document_id=document_id, user_id=user_id)
    
    # 获取文件信息，使用文档标题作为文件名
    original_filename = os.path.basename(document.file_path)
    file_extension = os.path.splitext(original_filename)[1]  # 获取扩展名
    # 清理文档标题中的非法文件名字符
    safe_title = "".join(c for c in document.title if c.isalnum() or c in (' ', '-', '_', '(', ')', '[', ']')).strip()
    filename = f"{safe_title}{file_extension}" if safe_title else original_filename
    
    return FileResponse(
        path=document.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.get("/{document_id}/preview", summary="预览文档文件")
def preview_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),  # 要求用户登录
):
    """
    预览文档文件（在线显示，不强制下载）- 需要登录
    """
    # 验证用户权限
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="用户账户未激活")
    
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 验证文件路径安全性（防止路径遍历）
    if not document.file_path or '..' in document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在或路径无效")
    
    # 确保文件在允许的上传目录内
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(document.file_path)
    if not file_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="不允许访问此文件")
    
    # 获取文件扩展名并确定MIME类型
    file_extension = os.path.splitext(document.file_path)[1].lower()
    
    # 根据文件类型设置正确的MIME类型
    mime_type_mapping = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.txt': 'text/plain; charset=utf-8',
        '.csv': 'text/csv; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.xml': 'application/xml; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.htm': 'text/html; charset=utf-8'
    }
    
    media_type = mime_type_mapping.get(file_extension, 'application/octet-stream')
    
    # 对于可预览的文件类型，设置inline显示；其他类型仍然下载
    if file_extension in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.txt']:
        # 在线预览，不强制下载
        from fastapi.responses import Response
        with open(document.file_path, 'rb') as f:
            file_content = f.read()
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600"  # 缓存1小时
            }
        )
    else:
        # 其他文件类型仍然强制下载
        filename = f"{document.title}{file_extension}"
        return FileResponse(
            path=document.file_path,
            filename=filename,
            media_type='application/octet-stream'
        )


# ==================== 阶段二十四：Office → PDF 预览转换端点 ====================
# 与"内容提取"进度通道完全独立（走 preview_convert_{doc_id}.json）

@router.get("/{document_id}/converted-pdf", summary="Office 格式转 PDF 用于浏览器预览")
async def get_converted_pdf(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """返回 LibreOffice 转好的 PDF（iframe 用）。

    - 缓存命中：直接返回（秒出）
    - 缓存未命中：同步触发转换（小文件秒出；大文件如 xlsx 可能 30s+）
    - LibreOffice 未装：返回 503 + 指引文档链接
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not document.file_path or '..' in document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在或路径无效")

    # 仅对支持的扩展名走转换
    ext = os.path.splitext(document.file_path)[1].lower().lstrip(".")
    from app.services.preview_converter import (
        is_supported_office_type, get_preview_converter,
    )
    if not is_supported_office_type(ext):
        raise HTTPException(
            status_code=400,
            detail=f"文档类型 .{ext} 不需要 LibreOffice 转换（PDF/图片/文本直接可看）",
        )

    converter = get_preview_converter()
    if not converter.is_available:
        raise HTTPException(
            status_code=503,
            detail="LibreOffice 未安装,Office 格式在线预览不可用。请参见 docs/环境安装-LibreOffice.md 安装后重启后端。",
        )

    try:
        pdf_path = await converter.get_or_convert(
            doc_id=document_id,
            file_path=document.file_path,
            file_type=ext,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"PDF 转换失败: {e}")

    # inline 显示（浏览器 PDF 查看器渲染）
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "public, max-age=3600",  # 缓存 1 小时
        },
    )


@router.get("/conversion-status/batch", summary="批量查询 PDF 转换进度（文档列表页用）")
def get_conversion_status_batch(
    *,
    db: Session = Depends(get_db),
    doc_ids: str = Query(..., description="逗号分隔的文档 ID，如 1,2,3"),
    current_user: User = Depends(get_current_active_user),
):
    """文档列表页一次性拉取本页所有文档的 PDF 转换状态。

    返回 {statuses: {doc_id: {status, elapsed_sec, error_msg, from_cache}}}。
    - Office 类文档：返回真实转换状态（idle/converting/ready/error）
    - 非 Office 文档（PDF/图片/文本）：返回 status='n/a'（无需转换）
    与单文档端点 /{id}/conversion-status 共用 get_status，不重复实现。
    """
    from app.services.preview_converter import get_preview_converter, is_supported_office_type

    # 解析 doc_ids
    ids = [int(x) for x in doc_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return {"statuses": {}}
    ids = ids[:100]  # 限制单次查询数量，避免列表过长拖慢

    # 按 id 批量查文档
    docs = db.query(DocumentModel).filter(DocumentModel.id.in_(ids)).all()
    id_map = {d.id: d for d in docs}

    converter = get_preview_converter()
    result: Dict[int, Dict[str, Any]] = {}
    for did in ids:
        doc = id_map.get(did)
        if not doc:
            continue  # 文档不存在（可能已删），跳过
        ext = (os.path.splitext(doc.file_path)[1].lower().lstrip(".") or "") if doc.file_path else ""
        if not is_supported_office_type(ext):
            # 非 Office 文档：无需转换
            result[did] = {"status": "n/a", "elapsed_sec": 0, "error_msg": None, "from_cache": False}
            continue
        st = converter.get_status(did)
        result[did] = {
            "status": st.get("status", "idle"),
            "elapsed_sec": st.get("elapsed_sec", 0),
            "error_msg": st.get("error_msg"),
            "from_cache": st.get("from_cache", False),
        }
    return {"statuses": result}


@router.get("/{document_id}/conversion-status", summary="查询 PDF 转换进度")
def get_conversion_status(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """前端轮询用：返回 {status, started_at, finished_at, elapsed_sec, output_size, error_msg}

    状态机：idle → converting → ready | error
    与"内容提取进度"端点 /tasks/document/{id}/extraction-status 完全独立
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    from app.services.preview_converter import get_preview_converter
    converter = get_preview_converter()
    return converter.get_status(document_id)


@router.post("/{document_id}/convert", summary="异步触发 PDF 转换（预热）")
async def trigger_convert(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """异步触发 LibreOffice 转换,适合"上传后立即预热"或"用户进预览前预热"。

    返回 task_started=True,前端可以开始轮询 /conversion-status。
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")

    ext = os.path.splitext(document.file_path)[1].lower().lstrip(".")
    from app.services.preview_converter import (
        is_supported_office_type, get_preview_converter,
    )
    if not is_supported_office_type(ext):
        raise HTTPException(
            status_code=400,
            detail=f"文档类型 .{ext} 不需要 LibreOffice 转换",
        )

    converter = get_preview_converter()
    if not converter.is_available:
        raise HTTPException(
            status_code=503,
            detail="LibreOffice 未安装,无法触发转换",
        )

    # 推后台任务（不阻塞响应）
    background_tasks.add_task(
        _run_convert_async,
        doc_id=document_id,
        file_path=document.file_path,
        file_type=ext,
    )
    return {"doc_id": document_id, "task_started": True, "status": "converting"}


async def _run_convert_async(doc_id: int, file_path: str, file_type: str):
    """后台任务的同步包装（FastAPI BackgroundTasks 不能 await async 协程）"""
    from app.services.preview_converter import get_preview_converter
    converter = get_preview_converter()
    try:
        converter.convert_blocking(doc_id, file_path, file_type)
    except Exception as e:
        logger.warning(f"[converted-pdf] 后台预热失败 doc={doc_id}: {e}")


# ==================== 阶段二十四 end ====================


# Analytics endpoint removed


# ==================== AI文档分析端点 ====================

@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: int,
    analysis_type: str = Query("full", description="分析类型: full, summary, keywords, classification"),
    use_ai: bool = Form(True),
    ai_provider: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI分析文档内容"""
    try:
        # 获取文档
        document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取文档内容
        content = document.content or ""
        
        if not content:
            # 如果没有内容，尝试提取
            from app.services.content_extractor import ContentExtractor
            extractor = ContentExtractor()
            content, error = extractor.extract_content(document.file_path)
            
            if error or not content:
                return {
                    "success": False,
                    "message": f"无法提取文档内容: {error or '未知错误'}",
                    "analysis": None
                }
        
        if use_ai and ai_provider:
            # 使用AI分析
            from app.services.ai.extractors.document_analyzer import DocumentAnalyzer
            analyzer = DocumentAnalyzer()
            
            result = await analyzer.analyze_document(
                title=document.title,
                content=content,
                analysis_type=analysis_type,
                provider=ai_provider
            )
            
            analysis_type_names = {
                'full': '完整分析',
                'summary': '摘要提取',
                'keywords': '关键词提取',
                'classification': '文档分类'
            }
            analysis_name = analysis_type_names.get(analysis_type, '分析')
            message = f"使用AI（{ai_provider or '默认'}）完成{analysis_name}"
        else:
            # 降级到传统方法
            from app.services.ai.extractors.document_analyzer import DocumentAnalyzer
            analyzer = DocumentAnalyzer()
            result = analyzer._default_analysis(document.title, content)
            message = "使用传统分析方法"
        
        return {
            "success": True,
            "message": message,
            "analysis": result,
            "document_id": document_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "文档分析失败"
        }
