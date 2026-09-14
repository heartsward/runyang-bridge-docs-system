# -*- coding: utf-8 -*-
"""
智能搜索API端点
"""
import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.models.user import User
from app.models.document import Document, SearchLog
from app.services.search_service import SearchService
from app.services.document_formatter import DocumentFormatter, DocumentType, FormatMode
from app.core.config import settings
import time

router = APIRouter()

# 多词切分：仅按空白（阶段二十·20.5）
# 标点（含 . / 等）属于词的一部分——"172.16.8.106" 是一个完整 IP，不能拆开
_TERM_SPLIT_RE = re.compile(r'\s+')


def tokenize_query(q: str) -> List[str]:
    """把用户查询切分为搜索词（阶段二十·20.2 / 20.5）

    - 仅空白为分隔符（"交换机 配置"→["交换机","配置"]）
    - 其余符号（标点/IP/URL 等）视为词的一部分
    - 去重保序；每词截断到 30 字符（防止超长词拖慢正则）
    - 无分隔符时返回单元素列表 → 调用方保持"整体串匹配"的旧语义
    """
    parts = _TERM_SPLIT_RE.split((q or '').strip())
    terms: List[str] = []
    seen = set()
    for p in parts:
        t = p.strip()[:30]
        if t and t not in seen:
            seen.add(t)
            terms.append(t)
    return terms


def _highlight_terms(text: str, terms: List[str]) -> str:
    """对文本中所有词做 <mark> 高亮（多词联合搜索用）"""
    if not text or not terms:
        return text
    try:
        pattern = re.compile('|'.join(re.escape(t) for t in terms), re.IGNORECASE)
        return pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)
    except re.error:
        return text


def get_actual_file_path(stored_path: str) -> Optional[str]:
    """
    获取文件的实际路径，支持路径自动修正
    
    Args:
        stored_path: 数据库中存储的文件路径（可能是绝对路径）
    
    Returns:
        实际可访问的文件路径，如果文件不存在则返回None
    """
    if not stored_path:
        return None
    
    # 首先检查原路径是否存在
    if os.path.exists(stored_path):
        return stored_path
    
    # 如果原路径不存在，尝试使用文件名重新生成路径
    filename = os.path.basename(stored_path)
    corrected_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    if os.path.exists(corrected_path):
        return corrected_path
    
    return None

