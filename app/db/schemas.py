from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import Field

# 系统用户 Schemas (SystemUser)
class SystemUserBase(BaseModel):
    user_id: Optional[UUID] = None
    username: str = Field(..., max_length=50)
    is_enabled: bool = Field(False, description="用户是否启用，默认禁用")
    model_config = {
        "from_attributes": True
    }

# WorkLogBase (只包含 WorkLog 表自身的字段)
class WorkLogBase(BaseModel):
    log_id: Optional[UUID] = None
    user_id: Optional[UUID] = None # 关联 SystemUser 的外键
    details: Optional[str]  = None
    audit_status: Optional[int] = 0 
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    work_time: Optional[int] = Field(None, description="工作时长，单位分钟 (向上取整)") 
    remark: Optional[str] = None
    # 💥 不包含 created_at 

    model_config = {
        "from_attributes": True
    }