from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    content = Column(Text)
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_type = Column(String(50))
    mime_type = Column(String(100))
    
    # 分类和标签
    category_id = Column(Integer, ForeignKey("categories.id"))
    tags = Column(JSON)  # 存储标签数组
    
    # 状态信息
    status = Column(String(20), default="published")  # draft, published, archived
    is_public = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # 内容处理状态
    content_extracted = Column(Boolean, default=None)  # None=提取中, True=已完成, False=失败
    content_extraction_error = Column(Text)  # 内容提取错误信息
    
    # AI分析结果
    ai_summary = Column(Text)  # AI生成的摘要
    ai_tags = Column(JSON)  # AI生成的标签
    confidence_score = Column(Float)  # AI分类置信度
    
    # 版本控制
    version = Column(String(20), default="1.0.0")
    parent_id = Column(Integer, ForeignKey("documents.id"))
    
    # 用户关联
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    owner = relationship("User", back_populates="documents")
    category = relationship("Category", back_populates="documents")
    parent = relationship("Document", remote_side=[id])
    children = relationship("Document", overlaps="parent")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    color = Column(String(20))
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("categories.id"))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # 创建者
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    creator = relationship("User", back_populates="categories")
    documents = relationship("Document", back_populates="category")
    parent = relationship("Category", remote_side=[id])
    children = relationship("Category", overlaps="parent")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    response_time = Column(Float)  # 毫秒
    filters = Column(JSON)  # 搜索过滤条件
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="search_logs")


class DocumentView(Base):
    __tablename__ = "document_views"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    duration = Column(Integer)  # 查看时长（秒）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentDownload(Base):
    __tablename__ = "document_downloads"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AssetView(Base):
    __tablename__ = "asset_views"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    view_type = Column(String(50))  # "credentials" 表示查看用户名密码, "details" 表示查看详情
    duration = Column(Integer)  # 查看时长（秒）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())