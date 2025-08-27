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
        """删除文档（仅数据库记录，不推荐直接使用）"""
        obj = db.query(Document).get(id)
        db.delete(obj)
        db.commit()
        return obj
    
    def delete_with_file(self, db: Session, id: int, backup_before_delete: bool = False) -> dict:
        """
        原子性删除文档记录和物理文件
        
        Args:
            db: 数据库会话
            id: 文档ID
            backup_before_delete: 删除前是否备份文件
            
        Returns:
            删除操作的详细结果
        """
        from app.services.file_manager import FileManagerService
        import logging
        
        logger = logging.getLogger(__name__)
        
        result = {
            "success": False,
            "document_deleted": False,
            "file_deleted": False,
            "document": None,
            "file_result": None,
            "error": None
        }
        
        # 开始数据库事务
        try:
            # 1. 获取文档信息
            document = db.query(Document).get(id)
            if not document:
                result["error"] = "文档不存在"
                return result
            
            result["document"] = {
                "id": document.id,
                "title": document.title,
                "file_path": document.file_path
            }
            
            # 2. 初始化文件管理器
            file_manager = FileManagerService()
            
            # 3. 删除物理文件（如果存在）
            file_deleted = False
            if document.file_path:
                file_result = file_manager.safe_delete_file(
                    document.file_path, 
                    backup_before_delete=backup_before_delete
                )
                result["file_result"] = file_result
                file_deleted = file_result["success"] or not file_result["existed"]
                
                # 如果文件存在但删除失败，回滚事务
                if file_result["existed"] and not file_result["success"]:
                    db.rollback()
                    result["error"] = f"文件删除失败: {file_result['error']}"
                    logger.error(f"文档 {id} 的文件删除失败，操作回滚: {file_result['error']}")
                    return result
            else:
                # 没有文件路径，认为文件已删除
                file_deleted = True
                logger.info(f"文档 {id} 没有关联的物理文件")
            
            # 4. 删除数据库记录
            db.delete(document)
            db.commit()
            
            result["document_deleted"] = True
            result["file_deleted"] = file_deleted
            result["success"] = True
            
            logger.info(f"文档删除成功 - ID: {id}, 标题: {document.title}, 文件: {document.file_path}")
            
        except Exception as e:
            # 发生异常时回滚数据库事务
            db.rollback()
            result["error"] = f"删除操作失败: {str(e)}"
            logger.error(f"文档删除异常 - ID: {id}, 错误: {str(e)}")
        
        return result

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