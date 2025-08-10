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
import time

router = APIRouter()

@router.get("/documents", summary="搜索文档")
async def search_documents(
    q: str = Query(..., description="搜索关键词"),
    doc_type: Optional[str] = Query(None, description="文档类型过滤"),
    limit: int = Query(20, description="返回结果数量限制"),
    offset: int = Query(0, description="结果偏移量"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """搜索文档内容"""
    print("=" * 50)
    print("🚀 SEARCH ENDPOINT HIT!")
    print(f"🔍 搜索API调用: q={q}")
    print("=" * 50)
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
        print(f"🔍 找到 {len(documents)} 个文档进行搜索")
        
        # 搜索结果分类
        content_results = []     # 内容匹配的结果
        title_results = []       # 仅标题匹配的结果
        description_results = [] # 仅描述匹配的结果
        
        for i, doc in enumerate(documents):
            print(f"🔍 处理第 {i+1}/{len(documents)} 个文档: {doc.title}")
            
            content_found = False
            
            # 优先搜索文档的预处理内容（不直接读取文件）
            if doc.content_extracted and doc.content:
                print(f"🔍 搜索预处理内容: {doc.title} (内容长度: {len(doc.content)})")
                
                try:
                    # 只搜索数据库中已提取的内容
                    matches = search_service.search_in_text(doc.content, q)
                    print(f"🔍 搜索结果: 找到 {len(matches) if matches else 0} 个匹配")
                    
                    if matches:
                        content_found = True
                        print(f"🔍 内容匹配成功: {doc.title} - 匹配数量: {len(matches)}")
                        # 计算相关度分数 - 内容匹配给最高分
                        base_content_score = 0.8  # 内容匹配基础分最高
                        match_bonus = min(len(matches) / 20.0, 0.15)  # 根据匹配数量给予奖励分
                        score = min(base_content_score + match_bonus, 1.0)
                        
                        # 生成高亮片段
                        highlights = []
                        for match in matches[:3]:  # 显示前3个匹配片段
                            highlights.append({
                                "text": match["text"],
                                "line_number": match["line_number"]
                            })
                        
                        content_results.append({
                            "id": doc.id,
                            "title": doc.title,
                            "description": doc.description,
                            "file_type": doc.file_type,
                            "file_path": doc.file_path,
                            "score": score,
                            "match_count": len(matches),
                            "highlights": highlights,
                            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                            "match_type": "content"  # 标记匹配类型
                        })
                    else:
                        print(f"🔍 预处理内容无匹配: {doc.title}")
                        
                except Exception as e:
                    print(f"🔍 搜索预处理内容 {doc.id} 失败: {str(e)}")
                    print(f"🔍 错误详情: {type(e).__name__}: {e}")
            else:
                print(f"🔍 文档无预处理内容: {doc.title} - content_extracted={doc.content_extracted}")
            
            # 如果内容中没有找到，检查标题和描述
            if not content_found:
                title_match = q.lower() in doc.title.lower()
                description_match = doc.description and q.lower() in doc.description.lower()
                
                if title_match:
                    # 标题匹配分数 - 低于内容匹配
                    base_score = 0.6
                    # 如果标题开头匹配，分数更高
                    if doc.title.lower().startswith(q.lower()):
                        score = base_score + 0.15
                    # 如果是完全匹配，分数最高
                    elif doc.title.lower() == q.lower():
                        score = base_score + 0.2
                    else:
                        score = base_score
                    
                    # 对标题进行高亮处理
                    import re
                    pattern = re.compile(re.escape(q), re.IGNORECASE)
                    highlighted_title = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", doc.title)
                    highlight_text = f"标题: {highlighted_title}"
                    
                    title_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description,
                        "file_type": doc.file_type,
                        "file_path": doc.file_path,
                        "score": score,
                        "match_count": 1,
                        "highlights": [{"text": highlight_text, "line_number": 1}],
                        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        "match_type": "title"  # 标记匹配类型
                    })
                
                elif description_match:
                    # 描述匹配分数 - 最低优先级
                    base_score = 0.4
                    # 计算关键词在描述中出现的次数
                    match_count = doc.description.lower().count(q.lower())
                    # 检查是否在描述开头出现
                    starts_with_keyword = doc.description.lower().startswith(q.lower())
                    
                    # 根据匹配次数和位置调整分数
                    if starts_with_keyword:
                        score = base_score + 0.1
                    elif match_count > 1:
                        score = base_score + 0.05
                    else:
                        score = base_score
                    
                    # 对描述进行高亮处理
                    import re
                    pattern = re.compile(re.escape(q), re.IGNORECASE)
                    highlighted_desc = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", doc.description)
                    
                    # 截取描述的一部分作为高亮显示
                    desc_snippet = doc.description
                    if len(desc_snippet) > 200:
                        # 找到关键词附近的文本
                        match_pos = doc.description.lower().find(q.lower())
                        start = max(0, match_pos - 100)
                        end = min(len(desc_snippet), match_pos + 100)
                        desc_snippet = desc_snippet[start:end]
                        if start > 0:
                            desc_snippet = "..." + desc_snippet
                        if end < len(doc.description):
                            desc_snippet = desc_snippet + "..."
                    
                    highlighted_snippet = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", desc_snippet)
                    highlight_text = f"描述: {highlighted_snippet}"
                    
                    description_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description,
                        "file_type": doc.file_type,
                        "file_path": doc.file_path,
                        "score": score,
                        "match_count": 1,
                        "highlights": [{"text": highlight_text, "line_number": 1}],
                        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        "match_type": "description"  # 标记匹配类型
                    })
        
        # 合并结果：内容匹配优先，然后是标题匹配，最后是描述匹配
        search_results = content_results + title_results + description_results
        
        # 按优先级排序：内容 > 标题 > 描述，同类型内按相关度分数排序
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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """预览文档内容"""
    try:
        # 获取文档 - 所有用户都可以预览所有文档
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        content = None
        content_source = "unknown"
        
        # 根据source参数决定内容来源
        if source == "extracted" or (source == "auto" and document.content_extracted and document.content):
            # 使用预处理的内容
            if document.content_extracted and document.content:
                content = document.content
                content_source = "extracted"
                print(f"🔍 使用预处理内容预览: {document.title} (长度: {len(content)})")
            else:
                # 如果没有预处理内容但请求预处理内容，返回错误信息
                if source == "extracted":
                    error_msg = document.content_extraction_error or "内容尚未提取"
                    raise HTTPException(status_code=400, detail=f"预处理内容不可用: {error_msg}")
        
        # 如果还没有内容，尝试从文件读取
        if not content:
            if not document.file_path or not os.path.exists(document.file_path):
                raise HTTPException(status_code=400, detail="文档文件不存在")
            
            search_service = SearchService()
            content = search_service.extract_file_content(document.file_path)
            content_source = "file"
            print(f"🔍 使用文件直接预览: {document.title}")
            
            if not content:
                raise HTTPException(status_code=400, detail="无法读取文档内容")
        
        # 如果有高亮关键词，添加高亮标记
        if highlight:
            search_service = SearchService()
            content = search_service.highlight_text(content, highlight)
        
        # 限制预览内容长度
        original_length = len(content)
        if len(content) > 10000:
            content = content[:10000] + "\n\n... (内容过长，已截断)"
        
        return {
            "document_id": document_id,
            "title": document.title,
            "file_type": document.file_type,
            "content": content,
            "content_source": content_source,
            "content_extracted": document.content_extracted,
            "content_extraction_error": document.content_extraction_error,
            "original_length": original_length,
            "is_truncated": len(content) < original_length,
            "file_size": os.path.getsize(document.file_path) if document.file_path and os.path.exists(document.file_path) else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

# 资产搜索功能已移除 - 智能搜索模块现在只搜索文档内容

@router.get("/suggestions", summary="获取搜索建议")
async def get_search_suggestions(
    q: Optional[str] = Query(None, description="部分关键词"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取搜索建议"""
    try:
        suggestions = []
        
        if q and len(q) >= 2:
            # 从文档标题中获取建议
            doc_titles = db.query(Document.title).filter(
                Document.title.contains(q)
            ).limit(3).all()
            
            for title in doc_titles:
                if title[0] not in suggestions:
                    suggestions.append(title[0])
            
            # 从文档描述中获取关键词建议
            docs_with_desc = db.query(Document.description).filter(
                Document.description.isnot(None),
                Document.description.contains(q)
            ).limit(5).all()
            
            # 从描述中提取包含搜索词的短语
            import re
            for desc_tuple in docs_with_desc:
                desc = desc_tuple[0]
                if desc:
                    # 找到包含搜索词的句子片段
                    sentences = re.split(r'[，。、；]', desc)
                    for sentence in sentences:
                        if q.lower() in sentence.lower() and len(sentence.strip()) > 0:
                            # 提取关键短语（去掉过长的句子）
                            if len(sentence.strip()) <= 50:
                                clean_sentence = sentence.strip()
                                if clean_sentence not in suggestions and len(suggestions) < 8:
                                    suggestions.append(clean_sentence)
            
            # 资产搜索建议已移除 - 只提供文档相关建议
        else:
            # 返回热门搜索建议 - 仅文档相关
            suggestions = [
                "Nginx配置",
                "数据库优化", 
                "监控告警",
                "故障排查",
                "部署文档",
                "API文档",
                "运维手册",
                "技术规范"
            ]
        
        return {
            "query": q,
            "suggestions": suggestions[:10]  # 最多返回10个建议
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")