import os
from fastapi import FastAPI
from app.api import token
from app.api import worklog

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="数据中心工作日志查询接口",
    description="本系统用于查询数据中心的工作日志",
    version="1.0.0",
)

app.include_router(token.router)
app.include_router(worklog.router)

# 允许前端跨域请求
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],      # GET, POST, OPTIONS 等
    allow_headers=["*"],      # 自定义 Header
)