"""
공통 의존성
"""
import os
import yaml
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from api.auth.security import get_current_active_user, require_role
from api.auth.models import User

# Windows 인코딩 문제 해결
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 설정 파일 로드
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
db_config = config.get("database", {})

# 데이터베이스 URL 생성
if db_config.get("type") == "postgresql":
    # pg8000 드라이버 사용 (Windows 한글 경로 문제 해결)
    DATABASE_URL = (
        f"postgresql+pg8000://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    # PostgreSQL 연결 설정
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # 연결 유효성 체크
        pool_recycle=3600,   # 1시간마다 연결 재생성
    )
else:
    # SQLite (fallback)
    DATABASE_URL = f"sqlite:///./{db_config.get('path', 'data/hts.db')}"
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
