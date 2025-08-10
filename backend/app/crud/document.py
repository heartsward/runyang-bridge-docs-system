from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from app.models.document import Document, Category, DocumentView, DocumentDownload
from app.schemas.document import DocumentCreate, DocumentUpdate, CategoryCreate, CategoryUpdate


class CRUDDocument:
    def get(self, db: Session, id: int) -> Optional[Document]:
        """根据ID获取文档"""
        return db.query(Document).filter(Document.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        owner_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Document]:
        """获取文档列表"""
        query = db.query(Document)
        
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)
        if category_id:
            query = query.filter(Document.category_id == category_id)
        if status:
            query = query.filter(Document.status == status)
            
        return query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    def count(
        self,
        db: Session,
        owner_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """统计文档数量"""
        query = db.query(Document)
        
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)
        if category_id:
            query = query.filter(Document.category_id == category_id)
        if status:
            query = query.filter(Document.status == status)
            
        return query.count()
    
    def count_recent(
        self,
        db: Session,
        days: int = 7,
        owner_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """统计最近几天的文档数量"""
        from datetime import datetime, timedelta
        
        query = db.query(Document)
        
        # 时间过滤
        recent_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Document.created_at >= recent_date)
        
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)
        if category_id:
            query = query.filter(Document.category_id == category_id)
        if status:
            query = query.filter(Document.status == status)
            
        return query.count()

    def create(self, db: Session, obj_in: DocumentCreate, owner_id: int) -> Document:
        """创建文档"""
        db_obj = Document(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Document, obj_in) -> Document:
        """更新文档"""
        if hasattr(obj_in, 'model_dump'):
            # Pydantic model
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            # Dictionary
            update_data = obj_in
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Document:
        """删除文档"""
        obj = db.query(Document).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def search(
        self, 
        db: Session, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Document]:
        """搜索文档"""
        return db.query(Document).filter(
            Document.title.contains(query) | 
            Document.description.contains(query) |
            Document.content.contains(query)
        ).order_by(desc(Document.updated_at)).offset(skip).limit(limit).all()

    def get_popular(self, db: Session, limit: int = 10) -> List[Document]:
        """获取热门文档"""
        return db.query(Document).order_by(
            desc(Document.view_count)
        ).limit(limit).all()

    def increment_view_count(self, db: Session, document_id: int, user_id: Optional[int] = None, ip_address: Optional[str] = None):
        """增加文档查看次数"""
        # 更新文档查看次数
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.view_count += 1
            db.commit()
        
        # 记录查看日志
        view_log = DocumentView(
            document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.add(view_log)
        db.commit()

    def increment_download_count(self, db: Session, document_id: int, user_id: Optional[int] = None, ip_address: Optional[str] = None):
        """增加文档下载次数"""
        # 更新文档下载次数
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.download_count += 1
            db.commit()
        
        # 记录下载日志
        download_log = DocumentDownload(
            document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.add(download_log)
        db.commit()
    
    def get_categories(self, db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
        """获取分类列表"""
        return db.query(Category).filter(Category.is_active == True).order_by(
            asc(Category.sort_order), asc(Category.name)
        ).offset(skip).limit(limit).all()
    
    def get_category(self, db: Session, id: int) -> Optional[Category]:
        """根据ID获取分类"""
        return db.query(Category).filter(Category.id == id).first()
    
    def create_category(self, db: Session, obj_in: CategoryCreate, creator_id: int) -> Category:
        """创建分类"""
        db_obj = Category(
            **obj_in.model_dump(),
            creator_id=creator_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_category(self, db: Session, db_obj: Category, obj_in: CategoryUpdate) -> Category:
        """更新分类"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete_category(self, db: Session, id: int) -> Category:
        """删除分类"""
        obj = db.query(Category).get(id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDCategory:
    def get(self, db: Session, id: int) -> Optional[Category]:
        """根据ID获取分类"""
        return db.query(Category).filter(Category.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
        """获取分类列表"""
        return db.query(Category).filter(Category.is_active == True).order_by(
            asc(Category.sort_order), asc(Category.name)
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CategoryCreate, creator_id: int) -> Category:
        """创建分类"""
        db_obj = Category(
            **obj_in.model_dump(),
            creator_id=creator_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Category, obj_in: CategoryUpdate) -> Category:
        """更新分类"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Category:
        """删除分类"""
        obj = db.query(Category).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def get_with_document_count(self, db: Session) -> List[dict]:
        """获取分类及文档数量"""
        return db.query(
            Category,
            func.count(Document.id).label('document_count')
        ).outerjoin(Document).group_by(Category.id).all()


document = CRUDDocument()
category = CRUDCategory()