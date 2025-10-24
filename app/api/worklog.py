from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.db.models import WorkLogModel, SystemUserModel
from app.api.token import verify_jwt_token  # 你的 JWT 验证依赖

router = APIRouter(
    prefix="/api",
    tags=["工作日志接口"]
)


@router.get("/worklogs", summary="查询指定时间段内的工作日志（可按用户名过滤）")
def get_work_logs(
    start_time: datetime = Query(..., description="开始时间，格式如 2025-10-01T00:00:00"),
    end_time: datetime = Query(..., description="结束时间，格式如 2025-10-24T23:59:59"),
    username: Optional[str] = Query(None, description="可选，用户名（不区分大小写）"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """
    根据时间段查询工作日志（需携带有效 JWT Token）。
    如果提供 username，则只查该用户，否则查所有用户。
    """

    # --- 基础查询：联表 system_users 获取 username ---
    query = (
        db.query(
            WorkLogModel.log_id,
            WorkLogModel.user_id,
            SystemUserModel.username,
            WorkLogModel.details,
            WorkLogModel.audit_status,
            WorkLogModel.start_time,
            WorkLogModel.end_time,
            WorkLogModel.work_time,
            WorkLogModel.remark,
        )
        .join(SystemUserModel, WorkLogModel.user_id == SystemUserModel.user_id, isouter=True)
        .filter(WorkLogModel.start_time >= start_time)
        .filter(WorkLogModel.end_time <= end_time)
    )

    # --- 按用户名筛选 ---
    if username:
        query = query.filter(SystemUserModel.username.ilike(f"%{username}%"))

    results = query.order_by(WorkLogModel.start_time.desc()).all()

    if not results:
        return {"message": "没有找到符合条件的工作日志"}

    # --- 格式化输出 ---
    logs = []
    for r in results:
        logs.append({
            "log_id": str(r.log_id),
            "user_id": str(r.user_id) if r.user_id else None,
            "username": r.username,
            "details": r.details,
            "audit_status": r.audit_status,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "work_time": r.work_time,
            "remark": r.remark,
        })

    return {"count": len(logs), "data": logs}