@router.get("/documents", summary="搜索文档")
async def search_documents(
    q: str = Query(..., description="搜索关键词"),
    doc_type: Optional[str] = Query(None, description="文档类型过滤"),
    limit: int = Query(20, description="返回结果数量限制"),
    offset: int = Query(0, description="结果偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # 要求用户登录
):
    """搜索文档内容"""
    start_time = time.time()
    
    try:
        search_service = SearchService()
        
        # 构建基础查询 - 所有用户都可以搜索所有文档
        query = db.query(Document)
        
        # 文档类型过滤
        if doc_type:
            query = query.filter(Document.file_type == doc_type)
        
        # 获取所有相关文档进行搜索
        documents = query.all()  # 搜索所有文档以确保完整性
        
        # ===== 阶段二十·20.2：多词联合搜索 =====
        # 单词（无分隔符）：完全保留改造前的匹配与打分语义（召回不降）
        # 多词（空格/标点分隔）：逐词独立匹配，命中词数多的排前
        terms = tokenize_query(q)
        single_term = len(terms) == 1
        all_terms = [q.strip()] if single_term else terms

        search_results = []

        for doc in documents:
            content_terms: List[str] = []
            title_terms: List[str] = []
            desc_terms: List[str] = []
            highlights: List[Dict[str, Any]] = []
            match_count = 0

            # --- 1) 内容匹配（最高优先级） ---
            if doc.content_extracted and doc.content:
                if single_term:
                    try:
                        matches = search_service.search_in_text(doc.content, q)
                        if matches:
                            content_terms = [q.strip()]
                            match_count = len(matches)
                            for match in matches[:3]:  # 显示前3个匹配片段
                                highlights.append({
                                    "text": match["content"],
                                    "line_number": match["line_number"]
                                })
                    except Exception:
                        pass
                else:
                    try:
                        term_matches = search_service.search_terms_in_text(doc.content, terms)
                    except Exception:
                        term_matches = {}
                    for t in terms:
                        ms = term_matches.get(t) or []
                        if ms:
                            content_terms.append(t)
                            match_count += len(ms)
                            if len(highlights) < 3:
                                highlights.append({
                                    "text": _highlight_terms(ms[0]["content"], terms),
                                    "line_number": ms[0]["line_number"]
                                })

            # --- 2) 标题匹配（对内容未命中的词） ---
            remaining = [t for t in all_terms if t not in content_terms]
            if remaining:
                for t in remaining:
                    if t.lower() in doc.title.lower():
                        title_terms.append(t)

            # --- 3) 描述匹配（对内容/标题未命中的词） ---
            remaining = [t for t in remaining if t not in title_terms]
            if remaining and doc.description:
                for t in remaining:
                    if t.lower() in doc.description.lower():
                        desc_terms.append(t)

            matched_terms = content_terms + title_terms + desc_terms
            if not matched_terms:
                continue

            # 文档级匹配类型：内容 > 标题 > 描述
            if content_terms:
                match_type = "content"
            elif title_terms:
                match_type = "title"
            else:
                match_type = "description"

            # --- 打分 ---
            if single_term:
                # 与改造前完全一致的打分公式
                if match_type == "content":
                    score = min(0.8 + min(match_count / 20.0, 0.15), 1.0)
                elif match_type == "title":
                    t0 = title_terms[0]
                    if doc.title.lower() == t0.lower():
                        score = 0.6 + 0.2
                    elif doc.title.lower().startswith(t0.lower()):
                        score = 0.6 + 0.15
                    else:
                        score = 0.6
                else:
                    t0 = desc_terms[0]
                    desc_lower = doc.description.lower()
                    if desc_lower.startswith(t0.lower()):
                        score = 0.4 + 0.1
                    elif desc_lower.count(t0.lower()) > 1:
                        score = 0.4 + 0.05
                    else:
                        score = 0.4
            else:
                # 多词：命中词覆盖率为主（全词命中 > 部分命中），命中桶质量为辅
                coverage = len(matched_terms) / len(terms)
                bucket_score = {"content": 0.8, "title": 0.6, "description": 0.4}[match_type]
                score = min(0.5 * coverage + 0.5 * bucket_score, 1.0)

            # 标题/描述命中的高亮文本（内容命中时 highlights 已由片段填充）
            if match_type == "title":
                highlights = [{"text": f"标题: {_highlight_terms(doc.title, title_terms)}", "line_number": 1}]
            elif match_type == "description":
                desc_snippet = doc.description
                if len(desc_snippet) > 200:
                    # 找首个命中词附近的文本窗口
                    pos = -1
                    for t in desc_terms:
                        pos = desc_snippet.lower().find(t.lower())
                        if pos >= 0:
                            break
                    if pos >= 0:
                        start = max(0, pos - 100)
                        end = min(len(desc_snippet), pos + 100)
                        desc_snippet = desc_snippet[start:end]
                        if start > 0:
                            desc_snippet = "..." + desc_snippet
                        if end < len(doc.description):
                            desc_snippet = desc_snippet + "..."
                highlights = [{"text": f"描述: {_highlight_terms(desc_snippet, desc_terms)}", "line_number": 1}]

            search_results.append({
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "file_type": doc.file_type,
                "file_path": doc.file_path,
                "score": score,
                "match_count": match_count if match_type == "content" else len(matched_terms),
                "highlights": highlights,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "match_type": match_type,
                # 阶段二十：多词联合搜索新增字段（单词查询时 matched_terms 为单元素）
                "matched_terms": matched_terms,
                "term_total": len(terms),
            })

        # 按优先级排序：内容 > 标题 > 描述，同类型内按相关度分数排序
        # 多词时 score 已含"命中词覆盖率"，全词命中的文档自然排前
        def sort_key(result):
            score = result["score"]
            match_type = result["match_type"]

            # 给不同匹配类型设置明确的优先级权重
            type_priority = {
                "content": 1000,    # 内容匹配：权重最高，确保始终排在前面
                "title": 500,       # 标题匹配：中等权重
                "description": 100  # 描述匹配：最低权重
            }

            # 综合排序分数 = 类型优先级权重 + 相关度分数
            # 这样可以确保类型优先级的绝对性，同时在同类型中按相关度排序
            combined_score = type_priority.get(match_type, 0) + score

            return combined_score

        search_results.sort(key=sort_key, reverse=True)
        
        # 分页
        total = len(search_results)
        paginated_results = search_results[offset:offset + limit]
        
        # 记录搜索日志（仅限已登录用户）
        if current_user:
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            search_log = SearchLog(
                user_id=current_user.id,
                query=q,
                results_count=total,
                response_time=response_time,
                filters={"doc_type": doc_type, "limit": limit, "offset": offset}
            )
            db.add(search_log)
            db.commit()
        
        return {
            "query": q,
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": paginated_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/preview/{document_id}", summary="预览文档内容")
async def preview_document(
    document_id: int,
    highlight: Optional[str] = Query(None, description="高亮关键词"),
    source: Optional[str] = Query("auto", description="内容来源: auto(自动选择), extracted(预处理内容), file(原始文件)"),
    format_mode: Optional[str] = Query("formatted", description="格式化模式: original(原始), formatted(格式化), compact(紧凑), structured(结构化)"),
    view_mode: Optional[str] = Query("content", description="查看模式: content(内容提取), original(原文查看) - 仅PDF文件支持"),
    max_length: Optional[int] = Query(None, description="内容长度限制(字符数)，不设置表示无限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # 要求用户登录
):
    """预览文档内容"""
    try:
        # 获取文档 - 所有用户都可以预览所有文档
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # PDF/图片文件原文查看模式
        is_pdf_file = document.file_type and document.file_type.lower() == 'pdf'
        is_image_file = document.file_type and document.file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
        
        if (is_pdf_file or is_image_file) and view_mode == "original":
            file_type_name = "PDF" if is_pdf_file else "图片"
            actual_file_path = get_actual_file_path(document.file_path)
            if not actual_file_path:
                raise HTTPException(status_code=400, detail=f"{file_type_name}文件不存在")
            
            # 返回原始文件信息，前端将直接显示原始文件
            return {
                "document_id": document_id,
                "title": document.title,
                "file_type": document.file_type,
                "view_mode": view_mode,
                "file_path": actual_file_path,
                "file_size": os.path.getsize(actual_file_path),
                "content": f"{file_type_name}原文查看模式 - 前端将直接渲染{file_type_name}文件",
                "content_source": "original_pdf" if is_pdf_file else "original_image",
                "content_extracted": document.content_extracted,
                "content_extraction_error": document.content_extraction_error,
                "original_length": 0,
                "formatted_length": 0,
                "is_truncated": False,
                "format_mode": format_mode,
                "is_pdf_original": True,
                "supports_dual_mode": True,
                "document_type": "PDF" if is_pdf_file else "IMAGE",
                "format_statistics": {},
                "document_structure": {},
                "message": f"请在前端使用{'PDF查看器' if is_pdf_file else '图片查看器'}显示原始{file_type_name}文件"
            }
        
        content = None
        content_source = "unknown"
        
        # 根据source参数决定内容来源  
        if source == "extracted" or (source == "auto" and document.content_extracted and document.content):
            # 使用预处理的内容
            if document.content_extracted and document.content:
                content = document.content
                content_source = "extracted"
            else:
                # 如果没有预处理内容但请求预处理内容，返回错误信息
                if source == "extracted":
                    error_msg = document.content_extraction_error or "内容尚未提取"
                    raise HTTPException(status_code=400, detail=f"预处理内容不可用: {error_msg}")
        
        # 如果还没有内容，尝试从文件读取
        if not content:
            actual_file_path = get_actual_file_path(document.file_path)
            if not actual_file_path:
                raise HTTPException(status_code=400, detail="文档文件不存在")
            
            search_service = SearchService()
            content = search_service.extract_file_content(actual_file_path)
            content_source = "file"
            
            
            if not content:
                raise HTTPException(status_code=400, detail="无法读取文档内容")
        
        # 智能文档格式化 - 对Excel文件进行优化处理
        original_length = len(content)
        
        # Excel文件优化：跳过额外格式化，提取引擎（anydoc/本地）已提供结构化表格
        if document.file_type and document.file_type.lower() in ['xls', 'xlsx']:
            format_stats = {
                "processing_time": 0.001,  # 几乎无延迟
                "original_length": original_length,
                "formatted_length": len(content)
            }
            document_structure = {}
            doc_type = DocumentType.EXCEL  # 设置Excel文档类型
        else:
            # 对其他文档类型进行正常格式化
            formatter = DocumentFormatter()
            
            # 根据文件类型确定文档类型
            doc_type = DocumentType.GENERAL
            if document.file_type:
                if document.file_type.lower() == 'pdf':
                    doc_type = DocumentType.PDF
                elif document.file_type.lower() in ['doc', 'docx']:
                    doc_type = DocumentType.WORD
                elif document.file_type.lower() in ['ppt', 'pptx']:
                    doc_type = DocumentType.POWERPOINT
                elif any(keyword in document.title.lower() for keyword in ['技术', '系统', 'api', '手册']):
                    doc_type = DocumentType.TECHNICAL
                elif any(keyword in document.title.lower() for keyword in ['法', '规定', '条例', '办法']):
                    doc_type = DocumentType.LEGAL
                elif any(keyword in document.title.lower() for keyword in ['报告', '总结', '分析']):
                    doc_type = DocumentType.REPORT
            
            # 确定格式化模式
            try:
                format_enum = FormatMode(format_mode)
            except ValueError:
                format_enum = FormatMode.FORMATTED
            
            # 执行智能格式化
            format_result = formatter.format_document(
                content=content,
                doc_type=doc_type,
                format_mode=format_enum,
                options={
                    'max_line_length': 120,
                    'preserve_whitespace': True,
                    'enhance_tables': True,
                    'add_navigation': format_enum == FormatMode.STRUCTURED,
                    'highlight_keywords': bool(highlight)
                }
            )
            
            # 获取格式化后的内容
            content = format_result.get('formatted_content', content)
            format_stats = format_result.get('statistics', {})
            document_structure = format_result.get('structure', {})
        
        
        # 如果有高亮关键词，添加高亮标记（阶段二十·20.5：按空格分词后多词高亮，
        # 每个 <mark> 带 data-term 属性供前端按词分组导航）
        if highlight:
            search_service = SearchService()
            hl_terms = tokenize_query(highlight)
            if len(hl_terms) == 1:
                # 单词：保持原有整体串匹配语义
                content = search_service.highlight_text(content, highlight.strip())
            else:
                content = search_service.highlight_terms(content, hl_terms)
        
        # 记录文档查看统计（仅限已登录用户）
        if current_user:
            try:
                from app.models.document import DocumentView
                view_log = DocumentView(
                    document_id=document_id,
                    user_id=current_user.id
                )
                db.add(view_log)
                
                # 更新文档的查看计数
                document.view_count = (document.view_count or 0) + 1
                
                db.commit()
            except Exception as e:
                db.rollback()
        
        # 移除内容长度限制，支持完整显示
        is_truncated = False
        # 添加安全检查：如果内容超过10MB，提供警告但仍显示完整内容
        if len(content) > 10 * 1024 * 1024:  # 10MB
            pass  # 大文件处理，暂时无特殊操作
        
        return {
            "document_id": document_id,
            "title": document.title,
            "file_type": document.file_type,
            "content": content,
            "content_source": content_source,
            "content_extracted": document.content_extracted,
            "content_extraction_error": document.content_extraction_error,
            "original_length": original_length,
            "formatted_length": len(content),
            "is_truncated": is_truncated,
            "format_mode": format_mode,
            "view_mode": view_mode,
            "is_pdf_original": False,
            "supports_dual_mode": is_pdf_file or is_image_file,
            "document_type": doc_type.value,
            "format_statistics": format_stats,
            "document_structure": document_structure,
            "file_size": os.path.getsize(get_actual_file_path(document.file_path)) if get_actual_file_path(document.file_path) else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/original/{document_id}", summary="获取原始PDF/图片文件")
async def get_original_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取原始PDF/图片文件用于前端直接显示"""
    try:
        # 获取文档信息
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查是否为PDF或图片文件
        is_pdf_file = document.file_type and document.file_type.lower() == 'pdf'
        is_image_file = document.file_type and document.file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
        
        if not (is_pdf_file or is_image_file):
            raise HTTPException(status_code=400, detail="仅支持PDF和图片文件的原文查看")
        
        # 检查文件是否存在
        actual_file_path = get_actual_file_path(document.file_path)
        if not actual_file_path:
            file_type_name = "PDF" if is_pdf_file else "图片"
            raise HTTPException(status_code=404, detail=f"{file_type_name}文件不存在")
        
        # 返回文件流，设置正确的MIME类型
        from fastapi.responses import FileResponse
        
        # 根据文件类型设置正确的MIME类型
        if is_pdf_file:
            media_type = 'application/pdf'
            filename = f"{document.title}.pdf"
        else:
            # 图片文件MIME类型映射
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'tiff': 'image/tiff',
                'webp': 'image/webp'
            }
            file_ext = document.file_type.lower()
            media_type = mime_types.get(file_ext, 'image/jpeg')  # 默认使用jpeg
            filename = f"{document.title}.{file_ext}"
        
        # 使用Response而不是FileResponse，确保在线预览而不是下载
        from fastapi.responses import Response
        with open(actual_file_path, 'rb') as f:
            file_content = f.read()
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": "inline",  # 关键：inline 而不是 attachment
                "Cache-Control": "public, max-age=3600"  # 缓存1小时
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取原始文件失败: {str(e)}")

# 资产搜索功能已移除 - 智能搜索模块现在只搜索文档内容
