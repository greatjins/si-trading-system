"""
인증 관련 API
"""
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta

from api.schemas import (
    LoginRequest, TokenResponse, UserCreateRequest, UserResponse, MessageResponse
)
from api.auth.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    get_current_user, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.auth.models import UserRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 사용자 저장소
user_repo = UserRepository()


@router.post("/register", response_model=UserResponse)
async def register(request: UserCreateRequest):
    """
    사용자 등록
    
    Args:
        request: 사용자 생성 요청
        
    Returns:
        생성된 사용자 정보
    """
    try:
        # 중복 확인
        if user_repo.get_user_by_username(request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if user_repo.get_user_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(request.password)
        
        # 사용자 생성
        user = user_repo.create_user(
            username=request.username,
            email=request.email,
            hashed_password=hashed_password,
            full_name=request.full_name
        )
        
        logger.info(f"User registered: {user.username}")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    로그인
    
    Args:
        request: 로그인 요청
        
    Returns:
        액세스 토큰 및 리프레시 토큰
    """
    try:
        # 사용자 조회
        user = user_repo.get_user_by_username(request.username)
        
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        logger.info(f"User logged in: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """
    현재 사용자 정보 조회
    
    Args:
        current_user: 현재 사용자 (의존성)
        
    Returns:
        사용자 정보
    """
    try:
        user = user_repo.get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    토큰 갱신
    
    Args:
        refresh_token: 리프레시 토큰
        
    Returns:
        새로운 액세스 토큰
    """
    try:
        from api.auth.security import decode_token
        
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        # 사용자 조회
        user = user_repo.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        # 새 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username, "user_id": user_id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    로그아웃
    
    Args:
        current_user: 현재 사용자 (의존성)
        
    Returns:
        로그아웃 결과
    """
    try:
        from broker.connection_pool import connection_pool
        from api.dependencies import get_db
        from api.repositories.account_repository import AccountRepository
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # DB 세션 생성
        engine = create_engine("sqlite:///data/hts.db")
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 사용자의 모든 계좌 조회
            repo = AccountRepository(db)
            accounts = repo.get_accounts(current_user["user_id"])
            
            # 각 계좌의 연결 종료
            for account in accounts:
                try:
                    credentials = repo.get_account_credentials(account.id, current_user["user_id"])
                    if credentials and credentials["account_number"]:
                        await connection_pool.close_adapter(
                            broker=account.broker.value,
                            account_id=credentials["account_number"]
                        )
                        logger.info(f"Closed connection for account: {credentials['account_number']}")
                except Exception as e:
                    logger.warning(f"Failed to close connection for account {account.id}: {e}")
        finally:
            db.close()
        
        # TODO: 토큰 블랙리스트 처리 (Redis)
        logger.info(f"User logged out: {current_user['username']}")
        
        return MessageResponse(
            message="Successfully logged out",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # 로그아웃은 실패해도 성공으로 처리
        return MessageResponse(
            message="Successfully logged out",
            success=True
        )
