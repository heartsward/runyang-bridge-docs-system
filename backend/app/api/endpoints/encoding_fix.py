# -*- coding: utf-8 -*-
"""
编码修复API端点
用于修复上传文档的编码问题
"""
import os
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.document import Document
from app.utils.encoding_detector import EncodingDetector
from app.services.content_extractor import ContentExtractor
from app.services.background_tasks import get_task_manager

router = APIRouter()


@router.post("/fix-document-encoding/{document_id}", summary="修复文档编码")
async def fix_document_encoding(
    document_id: int,
    force_encoding: str = None,  # 强制指定编码，如果为None则自动检测
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    修复指定文档的编码问题并重新提取内容
    
    Args:
        document_id: 文档ID
        force_encoding: 强制指定编码（可选），支持的编码：utf-8, gbk, gb2312等
    """
    # 检查权限：只有管理员才能修复编码
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以修复文档编码")
    
    # 获取文档记录
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    # 检查文件类型是否支持编码修复
    file_ext = document.file_path.split('.')[-1].lower()
    if file_ext not in ['txt', 'py', 'js', 'html', 'xml', 'yml', 'yaml', 'csv', 'rtf', 
                       'conf', 'config', 'cfg', 'ini', 'properties', 'env', 'md']:
        raise HTTPException(status_code=400, detail=f"文件类型 '{file_ext}' 不支持编码修复")
    
    try:
        # 获取编码信息
        encoding_info = EncodingDetector.get_encoding_info(document.file_path)
        
        # 读取文档内容
        if force_encoding:
            content, error = EncodingDetector.read_file_with_encoding(document.file_path, force_encoding)
            used_encoding = force_encoding
        else:
            content, error = EncodingDetector.read_file_with_encoding(document.file_path)
            used_encoding = encoding_info['detected_encoding']
        
        if content is None:
            raise HTTPException(status_code=500, detail=f"无法读取文档内容: {error}")
        
        # 直接更新数据库中的内容
        document.content = content
        document.content_extracted = True
        document.content_extraction_error = None
        
        # 记录编码修复信息
        if not document.metadata:
            document.metadata = {}
        
        document.metadata.update({
            'encoding_fixed': True,
            'detected_encoding': encoding_info['detected_encoding'],
            'detection_confidence': encoding_info['confidence'],
            'used_encoding': used_encoding,
            'fix_timestamp': str(datetime.now()),
            'fixed_by': current_user.username
        })
        
        db.commit()
        db.refresh(document)
        
        return {
            'success': True,
            'message': '文档编码修复成功',
            'document_id': document_id,
            'encoding_info': {
                'detected_encoding': encoding_info['detected_encoding'],
                'detection_confidence': encoding_info['confidence'],
                'used_encoding': used_encoding,
                'content_length': len(content) if content else 0,
                'readable': True,
                'contains_chinese': encoding_info.get('contains_chinese', False)
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"编码修复失败: {str(e)}")


@router.get("/check-encoding/{document_id}", summary="检查文档编码")
async def check_document_encoding(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    检查文档的编码信息，不进行修复
    """
    # 获取文档记录
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    try:
        # 获取编码信息
        encoding_info = EncodingDetector.get_encoding_info(document.file_path)
        
        return {
            'success': True,
            'document_id': document_id,
            'file_path': document.file_path,
            'file_name': document.file_name,
            'encoding_info': encoding_info,
            'current_content_status': {
                'content_extracted': document.content_extracted,
                'content_length': len(document.content or '') if document.content else 0,
                'extraction_error': document.content_extraction_error
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编码检查失败: {str(e)}")


@router.post("/batch-fix-encoding", summary="批量修复文档编码")
async def batch_fix_document_encoding(
    document_ids: List[int] = None,  # 如果为空，则处理所有有编码问题的文档
    force_encoding: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    批量修复文档编码问题
    """
    # 检查权限：只有管理员才能批量修复编码
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以批量修复文档编码")
    
    try:
        # 如果没有指定文档ID，查找所有可能有编码问题的文档
        if not document_ids:
            # 查找内容提取失败或内容为空的文本类型文档
            text_extensions = ['txt', 'py', 'js', 'html', 'xml', 'yml', 'yaml', 'csv', 'rtf', 
                             'conf', 'config', 'cfg', 'ini', 'properties', 'env', 'md']
            
            documents = db.query(Document).filter(
                Document.file_type.in_(text_extensions)
            ).filter(
                (Document.content_extracted == False) | 
                (Document.content.is_(None)) |
                (Document.content == '')
            ).all()
            
            document_ids = [doc.id for doc in documents]
        
        results = []
        success_count = 0
        error_count = 0
        
        for doc_id in document_ids:
            try:
                # 调用单个文档修复功能
                result = await fix_document_encoding(doc_id, force_encoding, db, current_user)
                results.append({
                    'document_id': doc_id,
                    'success': True,
                    'result': result
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    'document_id': doc_id,
                    'success': False,
                    'error': str(e)
                })
                error_count += 1
        
        return {
            'success': True,
            'message': f'批量修复完成：成功 {success_count} 个，失败 {error_count} 个',
            'total_processed': len(document_ids),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量修复失败: {str(e)}")


@router.get("/encoding-stats", summary="获取编码统计信息")
async def get_encoding_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取系统中文档编码的统计信息
    """
    try:
        # 获取所有文本类型的文档
        text_extensions = ['txt', 'py', 'js', 'html', 'xml', 'yml', 'yaml', 'csv', 'rtf', 
                          'conf', 'config', 'cfg', 'ini', 'properties', 'env', 'md']
        
        documents = db.query(Document).filter(
            Document.file_type.in_(text_extensions)
        ).all()
        
        stats = {
            'total_text_documents': len(documents),
            'content_extracted': 0,
            'content_failed': 0,
            'content_empty': 0,
            'encoding_fixed': 0,
            'potential_encoding_issues': 0
        }
        
        for doc in documents:
            if doc.content_extracted is True and doc.content:
                stats['content_extracted'] += 1
            elif doc.content_extracted is False:
                stats['content_failed'] += 1
                stats['potential_encoding_issues'] += 1
            elif not doc.content:
                stats['content_empty'] += 1
                stats['potential_encoding_issues'] += 1
            
            # 检查是否已修复过编码
            if (doc.metadata and 
                isinstance(doc.metadata, dict) and 
                doc.metadata.get('encoding_fixed')):
                stats['encoding_fixed'] += 1
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 修复导入datetime
from datetime import datetime