from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class Category(CategoryBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = []
    status: str = "published"
    is_public: bool = True


class DocumentCreate(DocumentBase):
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    content_extracted: Optional[bool] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentInDBBase(DocumentBase):
    id: int
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    view_count: int = 0
    download_count: int = 0
    # 内容提取状态
    content_extracted: Optional[bool] = None
    content_extraction_error: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_tags: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    version: str = "1.0.0"
    parent_id: Optional[int] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Document(DocumentInDBBase):
    pass


class DocumentWithCategory(Document):
    category: Optional[Category] = None


class DocumentList(BaseModel):
    items: List[Document]
    total: int
    page: int
    per_page: int
    pages: int


# 搜索相关
class SearchQuery(BaseModel):
    query: str
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    file_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    per_page: int = 20


class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content_snippet: str
    category: Optional[Category] = None
    tags: List[str]
    file_type: Optional[str] = None
    score: float
    created_at: datetime


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    per_page: int
    pages: int
    query_time: float


# 统计相关
class DocumentStats(BaseModel):
    total_documents: int
    published_documents: int
    draft_documents: int
    categories_count: int
    total_views: int
    total_downloads: int
    avg_confidence_score: Optional[float] = None


class CategoryStats(BaseModel):
    category_id: int
    category_name: str
    document_count: int
    total_views: int
    total_downloads: int


class PopularDocument(BaseModel):
    id: int
    title: str
    view_count: int
    download_count: int
    category_name: Optional[str] = None