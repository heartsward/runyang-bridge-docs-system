from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "运维文档管理系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./yunwei_docs_clean.db"
    TEST_DATABASE_URL: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,txt,md,xls,xlsx,csv,jpg,jpeg,png"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # Elasticsearch配置
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()