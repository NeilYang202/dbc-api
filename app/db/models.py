# 数据库模型
from sqlalchemy import Column, String
from app.db.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TEXT, UUID
from sqlalchemy import ForeignKey, DateTime, func, Boolean, Integer
from uuid_extensions import uuid7

# -------- 用户表 -------- #
class SystemUserModel(Base):
    __tablename__ = "system_users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100))
    name = Column(String(100))
    phonenumber = Column(String(15))
    password = Column(String, nullable=False)
    
    # 修正1：移除 role_id 上不合理的 default=uuid7 (外键不应默认为随机ID)
    role_id = Column(UUID(as_uuid=True), 
                     ForeignKey("system_roles.role_id", ondelete="SET NULL"), 
                     nullable=True)
                     
    # 修正2：合并 dept_id 的两次定义，并移除第二次定义中的 ForeignKey
    # 保留 default=uuid7 是因为它是非外键部分的属性，但如果希望用户必须指定部门，应移除 default
    dept_id = Column(UUID(as_uuid=True), 
                     ForeignKey("system_deptments.dept_id", ondelete="SET NULL"), 
                     nullable=True) 
                     
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # 修正3：is_enabled 默认值改为 'true'，新用户通常是启用的
    is_enabled = Column(Boolean, nullable=False, server_default="true") 

# -------- 工作日志表 -------- #
class WorkLogModel(Base):
    __tablename__ = "work_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid7)
    user_id = Column(UUID(as_uuid=True), ForeignKey("system_users.user_id", ondelete="SET NULL"), nullable=True)
    details = Column(String(500), nullable=False)
    audit_status = Column(Integer, server_default="0")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    work_time = Column(Integer, nullable=False)  # 工作时长，单位小时
    remark = Column(TEXT)
    created_at = Column(DateTime, server_default=func.now())

    # 关系：日志属于一个用户
    user = relationship("SystemUserModel")