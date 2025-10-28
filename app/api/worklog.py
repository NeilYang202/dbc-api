from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.db.models import WorkLogModel, SystemUserModel
from app.api.token import verify_jwt_token  # 你的 JWT 验证依赖
from datetime import timedelta

router = APIRouter(
    prefix="/api",
    tags=["工作日志接口"]
)


@router.get("/worklogs", summary="查询指定时间段内的工作日志（可按用户名过滤）")
def get_work_logs(
    start_time: datetime = Query(None, description="工作开始时间，格式如 2025-10-01 00:00:00"),
    end_time: datetime = Query(None, description="工作结束时间，格式如 2025-10-24 23:59:59"),

    created_start_time: Optional[datetime] = Query(None, description="日志创建开始时间"),
    created_end_time: Optional[datetime] = Query(None, description="日志创建结束时间"),

    username: Optional[str] = Query(None, description="可选，用户名（不区分大小写）"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)
):
    """
    根据时间段查询工作日志（需携带有效 JWT Token）。
    如果提供 username，则只查该用户，否则查所有用户。
    """
    if (start_time and not end_time) or (end_time and not start_time):
        raise HTTPException(status_code=400, detail="工作时间段必须成对提供（start_time 和 end_time）")

    if (created_start_time and not created_end_time) or (created_end_time and not created_start_time):
        raise HTTPException(status_code=400, detail="创建时间段必须成对提供（created_start_time 和 created_end_time）")

    # 2️⃣ 至少要提供一组
    if not ((start_time and end_time) or (created_start_time and created_end_time)):
        raise HTTPException(status_code=400, detail="必须至少选择一组时间条件（工作时间段 或 创建时间段）")
    # --- 基础查询：联表 system_users 获取 username ---
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
            WorkLogModel.created_at,
        )
        .join(SystemUserModel, WorkLogModel.user_id == SystemUserModel.user_id, isouter=True)
    )    

    # ---- 按工作时间筛选（北京时间）
    if start_time and end_time:
        query = query.filter(
            WorkLogModel.start_time >= start_time,
            WorkLogModel.end_time <= end_time
        )    

    # ---- 按日志创建时间筛选（用户输入北京时间 → 转换为 GMT 存储）
    if created_start_time and created_end_time:
        query = query.filter(
            WorkLogModel.created_at >= created_start_time - timedelta(hours=8),
            WorkLogModel.created_at <= created_end_time - timedelta(hours=8)
        )    

    # ---- 按用户名筛选 ---
    if username:
        query = query.filter(SystemUserModel.username.ilike(f"%{username}%"))

    results = query.order_by(WorkLogModel.start_time.desc()).all()

    if not results:
        return {"message": "没有找到符合条件的工作日志"}

    # --- 格式化输出 ---
    logs = []
    for r in results:
        # 转换时间格式
        start_time_str = r.start_time.strftime("%Y-%m-%d %H:%M:%S") if r.start_time else None
        end_time_str = r.end_time.strftime("%Y-%m-%d %H:%M:%S") if r.end_time else None    

        # created_at 是 GMT 时间，加 8 小时
        created_at_local = None
        if r.created_at:
            created_at_local = (r.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")    

        logs.append({
            "log_id": str(r.log_id),
            "user_id": str(r.user_id) if r.user_id else None,
            "username": r.username,
            "details": r.details,
            "audit_status": r.audit_status,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "work_time": r.work_time,
            "remark": r.remark,
            "created_at": created_at_local,
        })    

    return {"count": len(logs), "data": logs}
