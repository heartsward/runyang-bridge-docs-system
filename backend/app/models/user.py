from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(255))
    department = Column(String(100))
    position = Column(String(100))
    phone = Column(String(20))
    # 32.2：MCP 调用验证码（每普通用户随机一码）——
    # 普通用户：持有个人码；管理员：NULL（用 system_config 里的统一管理员码）。
    # 升级→清空、降级→生成（settings 端点钩子），也可随时"重新随机"。
    mcp_token = Column(String(64), unique=True, index=True, nullable=True,
                       comment="MCP 调用验证码（普通用户个人码；管理员为空用统一码）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系 - 使用延迟加载避免循环导入问题
    documents = relationship("Document", back_populates="owner", lazy="dynamic")
    categories = relationship("Category", back_populates="creator", lazy="dynamic")
    search_logs = relationship("SearchLog", back_populates="user", lazy="dynamic")
    ai_configs = relationship("AIUserConfig", back_populates="user", lazy="dynamic")