"""
인증 및 보안 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.logger import setup_logger

logger = setup_logger(__name__)

# 설정
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: 환경변수로 관리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 토큰
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
        
    Returns:
        검증 결과
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 평문 비밀번호
        
    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간
        
    Returns:
        JWT 토큰
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    리프레시 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        
    Returns:
        JWT 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    토큰 디코딩
    
    Args:
        token: JWT 토큰
        
    Returns:
        토큰 페이로드
        
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    현재 사용자 조회 (의존성)
    
    Args:
        credentials: HTTP Bearer 토큰
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException: 인증 실패
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: 데이터베이스에서 사용자 조회
    return {
        "username": username,
        "user_id": payload.get("user_id"),
        "role": payload.get("role", "user")
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    활성 사용자 조회 (의존성)
    
    Args:
        current_user: 현재 사용자
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException: 비활성 사용자
    """
    # TODO: 사용자 활성 상태 확인
    return current_user


def require_role(required_role: str):
    """
    역할 기반 접근 제어 데코레이터
    
    Args:
        required_role: 필요한 역할
        
    Returns:
        의존성 함수
    """
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        user_role = current_user.get("role", "user")
        
        # 역할 계층: admin > trader > user
        role_hierarchy = {"admin": 3, "trader": 2, "user": 1}
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker
