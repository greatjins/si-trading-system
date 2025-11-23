"""
공통 의존성
"""
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from api.auth.security import get_current_active_user, require_role
from api.auth.models import User

# 데이터베이스 설정
DATABASE_URL = "sqlite:///./data/hts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(current_user: User = Depends(get_current_active_user)) -> User:
    """현재 사용자 가져오기"""
    return current_user


# 인증된 사용자 필요
RequireAuth = Depends(get_current_active_user)

# 트레이더 역할 필요
RequireTrader = Depends(require_role("trader"))

# 관리자 역할 필요
RequireAdmin = Depends(require_role("admin"))
