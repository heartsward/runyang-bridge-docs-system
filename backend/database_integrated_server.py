#!/usr/bin/env python3
"""
运维文档管理系统 - 数据库集成版后端服务器
使用 yunwei_docs_clean.db 数据库进行数据持久化
"""
import os
import sys
import uuid
import json
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

# 添加应用路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import jwt

# 导入数据库和模型
from app.db.database import SessionLocal, engine
from app.models import user, document, asset
from app.core.config import settings
from app import crud
from app.schemas.document import DocumentCreate

# 导入服务
try:
    from app.services.enhanced_content_extractor import EnhancedContentExtractor
    from app.services.search_service import SearchService  
    from app.services.document_analyzer import DocumentAnalyzer
    from database_task_manager import DatabaseTaskManager
except ImportError as e:
    print(f"警告: 部分服务导入失败: {e}")
    # 回退到原始提取器
    try:
        from app.services.content_extractor import ContentExtractor as EnhancedContentExtractor
    except ImportError:
        EnhancedContentExtractor = None
    SearchService = None
    DocumentAnalyzer = None
    DatabaseTaskManager = None

# 创建数据库表
try:
    user.Base.metadata.create_all(bind=engine)
    document.Base.metadata.create_all(bind=engine)
    asset.Base.metadata.create_all(bind=engine)
    print("数据库表创建/验证成功")
except Exception as e:
    print(f"数据库表创建失败: {e}")

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的代码
    if 'task_manager' in globals() and task_manager:
        task_manager.start_worker()
        print("数据库后台任务处理器已启动")
    
    yield
    
    # 关闭时的代码
    print("服务器关闭中，保存用户分析数据...")
    try:
        save_user_analytics_to_file()
    except:
        pass
    
    if 'task_manager' in globals() and task_manager:
        task_manager.stop_worker()
        print("数据库后台任务处理器已停止")

