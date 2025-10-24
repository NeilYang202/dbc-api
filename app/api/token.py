from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import os

# --- JWT 相关的库 ---
from jose import JWTError, jwt
# 生产环境应该使用安全的密码哈希库，这里仅使用 os.getenv 模拟用户数据

router = APIRouter(
    tags=["认证与授权接口 (JWT)"],
    prefix="/api",
)

# ==================== 配置项 ====================

# JWT 签名密钥：生产环境必须使用强随机密钥，并存储在安全的地方
# 警告：这里使用一个简单的环境变量默认值，生产环境必须更换！
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-very-strong-secret-key-12345")
ALGORITHM = "HS256" # 使用 HMAC SHA-256 算法

# Token 有效期（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 30 
# 这里为了演示 JWT，我们不再需要 TOKENS 字典

# 警告：这是极不安全的明文存储。生产环境必须使用哈希。
USERNAME = os.environ.get('AUTH_USERNAME', 'admin') 
PASSWORD = os.environ.get('AUTH_PASSWORD', 'password123')

# 模拟用户数据存储 (生产环境应替换为数据库查询和哈希密码)
USER_CREDENTIALS: Dict[str, str] = {
    USERNAME: PASSWORD,
}

# ==================== JWT 核心函数 ====================

def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT (access token)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 默认过期时间
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    # 将过期时间 (exp) 加入 payload
    to_encode.update({"exp": expire})
    
    # 使用密钥和算法签名，生成 token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==================== Token 验证（HTTPBearer） =================
security = HTTPBearer()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI 依赖项：验证传入的 Bearer token，并返回 payload (包含用户信息)。
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 Authorization header")

    token = credentials.credentials
    
    try:
        # 解码并验证 token。如果签名不匹配或已过期，将抛出 JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 检查 payload 中是否有关键信息，例如 sub (subject)
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Token 缺少 'sub' 信息")
            
        # token 有效且未过期
        return payload
        
    except JWTError:
        # 签名无效、Token过期等所有 JWT 错误都捕获
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ================= Token 获取接口 (使用 Form Data) =================
@router.post("/token", summary="获取访问 token (JWT)")
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    接收用户名和密码 (通过 form data)，验证成功后颁发 JWT。
    """
    username = form_data.username
    password = form_data.password
    
    # ❌ 警告：此处是明文密码验证，生产环境必须替换为哈希验证
    if username not in USER_CREDENTIALS or USER_CREDENTIALS[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 验证成功，创建 Token
    # JWT 的 payload 中通常包含用户标识符 (sub: subject)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": username}, # sub: subject，通常放用户唯一标识
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, # 以秒为单位返回有效期
    }