# 创建FastAPI应用
app = FastAPI(
    title="运维文档管理系统",
    version="2.1.0",
    description="数据库集成版运维文档管理系统后端API",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
content_extractor = EnhancedContentExtractor() if EnhancedContentExtractor else None
search_service = SearchService() if SearchService else None
document_analyzer = DocumentAnalyzer() if DocumentAnalyzer else None

# 确保上传目录存在
upload_dir = "./uploads"
os.makedirs(upload_dir, exist_ok=True)

# 用户数据持久化存储
USERS_DATA_FILE = "./users_data.json"
SECRET_KEY = "your-secret-key-here"

def load_users_from_file():
    """从文件加载用户数据"""
    try:
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('users', {}), data.get('next_user_id', 3)
        else:
            # 如果文件不存在，返回默认用户数据
            default_users = {
                "admin": {
                    "id": 1,
                    "username": "admin",
                    "password": "admin123",
                    "email": "admin@system.com",
                    "full_name": "系统管理员",
                    "department": "技术部",
                    "position": "系统管理员",
                    "phone": "13800138000",
                    "is_active": True,
                    "is_superuser": True,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                "user": {
                    "id": 2,
                    "username": "user",
                    "password": "user123",
                    "email": "user@system.com",
                    "full_name": "普通用户",
                    "department": "业务部",
                    "position": "业务员",
                    "phone": "13800138001",
                    "is_active": True,
                    "is_superuser": False,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
            return default_users, 3
    except Exception as e:
        print(f"加载用户数据失败: {e}")
        # 返回默认用户数据
        default_users = {
            "admin": {
                "id": 1,
                "username": "admin",
                "password": "admin123",
                "email": "admin@system.com",
                "full_name": "系统管理员",
                "department": "技术部",
                "position": "系统管理员",
                "phone": "13800138000",
                "is_active": True,
                "is_superuser": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "user": {
                "id": 2,
                "username": "user",
                "password": "user123",
                "email": "user@system.com",
                "full_name": "普通用户",
                "department": "业务部",
                "position": "业务员",
                "phone": "13800138001",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        return default_users, 3

def save_users_to_file():
    """保存用户数据到文件"""
    try:
        data = {
            'users': USERS,
            'next_user_id': next_user_id,
            'updated_at': datetime.utcnow().isoformat() + "Z"
        }
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 用户数据已保存
    except Exception as e:
        print(f"保存用户数据失败: {e}")

# 从文件加载用户数据
USERS, next_user_id = load_users_from_file()
# 加载完成

# 如果是首次运行（没有数据文件），保存初始数据
if not os.path.exists(USERS_DATA_FILE):
    save_users_to_file()

# Pydantic模型
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DocumentInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    tags: List[str] = []
    status: str = "published"
    content_extracted: Optional[bool] = None
    ai_summary: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    owner: Dict[str, str]

class SearchRequest(BaseModel):
    query: str
    file_types: Optional[List[str]] = None
    max_results: int = 20

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    is_superuser: bool = False

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = None  # 添加密码字段支持

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: str

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 工具函数
def verify_password(plain_password: str, stored_password: str) -> bool:
    return plain_password == stored_password

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = None):
    """获取当前用户信息"""
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = USERS.get(username)
        if user is None:
            return None
        return user
    except jwt.PyJWTError as e:
        print(f"JWT解码错误: {e}")
        return None
    except Exception as e:
        print(f"获取用户信息错误: {e}")
        return None

def require_auth(token: str = None):
    """要求用户认证"""
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="未认证或token无效")
    return user

def require_admin(token: str = None):
    """要求管理员权限"""
    user = require_auth(token)
    if not user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user

def get_token_from_header(authorization: str = Header(None)):
    """从Authorization头中提取token"""
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return None

def get_current_user_dep(token: str = Depends(get_token_from_header)):
    """依赖注入：获取当前用户"""
    return get_current_user(token)

def require_auth_dep(token: str = Depends(get_token_from_header)):
    """依赖注入：要求认证"""
    return require_auth(token)

def require_admin_dep(token: str = Depends(get_token_from_header)):
    """依赖注入：要求管理员权限"""
    return require_admin(token)

def allowed_file(filename: str) -> bool:
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'md', 'xls', 'xlsx', 'csv', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 数据库任务管理器
class DatabaseTaskManager:
    """数据库集成任务管理器"""
    
    def __init__(self, content_extractor=None):
        self.content_extractor = content_extractor
        self.task_queue = []
        self.is_running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        
        # 创建任务状态存储目录
        self.task_dir = Path("./task_status")
        self.task_dir.mkdir(exist_ok=True)
        
    def start_worker(self):
        """启动后台任务处理器"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("数据库任务处理器已启动")
    
    def stop_worker(self):
        """停止后台任务处理器"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("数据库任务处理器已停止")
    
    def add_content_extraction_task(self, document_id: int, file_path: str, title: str) -> str:
        """添加内容提取任务"""
        task_id = f"extract_{document_id}_{int(time.time())}"
        
        task = {
            "task_id": task_id,
            "task_type": "content_extraction",
            "document_id": document_id,
            "file_path": file_path,
            "title": title,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "progress": 0
        }
        
        # 保存任务状态
        self._save_task_status(task_id, task)
        
        # 添加到队列
        with self.lock:
            self.task_queue.append(task)
        
        print(f"已添加内容提取任务: {task_id} - {title}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        status_file = self.task_dir / f"{task_id}.json"
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取任务状态失败: {e}")
        return None
    
    def get_document_extraction_status(self, document_id: int) -> Optional[Dict[str, Any]]:
        """获取文档的提取状态"""
        for task_file in sorted(self.task_dir.glob(f"extract_{document_id}_*.json"), reverse=True):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                    return {
                        "task_id": task_data["task_id"],
                        "status": task_data["status"],
                        "progress": task_data.get("progress", 0),
                        "error": task_data.get("error"),
                        "created_at": task_data["created_at"],
                        "completed_at": task_data.get("completed_at")
                    }
            except Exception:
                continue
        return None
    
    def _save_task_status(self, task_id: str, task_data: Dict[str, Any]):
        """保存任务状态"""
        status_file = self.task_dir / f"{task_id}.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务状态失败: {e}")
    
    def _worker_loop(self):
        """后台任务处理循环"""
        print("数据库任务处理循环已启动")
        
        while self.is_running:
            try:
                task = None
                
                with self.lock:
                    if self.task_queue:
                        task = self.task_queue.pop(0)
                
                if task:
                    self._process_task(task)
                else:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"后台任务处理异常: {e}")
                time.sleep(5)
    
    def _process_task(self, task: Dict[str, Any]):
        """处理单个任务"""
        task_id = task["task_id"]
        task_type = task["task_type"]
        
        print(f"开始处理任务: {task_id} - {task_type}")
        
        task["status"] = "processing"
        task["started_at"] = datetime.utcnow().isoformat()
        task["progress"] = 10
        self._save_task_status(task_id, task)
        
        try:
            if task_type == "content_extraction":
                self._process_content_extraction(task)
            else:
                raise ValueError(f"未知任务类型: {task_type}")
                
        except Exception as e:
            print(f"任务处理失败: {task_id} - {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.utcnow().isoformat()
            self._save_task_status(task_id, task)
    
    def _process_content_extraction(self, task: Dict[str, Any]):
        """处理内容提取任务 - 数据库版本"""
        document_id = task["document_id"]
        file_path = task["file_path"]
        title = task["title"]
        task_id = task["task_id"]
        
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")
        
        task["progress"] = 30
        self._save_task_status(task_id, task)
        
        if not self.content_extractor or not self.content_extractor.is_supported_file(file_path):
            raise Exception("不支持的文件格式或提取器不可用")
        
        task["progress"] = 50
        self._save_task_status(task_id, task)
        
        print(f"开始提取文档内容: {title}")
        content, error = self.content_extractor.extract_content(file_path)
        
        task["progress"] = 80
        self._save_task_status(task_id, task)
        
        # 更新数据库中的文档
        db = SessionLocal()
        try:
            document_obj = crud.document.get(db=db, id=document_id)
            if document_obj:
                if content:
                    # 更新文档内容
                    update_data = {
                        "content": content,
                        "content_extracted": True,
                        "content_extraction_error": None,
                        "updated_at": datetime.utcnow()
                    }
                    crud.document.update(db=db, db_obj=document_obj, obj_in=update_data)
                    db.commit()
                    print(f"内容提取成功: {title}, 内容长度: {len(content)}")
                    
                    task["status"] = "completed"
                    task["result"] = {
                        "content_length": len(content),
                        "extraction_success": True
                    }
                else:
                    # 提取失败
                    update_data = {
                        "content_extracted": False,
                        "content_extraction_error": error,
                        "updated_at": datetime.utcnow()
                    }
                    crud.document.update(db=db, db_obj=document_obj, obj_in=update_data)
                    db.commit()
                    print(f"内容提取失败: {title}, 错误: {error}")
                    
                    task["status"] = "failed"
                    task["error"] = error or "内容提取失败"
            else:
                raise Exception(f"数据库中文档不存在: {document_id}")
                
        except Exception as e:
            db.rollback()
            print(f"更新数据库失败: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
        finally:
            db.close()
        
        task["progress"] = 100
        task["completed_at"] = datetime.utcnow().isoformat()
        self._save_task_status(task_id, task)
        
        print(f"任务完成: {task_id}")

# 初始化数据库任务管理器
task_manager = DatabaseTaskManager(content_extractor)

# 基础API端点
@app.get("/")
def read_root():
    return {
        "message": "运维文档管理系统后端API - 数据库集成版",
        "status": "running",
        "version": "2.1.0",
        "database": "yunwei_docs_clean.db",
        "features": [
            "用户认证",
            "文档上传",
            "内容提取", 
            "智能搜索",
            "标签管理",
            "资产管理",
            "数据持久化"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "version": "2.1.0",
        "database": "yunwei_docs_clean.db",
        "services": {
            "content_extractor": content_extractor is not None,
            "search_service": search_service is not None,
            "document_analyzer": document_analyzer is not None,
            "task_manager": task_manager is not None,
        }
    }

# 认证相关API
@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: LoginRequest):
    """用户登录接口"""
    user = USERS.get(form_data.username)
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(require_auth_dep)):
    """获取当前用户信息"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "department": current_user.get("department"),
        "position": current_user.get("position"),
        "phone": current_user.get("phone"),
        "is_active": current_user.get("is_active", True),
        "is_superuser": current_user.get("is_superuser", False)
    }

# 文档上传API - 仅管理员
@app.post("/api/v1/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep)
):
    """上传文档文件"""
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: pdf, doc, docx, txt, md, xls, xlsx, csv"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)"
        )
    
    # 生成唯一文件名
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
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
    
    # 创建文档记录到数据库
    # 注意：如果前端进行了重命名，title 应该是处理后的文件名（不含扩展名）
    # 我们需要重新构建完整的文件名用于存储
    processed_filename = f"{title}.{file_extension}" if title and not title.endswith(f".{file_extension}") else (title or file.filename)
    
    print(f"上传文档: 原始文件名='{file.filename}', 处理后标题='{title}', 存储文件名='{processed_filename}'")
    
    document_data = DocumentCreate(
        title=title,
        description=description,
        file_name=processed_filename,  # 使用处理后的文件名
        file_path=file_path,
        file_size=file_size,
        file_type=file_extension,
        tags=tag_list,
        status="published",
        content_extracted=None  # 待提取
    )
    
    try:
        # 保存到数据库 - 使用admin用户ID (假设为1)
        document_obj = crud.document.create(db=db, obj_in=document_data, owner_id=1)
        
        # 异步提取文档内容
        if task_manager:
            try:
                task_id = task_manager.add_content_extraction_task(
                    document_id=document_obj.id,
                    file_path=file_path,
                    title=title
                )
                print(f"已添加内容提取任务: {title} - 任务ID: {task_id}")
            except Exception as e:
                print(f"添加提取任务失败: {e}")
        
        # 返回文档信息
        return {
            "id": document_obj.id,
            "title": document_obj.title,
            "description": document_obj.description,
            "file_name": document_obj.file_name,
            "file_size": document_obj.file_size,
            "file_type": document_obj.file_type,
            "tags": document_obj.tags or [],
            "status": document_obj.status,
            "content_extracted": document_obj.content_extracted,
            "ai_summary": document_obj.ai_summary,
            "created_at": document_obj.created_at.isoformat(),
            "updated_at": document_obj.updated_at.isoformat() if document_obj.updated_at else None,
            "owner": {"username": "admin", "full_name": "系统管理员"}
        }
        
    except Exception as e:
        db.rollback()
        # 清理已保存的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"保存文档失败: {str(e)}")

# 检查文件名是否已存在的API
@app.get("/api/v1/documents/check-filename")
async def check_filename_exists(
    filename: str = Query(..., description="要检查的文件名"),
    db: Session = Depends(get_db)
):
    """检查文件名是否已存在"""
    try:
        print(f"\n=== 检查文件名冲突: '{filename}' ===")
        
        # 查询数据库中是否已有相同文件名的文档
        existing_docs = db.query(document.Document).filter(
            document.Document.file_name == filename
        ).all()
        
        result_exists = len(existing_docs) > 0
        print(f"精确匹配结果: exists={result_exists}, count={len(existing_docs)}")
        
        if result_exists:
            for doc in existing_docs[:3]:  # 只显示前3个
                print(f"  匹配文档: ID={doc.id}, title='{doc.title}', file_name='{doc.file_name}'")
        else:
            print(f"  没有找到精确匹配 '{filename}' 的文档")
        
        print(f"=== 检查完成 ===\n")
        
        return {
            "exists": result_exists,
            "count": len(existing_docs),
            "existing_documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "file_name": doc.file_name,
                    "created_at": doc.created_at.isoformat()
                } for doc in existing_docs[:5]  # 最多返回5个重复文档
            ] if result_exists else []
        }
        
    except Exception as e:
        print(f"检查文件名时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return {
            "exists": False,
            "count": 0,
            "existing_documents": [],
            "error": str(e)
        }

# 文档相关API
@app.get("/api/v1/documents")
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取文档列表"""
    documents = crud.document.get_multi(db=db, skip=skip, limit=limit)
    total = crud.document.count(db=db)
    
    items = []
    for doc in documents:
        # 检查提取状态
        content_extracted = doc.content_extracted
        extraction_error = None
        
        if content_extracted is None and task_manager:
            # 检查任务状态
            status = task_manager.get_document_extraction_status(doc.id)
            if status:
                if status["status"] == "completed":
                    content_extracted = True
                elif status["status"] == "failed":
                    content_extracted = False
                    extraction_error = status.get("error", "提取失败")
        
        items.append({
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "tags": doc.tags or [],
            "status": doc.status,
            "content_extracted": content_extracted,
            "ai_summary": doc.ai_summary,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "owner": {"username": "admin", "full_name": "系统管理员"}
        })
    
    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """获取文档详情"""
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查提取状态
    content_extracted = document_obj.content_extracted
    extraction_error = None
    
    if content_extracted is None and task_manager:
        status = task_manager.get_document_extraction_status(document_id)
        if status:
            if status["status"] == "completed":
                content_extracted = True
            elif status["status"] == "failed":
                content_extracted = False
                extraction_error = status.get("error", "提取失败")
    
    result = {
        "id": document_obj.id,
        "title": document_obj.title,
        "description": document_obj.description,
        "file_name": document_obj.file_name,
        "file_size": document_obj.file_size,
        "file_type": document_obj.file_type,
        "tags": document_obj.tags or [],
        "status": document_obj.status,
        "content_extracted": content_extracted,
        "ai_summary": document_obj.ai_summary,
        "created_at": document_obj.created_at.isoformat(),
        "updated_at": document_obj.updated_at.isoformat() if document_obj.updated_at else None,
        "owner": {"username": "admin", "full_name": "系统管理员"}
    }
    
    if extraction_error:
        result["extraction_error"] = extraction_error
    
    return result

@app.get("/api/v1/documents/{document_id}/download")
async def download_document(document_id: int, db: Session = Depends(get_db)):
    """下载文档文件"""
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    file_path = document_obj.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=document_obj.file_name,
        media_type='application/octet-stream'
    )

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin_dep)):
    """删除文档"""
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 删除物理文件
        if document_obj.file_path and os.path.exists(document_obj.file_path):
            os.remove(document_obj.file_path)
        
        # 从数据库删除记录
        crud.document.delete(db=db, id=document_id)
        
        return {"message": "文档删除成功", "id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.put("/api/v1/documents/{document_id}")
async def update_document(
    document_id: int, 
    title: str = Form(...),
    description: str = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep)
):
    """更新文档信息"""
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    try:
        # 处理标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 更新数据
        update_data = {
            "title": title,
            "description": description,
            "tags": tag_list
        }
        
        updated_doc = crud.document.update(db=db, db_obj=document_obj, obj_in=update_data)
        
        return {
            "id": updated_doc.id,
            "title": updated_doc.title,
            "description": updated_doc.description,
            "tags": updated_doc.tags,
            "updated_at": updated_doc.updated_at.isoformat() if updated_doc.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@app.get("/api/v1/search/preview/{document_id}")
async def preview_document(
    document_id: int,
    highlight: Optional[str] = Query(None, description="高亮关键词"), 
    page: int = Query(1, ge=1), 
    page_size: int = Query(5000, ge=1000, le=10000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dep)
):
    """预览文档内容（支持分页）"""
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 跟踪文档查看 - 使用当前用户ID
    user_id = current_user.get("id", 1) if current_user else 1
    track_document_view(document_id, user_id)
    
    # 如果内容还未提取完成
    if document_obj.content_extracted is None:
        return {
            "content": "内容正在提取中，请稍后再试...",
            "page": 1,
            "total_pages": 1,
            "status": "extracting"
        }
    
    # 如果内容提取失败
    if document_obj.content_extracted is False:
        error_msg = document_obj.content_extraction_error or "内容提取失败"
        return {
            "content": f"无法预览文档内容: {error_msg}",
            "page": 1,
            "total_pages": 1,
            "status": "error"
        }
    
    # 获取文档内容
    content = document_obj.content or ""
    
    if not content:
        return {
            "content": "文档内容为空",
            "page": 1,
            "total_pages": 1,
            "status": "empty"
        }
    
    # 分页处理
    if content_extractor:
        pages = content_extractor.split_content_pages(content, page_size)
    else:
        # 简单分页
        pages = []
        for i in range(0, len(content), page_size):
            pages.append(content[i:i + page_size])
    
    total_pages = len(pages)
    
    if page > total_pages:
        raise HTTPException(status_code=404, detail="页码超出范围")
    
    current_content = pages[page - 1] if pages else ""
    
    # 如果有高亮关键词，添加高亮标记
    if highlight and current_content:
        current_content = highlight_text(current_content, highlight)
    
    return {
        "content": current_content,
        "page": page,
        "total_pages": total_pages,
        "status": "success",
        "highlight": highlight,
        "content_source": "extracted",  # 直接显示使用预处理内容
        "document_info": {
            "title": document_obj.title,
            "file_type": document_obj.file_type,
            "file_size": document_obj.file_size,
            "content_extracted": document_obj.content_extracted
        }
    }

# 搜索相关API
@app.post("/api/v1/search")
async def search_documents(search_request: SearchRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user_dep)):
    """搜索文档内容 - 智能搜索"""
    import time
    start_time = time.time()
    
    query = search_request.query.lower().strip()
    if not query:
        return {
            "results": [],
            "total": 0,
            "page": 1,
            "per_page": search_request.max_results,
            "pages": 0,
            "query_time": 0.0
        }
    
    # 跟踪搜索关键词 - 使用当前用户ID
    user_id = current_user.get("id", 1) if current_user else 1
    track_search_keyword(query, user_id)
    
    # 从数据库获取所有文档
    documents = crud.document.get_multi(db=db, skip=0, limit=1000)  # 获取更多文档用于搜索
    
    results = []
    
    for doc in documents:
        score = 0.0
        matches = []
        
        # 1. 内容匹配（最高权重 - 用户要求优先级最高）
        content = doc.content or ""
        if content and query in content.lower():
            score += 3.0
            matches.append("内容")
        
        # 2. 标题匹配（中权重 - 用户要求优先级第二）
        if query in doc.title.lower():
            score += 2.0
            matches.append("标题")
        
        # 3. 描述匹配（低权重 - 用户要求优先级最低）
        description = doc.description or ""
        if description and query in description.lower():
            score += 1.0
            matches.append("描述")
        
        # 4. 标签匹配（低权重）
        tags = doc.tags or []
        for tag in tags:
            if query in tag.lower():
                score += 1.0
                matches.append("标签")
                break
        
        # 5. 文件名匹配（低权重）
        file_name = doc.file_name or ""
        if file_name and query in file_name.lower():
            score += 0.5
            matches.append("文件名")
        
        # 提取内容片段用于显示
        if content and query in content.lower():
            content_snippet = extract_content_snippet(content, query, 200)
        else:
            content_snippet = description[:200] if description else ""
        
        # 如果有匹配，添加到结果
        if score > 0:
            results.append({
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "content_snippet": content_snippet,
                "category": {"id": 1, "name": "默认分类"},
                "tags": doc.tags or [],
                "score": min(score, 5.0),
                "created_at": doc.created_at.isoformat(),
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "matches": matches,
                "content_extracted": doc.content_extracted
            })
    
    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 分页
    total = len(results)
    results = results[:search_request.max_results]
    
    query_time = time.time() - start_time
    
    return {
        "results": results,
        "total": total,
        "page": 1,
        "per_page": search_request.max_results,
        "pages": 1,
        "query_time": round(query_time, 3),
        "query": search_request.query
    }

# 添加GET方法的搜索路由以兼容前端调用
@app.get("/api/v1/search/documents")
async def search_documents_get(
    q: str = Query(..., description="搜索关键词"),
    doc_type: Optional[str] = Query(None, description="文档类型过滤"),
    limit: int = Query(20, description="返回结果数量限制"),
    offset: int = Query(0, description="结果偏移量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dep)
):
    """GET方法搜索文档 - 兼容前端调用"""
    import time
    start_time = time.time()
    
    query = q.lower().strip()
    if not query:
        return {
            "query": q,
            "total": 0,
            "limit": limit,
            "offset": offset,
            "results": []
        }
    
    # 跟踪搜索关键词 - 使用当前用户ID
    user_id = current_user.get("id", 1) if current_user else 1
    track_search_keyword(query, user_id)
    
    # 从数据库获取所有文档
    documents = crud.document.get_multi(db=db, skip=0, limit=1000)
    
    results = []
    content_matches = 0
    title_matches = 0
    description_matches = 0
    
    for doc in documents:
        score = 0.0
        matches = []
        match_details = []
        highlighted_snippets = []
        
        # 1. 内容匹配（最高权重）
        content = doc.content or ""
        if content and query in content.lower():
            score += 3.0
            matches.append("内容")
            content_matches += 1
            # 生成高亮内容片段
            highlighted_content = highlight_text_snippet(content, query, 200)
            highlighted_snippets.append({
                "type": "content",
                "text": highlighted_content,
                "label": "文档内容"
            })
        
        # 2. 标题匹配（中权重）
        if query in doc.title.lower():
            score += 2.0
            matches.append("标题")
            title_matches += 1
            # 生成高亮标题
            highlighted_title = highlight_text(doc.title, query)
            highlighted_snippets.append({
                "type": "title", 
                "text": highlighted_title,
                "label": "文档标题"
            })
        
        # 3. 描述匹配（低权重）
        description = doc.description or ""
        if description and query in description.lower():
            score += 1.0
            matches.append("描述")
            description_matches += 1
            # 生成高亮描述片段
            highlighted_desc = highlight_text_snippet(description, query, 150)
            highlighted_snippets.append({
                "type": "description",
                "text": highlighted_desc,
                "label": "文档描述"
            })
        
        # 4. 文件名匹配
        file_name = doc.file_name or ""
        if file_name and query in file_name.lower():
            score += 0.5
            matches.append("文件名")
            highlighted_filename = highlight_text(file_name, query)
            highlighted_snippets.append({
                "type": "filename",
                "text": highlighted_filename,
                "label": "文件名"
            })
        
        # 如果有匹配，添加到结果
        if score > 0:
            # 确定主要匹配类型
            if "内容" in matches:
                match_type = "content"
                match_priority = 1
            elif "标题" in matches:
                match_type = "title" 
                match_priority = 2
            elif "描述" in matches:
                match_type = "description"
                match_priority = 3
            else:
                match_type = "filename"
                match_priority = 4
            
            results.append({
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "category": {"id": 1, "name": "默认分类"},
                "tags": doc.tags or [],
                "score": min(score, 5.0),
                "created_at": doc.created_at.isoformat(),
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "matches": matches,
                "match_type": match_type,
                "match_priority": match_priority,
                "highlighted_snippets": highlighted_snippets,
                "content_extracted": doc.content_extracted
            })
    
    # 按分数和优先级排序（确保内容>标题>描述的优先级）
    results.sort(key=lambda x: (x["score"], -x["match_priority"]), reverse=True)
    
    # 分页
    total = len(results)
    results_page = results[offset:offset + limit]
    
    return {
        "query": q,
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results_page,
        "statistics": {
            "content_matches": content_matches,
            "title_matches": title_matches, 
            "description_matches": description_matches,
            "total_matches": total
        }
    }

def highlight_text(text: str, query: str) -> str:
    """高亮显示文本中的关键词"""
    import re
    if not text or not query:
        return text
    
    try:
        # 使用正则表达式进行不区分大小写的替换
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: f'<mark class="highlight">{m.group()}</mark>', text)
        return highlighted
    except:
        return text

def highlight_text_snippet(text: str, query: str, max_length: int = 200) -> str:
    """提取并高亮显示包含关键词的文本片段"""
    if not text or not query:
        return ""
    
    text_lower = text.lower()
    query_lower = query.lower()
    
    # 找到查询词在文本中的位置
    pos = text_lower.find(query_lower)
    if pos == -1:
        return text[:max_length] + ("..." if len(text) > max_length else "")
    
    # 计算截取范围，确保查询词在中间
    start = max(0, pos - max_length // 2)
    end = min(len(text), start + max_length)
    
    # 如果从开头开始，调整结束位置
    if start == 0:
        end = min(len(text), max_length)
    # 如果到结尾结束，调整开始位置  
    elif end == len(text):
        start = max(0, len(text) - max_length)
    
    snippet = text[start:end]
    
    # 添加省略号
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    # 高亮显示
    return highlight_text(snippet, query)

def extract_content_snippet(content: str, query: str, max_length: int = 200) -> str:
    """从内容中提取包含查询词的片段"""
    if not content or not query:
        return ""
    
    content_lower = content.lower()
    query_lower = query.lower()
    
    pos = content_lower.find(query_lower)
    if pos == -1:
        return content[:max_length] + "..." if len(content) > max_length else content
    
    start = max(0, pos - max_length // 2)
    end = min(len(content), start + max_length)
    
    if start > 0:
        for i in range(start, min(start + 50, len(content))):
            if content[i] in ' .\n':
                start = i + 1
                break
    
    snippet = content[start:end]
    highlighted = snippet.replace(query, f"**{query}**")
    
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    
    return f"{prefix}{highlighted}{suffix}"

@app.get("/api/v1/search/suggestions")
async def get_search_suggestions():
    """获取搜索建议"""
    return {
        "suggestions": [
            "服务器配置",
            "网络设备",
            "安全策略",
            "备份方案",
            "监控系统",
            "故障处理",
            "系统维护"
        ]
    }

# 任务相关API
@app.get("/api/v1/tasks")
async def get_tasks():
    """获取任务列表"""
    if not task_manager:
        return {"items": [], "total": 0}
    
    tasks = []
    task_dir = Path("./task_status")
    if task_dir.exists():
        for task_file in sorted(task_dir.glob("*.json"), reverse=True)[:10]:
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                    tasks.append({
                        "id": task_data["task_id"],
                        "type": task_data["task_type"],
                        "status": task_data["status"],
                        "progress": task_data.get("progress", 0),
                        "created_at": task_data["created_at"],
                        "document_title": task_data.get("title", "")
                    })
            except Exception:
                continue
    
    return {"items": tasks, "total": len(tasks)}

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if not task_manager:
        raise HTTPException(status_code=404, detail="任务管理器不可用")
    
    status = task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status

@app.get("/api/v1/tasks/document/{document_id}/extraction-status")
async def get_document_extraction_status(document_id: int, db: Session = Depends(get_db)):
    """获取文档的内容提取状态"""
    # 检查文档是否存在
    document_obj = crud.document.get(db=db, id=document_id)
    if not document_obj:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 首先检查任务管理器中的状态
    if task_manager:
        status = task_manager.get_document_extraction_status(document_id)
        if status:
            return status
    
    # 如果任务管理器中没有状态，检查数据库中的提取状态
    if document_obj.content_extracted is True:
        return {
            "status": "completed",
            "progress": 100,
            "content_length": len(document_obj.content) if document_obj.content else 0,
            "extraction_success": True,
            "completed_at": document_obj.updated_at.isoformat() if document_obj.updated_at else None
        }
    elif document_obj.content_extracted is False:
        return {
            "status": "failed",
            "progress": 0,
            "error": document_obj.content_extraction_error or "内容提取失败",
            "extraction_success": False
        }
    else:
        return {
            "status": "pending",
            "progress": 0,
            "extraction_success": None
        }

# 其他API端点
@app.get("/api/v1/analytics/stats")
async def get_analytics_stats(current_user: dict = Depends(require_admin_dep)):
    """系统统计信息"""
    global assets_storage
    
    try:
        # 获取真实的资产统计
        total_assets = len(assets_storage) if assets_storage else 0
        
        # 计算资产相关统计
        active_assets = 0
        maintenance_assets = 0
        recent_assets = 0
        
        if assets_storage:
            active_assets = len([asset for asset in assets_storage if asset.get('status') == 'active'])
            maintenance_assets = len([asset for asset in assets_storage if asset.get('status') == 'maintenance'])
            
            # 计算最近新增资产（最近7天）
            from datetime import datetime, timedelta
            recent_date = datetime.utcnow() - timedelta(days=7)
            
            for asset in assets_storage:
                try:
                    created_at = datetime.fromisoformat(asset.get("created_at", "").replace("Z", "+00:00"))
                    if created_at > recent_date:
                        recent_assets += 1
                except:
                    pass
        
        # 获取文档统计并生成用户活动统计
        total_documents = 0
        recent_uploads = 0
        user_activity_stats = []
        global USERS
        
        # 创建数据库会话用于文档和用户活动统计
        db = None
        try:
            db = SessionLocal()
            # 直接查询文档总数
            from app.models.document import Document
            total_documents = db.query(Document).count()
            
            # 查询最近7天上传的文档
            from datetime import datetime, timedelta
            recent_date = datetime.utcnow() - timedelta(days=7)
            recent_uploads = db.query(Document).filter(Document.created_at >= recent_date).count()
            
            print(f"成功获取文档统计: 总数={total_documents}, 最近上传={recent_uploads}")
        except Exception as e:
            print(f"获取文档统计失败，使用0值: {e}")
            # 使用0作为默认值，表示没有数据
            total_documents = 0
            recent_uploads = 0
            # 如果数据库连接失败，关闭连接并设为None
            if db:
                try:
                    db.close()
                except:
                    pass
                db = None
        
        # 基于真实用户数据生成活动统计（可能使用db会话获取真实名称）
        for username, user_data in USERS.items():
            user_id = user_data.get("id")
            
            # 统计该用户的文档查看次数
            document_views = 0
            document_details = []
            for doc_id, view_data in DOCUMENT_VIEWS.items():
                if user_id in view_data.get("users", set()):
                    # 计算该用户对此文档的查看次数（简化统计）
                    user_view_count = view_data["count"] // len(view_data.get("users", {1}))  # 平均分配
                    document_views += user_view_count
                    
                    # 从数据库获取真实的文档标题
                    document_title = f"文档{doc_id}"  # 默认标题
                    if db:
                        try:
                            document_obj = crud.document.get(db=db, id=doc_id)
                            if document_obj:
                                document_title = document_obj.title
                        except Exception as e:
                            print(f"获取文档{doc_id}标题失败: {e}")
                    
                    document_details.append({
                        "documentId": doc_id,
                        "documentTitle": document_title,
                        "accessCount": user_view_count,
                        "lastAccess": view_data.get("last_viewed")
                    })
            
            # 统计该用户的资产查看次数
            asset_views = 0
            asset_details = []
            for asset_id, view_data in ASSET_VIEWS.items():
                if user_id in view_data.get("users", set()):
                    # 计算该用户对此资产的查看次数
                    user_view_count = view_data["count"] // len(view_data.get("users", {1}))  # 平均分配
                    asset_views += user_view_count
                    
                    # 从资产存储获取真实的资产名称
                    asset_name = f"资产设备{asset_id}"  # 默认名称
                    try:
                        for asset in assets_storage:
                            if asset["id"] == asset_id:
                                asset_name = asset["name"]
                                break
                    except Exception as e:
                        print(f"获取资产{asset_id}名称失败: {e}")
                    
                    asset_details.append({
                        "assetId": asset_id,
                        "assetName": asset_name,
                        "accessCount": user_view_count,
                        "lastAccess": view_data.get("last_viewed")
                    })
            
            # 统计该用户的搜索次数
            searches = 0
            for keyword, search_data in SEARCH_KEYWORDS_COUNT.items():
                if user_id in search_data.get("users", set()):
                    searches += search_data["count"] // len(search_data.get("users", {1}))  # 平均分配
            
            # 计算最后活动时间
            last_activity = None
            activity_times = []
            for doc_id, view_data in DOCUMENT_VIEWS.items():
                if user_id in view_data.get("users", set()) and view_data.get("last_viewed"):
                    activity_times.append(view_data["last_viewed"])
            for asset_id, view_data in ASSET_VIEWS.items():
                if user_id in view_data.get("users", set()) and view_data.get("last_viewed"):
                    activity_times.append(view_data["last_viewed"])
            
            if activity_times:
                last_activity = max(activity_times)
            
            user_activity_stats.append({
                "userId": user_id,
                "username": user_data.get("full_name") or username,
                "department": user_data.get("department", "未设置"),
                "documentViews": document_views,
                "searches": searches,
                "assetViews": asset_views,  # 添加资产查看统计
                "lastActivity": last_activity or datetime.utcnow().isoformat() + "Z",
                "documentAccess": document_details[:5],  # 最多显示5个
                "assetAccess": asset_details[:5]  # 最多显示5个
            })
        
        # 按文档查看次数排序
        user_activity_stats.sort(key=lambda x: x["documentViews"] + x["assetViews"], reverse=True)
        
        # 关闭数据库会话
        if db:
            db.close()
        
        # 搜索关键词排行数据 - 使用真实跟踪数据
        real_keywords = []
        print(f"DEBUG: SEARCH_KEYWORDS_COUNT has {len(SEARCH_KEYWORDS_COUNT)} items")
        for keyword, data in SEARCH_KEYWORDS_COUNT.items():
            print(f"DEBUG: Found keyword '{keyword}' with count {data['count']}")
            real_keywords.append({
                "keyword": keyword,
                "count": data["count"],
                "growth": 15  # 模拟增长率
            })
        
        # 按搜索次数排序
        real_keywords.sort(key=lambda x: x["count"], reverse=True)
        print(f"DEBUG: real_keywords has {len(real_keywords)} items")
        
        # 直接使用真实数据，如果没有真实数据则显示空
        search_keywords = real_keywords[:10] if real_keywords else []

        # 计算真实的查看统计
        total_document_views = sum(data["count"] for data in DOCUMENT_VIEWS.values())
        total_asset_views = sum(data["count"] for data in ASSET_VIEWS.values())
        total_searches_real = sum(data["count"] for data in SEARCH_KEYWORDS_COUNT.values())
        
        return {
            "total_documents": total_documents,
            "total_assets": total_assets,
            "active_assets": active_assets,
            "maintenance_assets": maintenance_assets,
            "recent_assets": recent_assets,
            "total_users": len(USERS),
            "total_searches": total_searches_real,
            "total_document_views": total_document_views,
            "total_asset_views": total_asset_views,
            "recent_uploads": recent_uploads,
            "system_status": "healthy",
            "userActivityStats": user_activity_stats,
            "searchKeywords": search_keywords,
            "user_activity_log": USER_ACTIVITY_LOG[-20:] if USER_ACTIVITY_LOG else []  # 最近20条活动
        }
    except Exception as e:
        print(f"获取分析统计失败: {e}")
        # 返回零值，表示系统中没有数据
        return {
            "total_documents": 0,
            "total_assets": 0,
            "active_assets": 0,
            "maintenance_assets": 0,
            "recent_assets": 0,
            "total_users": len(USERS) if 'USERS' in globals() else 1,
            "total_searches": 0,
            "total_document_views": 0,
            "total_asset_views": 0,
            "recent_uploads": 0,
            "system_status": "error",
            "userActivityStats": [],
            "searchKeywords": []
        }

# 资产数据持久化存储
ASSETS_DATA_FILE = "./assets_data.json"

# 用户行为跟踪数据文件
USER_ANALYTICS_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_analytics_data.json")

# 用户行为跟踪存储
USER_ACTIVITY_LOG = []
SEARCH_KEYWORDS_COUNT = {}
DOCUMENT_VIEWS = {}
ASSET_VIEWS = {}

def load_assets_from_file():
    """从文件加载资产数据"""
    try:
        if os.path.exists(ASSETS_DATA_FILE):
            with open(ASSETS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('assets', []), data.get('next_id', 6)
        else:
            # 如果文件不存在，返回初始数据
            return get_initial_assets(), 6
    except Exception as e:
        print(f"加载资产数据失败: {e}")
        return get_initial_assets(), 6

def save_assets_to_file():
    """保存资产数据到文件"""
    try:
        data = {
            'assets': assets_storage,
            'next_id': next_asset_id,
            'updated_at': datetime.utcnow().isoformat() + "Z"
        }
        with open(ASSETS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 资产数据已保存
    except Exception as e:
        print(f"保存资产数据失败: {e}")

def load_user_analytics_from_file():
    """从文件加载用户分析数据"""
    global USER_ACTIVITY_LOG, SEARCH_KEYWORDS_COUNT, DOCUMENT_VIEWS, ASSET_VIEWS
    
    try:
        if os.path.exists(USER_ANALYTICS_DATA_FILE):
            with open(USER_ANALYTICS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                USER_ACTIVITY_LOG = data.get('user_activity_log', [])
                SEARCH_KEYWORDS_COUNT = data.get('search_keywords_count', {})
                
                # 转换文档视图数据，处理 set 类型
                raw_document_views = data.get('document_views', {})
                DOCUMENT_VIEWS = {}
                for doc_id, view_data in raw_document_views.items():
                    DOCUMENT_VIEWS[int(doc_id)] = {
                        "count": view_data.get("count", 0),
                        "users": set(view_data.get("users", [])),
                        "last_viewed": view_data.get("last_viewed")
                    }
                
                # 转换资产视图数据，处理 set 类型
                raw_asset_views = data.get('asset_views', {})
                ASSET_VIEWS = {}
                for asset_id, view_data in raw_asset_views.items():
                    ASSET_VIEWS[int(asset_id)] = {
                        "count": view_data.get("count", 0),
                        "users": set(view_data.get("users", [])),
                        "last_viewed": view_data.get("last_viewed")
                    }
                
                # 用户分析数据加载完成
        else:
            pass  # 使用空数据
    except Exception as e:
        print(f"加载用户分析数据失败: {e}")
        # 重置为空数据
        USER_ACTIVITY_LOG = []
        SEARCH_KEYWORDS_COUNT = {}
        DOCUMENT_VIEWS = {}
        ASSET_VIEWS = {}

def save_user_analytics_to_file():
    """保存用户分析数据到文件"""
    print(f"[DEBUG] 开始保存用户分析数据到文件: {USER_ANALYTICS_DATA_FILE}")
    try:
        # 转换数据，处理 set 类型
        document_views_serializable = {}
        for doc_id, view_data in DOCUMENT_VIEWS.items():
            document_views_serializable[str(doc_id)] = {
                "count": view_data["count"],
                "users": list(view_data["users"]),
                "last_viewed": view_data["last_viewed"]
            }
        
        asset_views_serializable = {}
        for asset_id, view_data in ASSET_VIEWS.items():
            asset_views_serializable[str(asset_id)] = {
                "count": view_data["count"],
                "users": list(view_data["users"]),
                "last_viewed": view_data["last_viewed"]
            }
        
        data = {
            'user_activity_log': USER_ACTIVITY_LOG,
            'search_keywords_count': SEARCH_KEYWORDS_COUNT,
            'document_views': document_views_serializable,
            'asset_views': asset_views_serializable,
            'updated_at': datetime.utcnow().isoformat() + "Z"
        }
        
        with open(USER_ANALYTICS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[DEBUG] 用户分析数据已保存成功: {len(USER_ACTIVITY_LOG)} 条活动记录, {len(SEARCH_KEYWORDS_COUNT)} 个搜索关键词")
    except Exception as e:
        print(f"[ERROR] 保存用户分析数据失败: {e}")
        import traceback
        traceback.print_exc()

def track_user_activity(user_id: int, activity_type: str, target_id: int, target_type: str):
    """记录用户活动"""
    global USER_ACTIVITY_LOG, USERS
    
    # 根据用户ID获取真实用户名
    username = "unknown"
    for user_key, user_data in USERS.items():
        if user_data.get("id") == user_id:
            username = user_key
            break
    
    activity = {
        "user_id": user_id,
        "username": username,
        "activity_type": activity_type,  # "view_document", "view_asset", "search"
        "target_id": target_id,
        "target_type": target_type,  # "document", "asset", "search"
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    USER_ACTIVITY_LOG.append(activity)
    
    # 保持最近1000条记录
    if len(USER_ACTIVITY_LOG) > 1000:
        USER_ACTIVITY_LOG = USER_ACTIVITY_LOG[-1000:]
    
    # 记录用户活动
    
    # 每次活动都保存，确保数据持久化
    save_user_analytics_to_file()

def track_document_view(document_id: int, user_id: int = 1):
    """跟踪文档查看"""
    global DOCUMENT_VIEWS
    
    if document_id not in DOCUMENT_VIEWS:
        DOCUMENT_VIEWS[document_id] = {"count": 0, "users": set(), "last_viewed": None}
    
    DOCUMENT_VIEWS[document_id]["count"] += 1
    DOCUMENT_VIEWS[document_id]["users"].add(user_id)
    DOCUMENT_VIEWS[document_id]["last_viewed"] = datetime.utcnow().isoformat() + "Z"
    
    # 记录用户活动
    track_user_activity(user_id, "view_document", document_id, "document")
    
    # 定期保存数据 - 每次文档查看都保存，确保数据持久化
    save_user_analytics_to_file()

def track_asset_view(asset_id: int, user_id: int = 1):
    """跟踪资产查看"""
    global ASSET_VIEWS
    
    if asset_id not in ASSET_VIEWS:
        ASSET_VIEWS[asset_id] = {"count": 0, "users": set(), "last_viewed": None}
    
    ASSET_VIEWS[asset_id]["count"] += 1
    ASSET_VIEWS[asset_id]["users"].add(user_id)
    ASSET_VIEWS[asset_id]["last_viewed"] = datetime.utcnow().isoformat() + "Z"
    
    # 记录用户活动
    track_user_activity(user_id, "view_asset", asset_id, "asset")
    
    # 定期保存数据 - 每次资产查看都保存，确保数据持久化
    save_user_analytics_to_file()

def track_search_keyword(keyword: str, user_id: int = 1):
    """跟踪搜索关键词"""
    global SEARCH_KEYWORDS_COUNT
    
    keyword_lower = keyword.lower().strip()
    # 跟踪搜索关键词
    if keyword_lower:
        if keyword_lower not in SEARCH_KEYWORDS_COUNT:
            SEARCH_KEYWORDS_COUNT[keyword_lower] = {"count": 0, "users": set()}
        
        SEARCH_KEYWORDS_COUNT[keyword_lower]["count"] += 1
        SEARCH_KEYWORDS_COUNT[keyword_lower]["users"].add(user_id)
        # 更新搜索关键词统计
        
        # 记录用户活动
        track_user_activity(user_id, "search", 0, "search")
        
        # 定期保存数据 - 每次搜索都保存，确保数据持久化
        save_user_analytics_to_file()

def get_initial_assets():
    """获取初始资产数据"""
    return [
        {
            "id": 1,
            "name": "Web服务器01",
            "asset_type": "server",
            "device_model": "Dell PowerEdge R730",
            "ip_address": "192.168.1.100",
            "hostname": "web-server-01",
            "username": "admin",
            "password": "admin123",
            "network_location": "office",
            "department": "技术部",
            "status": "active",
            "notes": "主要Web服务器",
            "tags": ["production", "web"],
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        },
        {
            "id": 2,
            "name": "核心交换机", 
            "asset_type": "network",
            "device_model": "Cisco Catalyst 9300",
            "ip_address": "192.168.1.1",
            "hostname": "core-switch-01",
            "username": "admin",
            "password": "switch123",
            "network_location": "office",
            "department": "网络部",
            "status": "active",
            "notes": "核心网络交换机",
            "tags": ["network", "core"],
            "created_at": "2024-01-08T09:00:00Z",
            "updated_at": "2024-01-12T14:20:00Z"
        },
        {
            "id": 3,
            "name": "存储服务器01",
            "asset_type": "storage",
            "device_model": "Synology DS920+",
            "ip_address": "192.168.1.110",
            "hostname": "storage-01",
            "username": "admin",
            "password": "storage123",
            "network_location": "office",
            "department": "技术部",
            "status": "active",
            "notes": "主要存储设备",
            "tags": ["storage"],
            "created_at": "2024-01-05T11:00:00Z",
            "updated_at": "2024-01-10T16:45:00Z"
        },
        {
            "id": 4,
            "name": "防火墙设备",
            "asset_type": "security",
            "device_model": "Fortinet FortiGate 60F",
            "ip_address": "192.168.1.254",
            "hostname": "firewall-01",
            "username": "admin",
            "password": "firewall123",
            "network_location": "office",
            "department": "安全部",
            "status": "maintenance",
            "notes": "边界防火墙，维护中",
            "tags": ["security", "firewall"],
            "created_at": "2024-01-03T14:30:00Z",
            "updated_at": "2024-01-18T09:15:00Z"
        },
        {
            "id": 5,
            "name": "数据库服务器",
            "asset_type": "server",
            "device_model": "HP ProLiant DL380",
            "ip_address": "192.168.1.105",
            "hostname": "db-server-01",
            "username": "root",
            "password": "db123456",
            "network_location": "office",
            "department": "技术部",
            "status": "active",
            "notes": "MySQL数据库服务器",
            "tags": ["database", "mysql"],
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-20T13:25:00Z"
        }
    ]

# 从文件加载资产数据
assets_storage, next_asset_id = load_assets_from_file()
# 资产数据已加载

# 从文件加载用户分析数据
load_user_analytics_from_file()

# 如果是首次运行（没有数据文件），保存初始数据
if not os.path.exists(ASSETS_DATA_FILE):
    save_assets_to_file()

if not os.path.exists(USER_ANALYTICS_DATA_FILE):
    save_user_analytics_to_file()

@app.get("/api/v1/assets")
async def get_assets(
    query: Optional[str] = Query(None, description="搜索查询"),
    asset_type: Optional[str] = Query(None, description="资产类型"),
    status: Optional[str] = Query(None, description="资产状态"),
    department: Optional[str] = Query(None, description="部门"),
    network_location: Optional[str] = Query(None, description="网络位置"),
    page: int = Query(1, description="页码"),
    per_page: int = Query(20, description="每页数量")
):
    """获取资产列表（支持搜索和筛选）"""
    # 使用全局存储的资产数据
    global assets_storage
    
    # 应用筛选条件
    filtered_assets = assets_storage.copy()
    
    if query:
        query_lower = query.lower()
        filtered_assets = [
            asset for asset in filtered_assets
            if (query_lower in asset["name"].lower() or
                query_lower in asset.get("hostname", "").lower() or
                query_lower in asset.get("ip_address", "").lower() or
                query_lower in asset.get("department", "").lower())
        ]
    
    if asset_type:
        filtered_assets = [asset for asset in filtered_assets if asset["asset_type"] == asset_type]
    
    if status:
        filtered_assets = [asset for asset in filtered_assets if asset["status"] == status]
        
    if department:
        filtered_assets = [asset for asset in filtered_assets if asset.get("department") == department]
        
    if network_location:
        filtered_assets = [asset for asset in filtered_assets if asset.get("network_location") == network_location]
    
    # 分页（这里简化处理，直接返回所有结果）
    total_count = len(filtered_assets)
    
    # 统一返回格式，总是包含items和分页信息
    return {
        "items": filtered_assets,
        "total": total_count,
        "page": page,
        "per_page": per_page
    }

@app.get("/api/v1/assets/statistics")
async def get_asset_statistics():
    """资产统计信息"""
    global assets_storage
    
    # 基于真实资产数据计算统计
    total_count = len(assets_storage)
    
    # 按类型统计
    by_type = {}
    for asset in assets_storage:
        asset_type = asset.get("asset_type", "unknown")
        by_type[asset_type] = by_type.get(asset_type, 0) + 1
    
    # 按状态统计
    by_status = {}
    for asset in assets_storage:
        status = asset.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    
    # 按部门统计
    by_department = {}
    for asset in assets_storage:
        department = asset.get("department", "")
        if department:
            by_department[department] = by_department.get(department, 0) + 1
    
    # 计算最近新增（最近7天）
    from datetime import datetime, timedelta
    recent_date = datetime.utcnow() - timedelta(days=7)
    recent_additions = 0
    
    for asset in assets_storage:
        try:
            created_at = datetime.fromisoformat(asset.get("created_at", "").replace("Z", "+00:00"))
            if created_at > recent_date:
                recent_additions += 1
        except:
            pass
    
    return {
        "total_count": total_count,
        "by_type": by_type,
        "by_status": by_status,
        "by_environment": {},
        "by_department": by_department,
        "recent_additions": recent_additions,
        "pending_maintenance": by_status.get("maintenance", 0)
    }

# 资产管理API端点

@app.get("/api/v1/assets/{asset_id}")
async def get_asset(asset_id: int):
    """获取单个资产详情"""
    global assets_storage
    
    # 在存储中查找资产
    for asset in assets_storage:
        if asset["id"] == asset_id:
            return asset
    
    # 如果没找到，返回404错误
    raise HTTPException(status_code=404, detail=f"资产ID {asset_id} 不存在")

@app.post("/api/v1/assets")
async def create_asset(asset_data: dict, current_user: dict = Depends(require_admin_dep)):
    """创建新资产"""
    global assets_storage, next_asset_id
    
    # 创建新资产对象
    new_asset = {
        "id": next_asset_id,
        "name": asset_data.get("name", ""),
        "asset_type": asset_data.get("asset_type", "server"),
        "device_model": asset_data.get("device_model", ""),
        "ip_address": asset_data.get("ip_address", ""),
        "hostname": asset_data.get("hostname", ""),
        "username": asset_data.get("username", ""),
        "password": asset_data.get("password", ""),
        "network_location": asset_data.get("network_location", "office"),
        "department": asset_data.get("department", ""),
        "status": asset_data.get("status", "active"),
        "notes": asset_data.get("notes", ""),
        "tags": asset_data.get("tags", []),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # 添加到存储
    assets_storage.append(new_asset)
    next_asset_id += 1
    
    # 保存到文件
    save_assets_to_file()
    
    # 资产创建完成
    return new_asset

@app.put("/api/v1/assets/{asset_id}")
async def update_asset(asset_id: int, asset_data: dict, current_user: dict = Depends(require_admin_dep)):
    """更新资产信息"""
    global assets_storage
    
    # 查找要更新的资产
    for i, asset in enumerate(assets_storage):
        if asset["id"] == asset_id:
            # 更新资产信息
            updated_asset = {
                **asset,  # 保留原有信息
                **asset_data,  # 更新新信息
                "id": asset_id,  # 确保ID不被更改
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            assets_storage[i] = updated_asset
            
            # 保存到文件
            save_assets_to_file()
            
            # 资产更新完成
            return updated_asset
    
    # 如果没找到，返回404错误
    raise HTTPException(status_code=404, detail=f"资产ID {asset_id} 不存在")

@app.delete("/api/v1/assets/{asset_id}")
async def delete_asset(asset_id: int, current_user: dict = Depends(require_admin_dep)):
    """删除资产"""
    global assets_storage
    
    # 查找要删除的资产
    for i, asset in enumerate(assets_storage):
        if asset["id"] == asset_id:
            deleted_asset = assets_storage.pop(i)
            
            # 保存到文件
            save_assets_to_file()
            
            # 资产删除完成
            return {"message": f"资产 '{deleted_asset['name']}' 删除成功", "id": asset_id}
    
    # 如果没找到，返回404错误
    raise HTTPException(status_code=404, detail=f"资产ID {asset_id} 不存在")

@app.post("/api/v1/assets/{asset_id}/view-details")
async def view_asset_details(asset_id: int, current_user: dict = Depends(get_current_user_dep)):
    """查看资产详情并记录统计"""
    # 跟踪资产查看 - 使用当前用户ID
    user_id = current_user.get("id", 1) if current_user else 1
    track_asset_view(asset_id, user_id)
    
    # 记录查看统计
    # 记录资产查看
    
    # 返回统计记录结果
    return {
        "asset_id": asset_id,
        "viewed_at": datetime.utcnow().isoformat() + "Z",
        "view_count": ASSET_VIEWS.get(asset_id, {"count": 0})["count"],
        "message": "资产详情查看已记录"
    }

@app.post("/api/v1/assets/export")
async def export_assets(export_request: dict, current_user: dict = Depends(require_admin_dep)):
    """导出资产数据"""
    asset_ids = export_request.get("asset_ids", [])
    export_format = export_request.get("format", "excel")
    fields = export_request.get("fields", [])
    
    # 导出资产数据
    
    # 模拟生成导出文件
    if export_format == "excel":
        # 实际应生成Excel文件并返回
        import io
        
        # 模拟Excel内容
        excel_content = b"Fake Excel Content for Assets Export"
        
        from fastapi.responses import StreamingResponse
        
        def generate():
            yield excel_content
        
        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=assets_export.xlsx"}
        )
    else:
        # CSV格式
        csv_content = "ID,Name,Type,IP Address,Status\n"
        for asset_id in asset_ids:
            csv_content += f"{asset_id},设备{asset_id:03d},server,192.168.1.{100+asset_id},active\n"
        
        from fastapi.responses import StreamingResponse
        import io
        
        def generate():
            yield csv_content.encode('utf-8')
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=assets_export.csv"}
        )

@app.post("/api/v1/assets/extract")
async def extract_assets_from_document(extract_request: dict, current_user: dict = Depends(require_admin_dep)):
    """从文档提取资产信息"""
    global assets_storage, next_asset_id
    
    document_id = extract_request.get("document_id")
    auto_merge = extract_request.get("auto_merge", True)
    merge_threshold = extract_request.get("merge_threshold", 80)
    
    # 从文档提取资产
    
    # 模拟提取过程
    import time
    time.sleep(1)  # 模拟处理时间
    
    # 模拟提取的资产数据模板
    extract_templates = [
        {
            "name": "提取的服务器01",
            "asset_type": "server",
            "device_model": "Dell PowerEdge R740",
            "ip_address": "192.168.1.201",
            "hostname": "extracted-server-01",
            "username": "root",
            "password": "extract123",
            "network_location": "office",
            "department": "技术部",
            "status": "active",
            "notes": "从文档中提取的服务器信息",
            "tags": ["extracted", "server"],
            "confidence_score": 85,
            "is_merged": False
        },
        {
            "name": "提取的网络设备01",
            "asset_type": "network",
            "device_model": "Cisco Catalyst 2960",
            "ip_address": "192.168.1.202",
            "hostname": "switch-extracted-01",
            "username": "admin",
            "password": "switch456",
            "network_location": "office",
            "department": "网络部",
            "status": "active",
            "notes": "从文档中提取的网络设备",
            "tags": ["extracted", "network"],
            "confidence_score": 92,
            "is_merged": False
        }
    ]
    
    extracted_assets = []
    created_count = 0
    
    # 实际创建资产到存储中
    for template in extract_templates:
        new_asset = {
            "id": next_asset_id,
            "name": template["name"],
            "asset_type": template["asset_type"],
            "device_model": template["device_model"],
            "ip_address": template["ip_address"],
            "hostname": template["hostname"],
            "username": template["username"],
            "password": template["password"],
            "network_location": template["network_location"],
            "department": template["department"],
            "status": template["status"],
            "notes": template["notes"],
            "tags": template["tags"],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "confidence_score": template["confidence_score"],
            "is_merged": template["is_merged"]
        }
        
        # 添加到存储
        assets_storage.append(new_asset)
        extracted_assets.append(new_asset)
        next_asset_id += 1
        created_count += 1
        
        # 资产提取创建完成
    
    # 保存到文件
    if created_count > 0:
        save_assets_to_file()
    
    return {
        "extracted_count": len(extract_templates),
        "merged_count": 0,  # 目前不实现合并逻辑
        "assets": extracted_assets,
        "errors": []
    }

@app.get("/api/v1/categories")
async def get_categories():
    """获取分类列表"""
    return [
        {
            "id": 1,
            "name": "技术文档",
            "description": "技术相关文档",
            "color": "#2563eb",
            "icon": "DocumentTextOutline",
            "sort_order": 1,
            "is_active": True
        },
        {
            "id": 2,
            "name": "操作手册", 
            "description": "操作流程和规范",
            "color": "#dc2626",
            "icon": "BookOutline",
            "sort_order": 2,
            "is_active": True
        }
    ]

# 用户管理API端点 - 仅管理员
@app.get("/api/v1/settings/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_admin_dep)):
    """获取所有用户（仅管理员）"""
    global USERS
    
    users_list = []
    for username, user_data in USERS.items():
        users_list.append({
            "id": user_data["id"],
            "username": username,
            "email": user_data["email"],
            "full_name": user_data.get("full_name"),
            "department": user_data.get("department"),
            "position": user_data.get("position"),
            "phone": user_data.get("phone"),
            "is_active": user_data.get("is_active", True),
            "is_superuser": user_data.get("is_superuser", False),
            "created_at": user_data.get("created_at", datetime.utcnow().isoformat() + "Z")
        })
    
    return users_list

@app.post("/api/v1/settings/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_admin_dep)):
    """创建新用户（仅管理员）"""
    global USERS, next_user_id
    
    # 检查用户名是否已存在
    if user_data.username in USERS:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    for existing_user in USERS.values():
        if existing_user.get("email") == user_data.email:
            raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    new_user = {
        "id": next_user_id,
        "username": user_data.username,
        "password": user_data.password,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "department": user_data.department,
        "position": user_data.position,
        "phone": user_data.phone,
        "is_active": True,
        "is_superuser": user_data.is_superuser,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    USERS[user_data.username] = new_user
    next_user_id += 1
    
    # 保存到文件
    save_users_to_file()
    
    # 用户创建完成
    
    return {
        "id": new_user["id"],
        "username": new_user["username"],
        "email": new_user["email"],
        "full_name": new_user.get("full_name"),
        "department": new_user.get("department"),
        "position": new_user.get("position"),
        "phone": new_user.get("phone"),
        "is_active": new_user.get("is_active", True),
        "is_superuser": new_user.get("is_superuser", False),
        "created_at": new_user.get("created_at")
    }

@app.put("/api/v1/settings/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, current_user: dict = Depends(require_admin_dep)):
    """更新用户信息（仅管理员）"""
    global USERS
    
    # 查找用户
    target_user = None
    target_username = None
    for username, user_info in USERS.items():
        if user_info.get("id") == user_id:
            target_user = user_info
            target_username = username
            break
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    if user_data.email is not None:
        target_user["email"] = user_data.email
    if user_data.full_name is not None:
        target_user["full_name"] = user_data.full_name
    if user_data.department is not None:
        target_user["department"] = user_data.department
    if user_data.position is not None:
        target_user["position"] = user_data.position
    if user_data.phone is not None:
        target_user["phone"] = user_data.phone
    if user_data.is_active is not None:
        target_user["is_active"] = user_data.is_active
    if user_data.is_superuser is not None:
        target_user["is_superuser"] = user_data.is_superuser
    if user_data.password is not None and user_data.password.strip():
        target_user["password"] = user_data.password  # 新增密码修改功能
        print(f"用户 {target_username} 的密码已更新")
    
    target_user["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    # 保存到文件
    save_users_to_file()
    
    # 用户更新完成
    
    return {
        "id": target_user["id"],
        "username": target_username,
        "email": target_user["email"],
        "full_name": target_user.get("full_name"),
        "department": target_user.get("department"),
        "position": target_user.get("position"),
        "phone": target_user.get("phone"),
        "is_active": target_user.get("is_active", True),
        "is_superuser": target_user.get("is_superuser", False),
        "created_at": target_user.get("created_at")
    }

@app.delete("/api/v1/settings/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin_dep)):
    """删除用户（仅管理员）"""
    global USERS
    
    # 查找用户
    target_username = None
    for username, user_info in USERS.items():
        if user_info.get("id") == user_id:
            target_username = username
            break
    
    if not target_username:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不允许删除管理员用户
    if USERS[target_username].get("is_superuser"):
        raise HTTPException(status_code=400, detail="不能删除管理员用户")
    
    # 删除用户
    del USERS[target_username]
    
    # 保存到文件
    save_users_to_file()
    
    # 用户删除完成
    
    return {"message": f"用户 {target_username} 删除成功"}

# AI智能分析API端点 - 仅管理员
@app.get("/api/v1/analytics/ai-analysis")
async def get_ai_analysis(current_user: dict = Depends(require_admin_dep), db: Session = Depends(get_db)):
    """获取AI智能分析和运维建议"""
    global USER_ACTIVITY_LOG, DOCUMENT_VIEWS, ASSET_VIEWS, SEARCH_KEYWORDS_COUNT, assets_storage
    
    # 分析用户行为模式
    analysis_results = {
        "analysis_time": datetime.utcnow().isoformat() + "Z",
        "insights": [],
        "recommendations": [],
        "risk_alerts": [],
        "performance_metrics": {}
    }
    
    try:
        # 分析文档访问模式
        if DOCUMENT_VIEWS:
            most_viewed_doc = max(DOCUMENT_VIEWS.items(), key=lambda x: x[1]["count"])
            doc_id = most_viewed_doc[0]
            doc_count = most_viewed_doc[1]['count']
            
            # 获取真实的文档名称
            doc_name = f"文档 ID {doc_id}"  # 默认名称
            if db:
                try:
                    document_obj = crud.document.get(db=db, id=doc_id)
                    if document_obj:
                        doc_name = f'"{document_obj.title}"'
                except Exception as e:
                    print(f"获取文档{doc_id}名称失败: {e}")
            
            analysis_results["insights"].append({
                "type": "document_access",
                "title": "文档访问热点分析",
                "content": f"文档 {doc_name} 是最受关注的文档，被访问了 {doc_count} 次。",
                "priority": "info"
            })
            
            # 检查是否有文档长时间未被访问
            unaccessed_docs = len([doc_id for doc_id, data in DOCUMENT_VIEWS.items() 
                                 if data["count"] == 0])
            if unaccessed_docs > 0:
                analysis_results["recommendations"].append({
                    "type": "content_optimization",
                    "title": "优化文档内容",
                    "content": f"发现 {unaccessed_docs} 个文档未被访问，建议检查内容相关性和搜索标签。",
                    "action": "审查未使用文档"
                })
        
        # 分析资产管理模式
        if ASSET_VIEWS:
            most_viewed_asset = max(ASSET_VIEWS.items(), key=lambda x: x[1]["count"])
            asset_id = most_viewed_asset[0]
            asset_count = most_viewed_asset[1]['count']
            
            # 获取真实的资产名称
            asset_name = f"资产 ID {asset_id}"  # 默认名称
            try:
                for asset in assets_storage:
                    if asset["id"] == asset_id:
                        asset_name = f'"{asset["name"]}"'
                        break
            except Exception as e:
                print(f"获取资产{asset_id}名称失败: {e}")
            
            analysis_results["insights"].append({
                "type": "asset_monitoring",
                "title": "资产关注度分析",
                "content": f"资产 {asset_name} 是最受关注的设备，被查看了 {asset_count} 次，可能需要重点维护。",
                "priority": "warning"
            })
        
        # 分析资产状态分布
        if assets_storage:
            maintenance_count = len([asset for asset in assets_storage if asset.get('status') == 'maintenance'])
            total_assets = len(assets_storage)
            maintenance_ratio = maintenance_count / total_assets if total_assets > 0 else 0
            
            if maintenance_ratio > 0.2:  # 如果超过20%的设备在维护中
                analysis_results["risk_alerts"].append({
                    "type": "high_maintenance_ratio",
                    "title": "设备维护率偏高",
                    "content": f"当前有 {maintenance_count}/{total_assets} ({maintenance_ratio:.1%}) 设备处于维护状态，建议制定预防性维护计划。",
                    "severity": "high",
                    "recommended_action": "制定预防性维护策略"
                })
        
        # 分析搜索关键词趋势
        if SEARCH_KEYWORDS_COUNT:
            top_keywords = sorted(SEARCH_KEYWORDS_COUNT.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
            
            security_related = [kw for kw, data in top_keywords if any(term in kw.lower() 
                               for term in ['安全', '防火墙', '漏洞', '攻击', 'security', 'firewall'])]
            
            if security_related:
                analysis_results["insights"].append({
                    "type": "security_focus",
                    "title": "安全关注度分析",
                    "content": f"用户频繁搜索安全相关内容: {', '.join([kw[0] for kw in security_related])}，表明安全运维需求较高。",
                    "priority": "high"
                })
                
                analysis_results["recommendations"].append({
                    "type": "security_enhancement",
                    "title": "加强安全运维",
                    "content": "建议增加安全相关文档和培训资料，建立安全事件响应流程。",
                    "action": "加强安全文档建设"
                })
        
        # 生成运维建议
        analysis_results["recommendations"].extend([
            {
                "type": "documentation",
                "title": "完善文档体系",
                "content": "基于用户搜索行为，建议补充常用运维场景的操作手册和故障处理指南。",
                "action": "制作运维操作指南"
            },
            {
                "type": "monitoring",
                "title": "增强监控能力",
                "content": "建议对高频访问的资产建立更详细的监控指标和告警规则。",
                "action": "建立增强监控体系"
            },
            {
                "type": "training",
                "title": "团队技能提升",
                "content": "根据搜索关键词分析，建议针对热点技术领域开展专项培训。",
                "action": "组织技术专项培训"
            }
        ])
        
        # 性能指标
        analysis_results["performance_metrics"] = {
            "document_utilization": len(DOCUMENT_VIEWS) / max(1, total_documents) if 'total_documents' in locals() else 0,
            "asset_monitoring_coverage": len(ASSET_VIEWS) / max(1, len(assets_storage)) if assets_storage else 0,
            "search_diversity": len(SEARCH_KEYWORDS_COUNT),
            "user_engagement": len(USER_ACTIVITY_LOG)
        }
        
    except Exception as e:
        analysis_results["insights"].append({
            "type": "analysis_error",
            "title": "分析过程异常",
            "content": f"部分分析功能遇到问题: {str(e)}，请检查数据完整性。",
            "priority": "warning"
        })
    
    return analysis_results

# 清空用户活动统计数据API - 仅管理员
@app.post("/api/v1/analytics/clear-stats")
async def clear_analytics_stats(current_user: dict = Depends(require_admin_dep)):
    """清空所有用户活动统计数据"""
    global USER_ACTIVITY_LOG, SEARCH_KEYWORDS_COUNT, DOCUMENT_VIEWS, ASSET_VIEWS
    
    try:
        # 备份当前数据（如果需要的话）
        backup_data = {
            'user_activity_log_count': len(USER_ACTIVITY_LOG),
            'search_keywords_count': len(SEARCH_KEYWORDS_COUNT),
            'document_views_count': len(DOCUMENT_VIEWS),
            'asset_views_count': len(ASSET_VIEWS),
            'cleared_at': datetime.utcnow().isoformat() + "Z",
            'cleared_by': current_user.get("username", "unknown")
        }
        
        # 在清空用户活动统计数据
        
        # 清空所有统计数据
        USER_ACTIVITY_LOG = []
        SEARCH_KEYWORDS_COUNT = {}
        DOCUMENT_VIEWS = {}
        ASSET_VIEWS = {}
        
        # 保存空数据到文件
        save_user_analytics_to_file()
        
        # 数据清空完成
        
        return {
            "success": True,
            "message": "用户活动统计数据已清空",
            "backup_info": backup_data
        }
    except Exception as e:
        print(f"清空用户活动统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空统计数据失败: {str(e)}")


if __name__ == "__main__":
    try:
        print("润扬大桥运维文档管理系统 - 启动后端服务")
        print("访问地址: http://127.0.0.1:8002")
        print("API文档: http://127.0.0.1:8002/docs")
        print("默认用户: admin / admin123")
        print("按 Ctrl+C 停止服务")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8002,
            reload=False,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n用户中断服务，正在优雅关闭...")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("后端服务已停止")