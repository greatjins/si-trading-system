"""
계좌 관리 데이터베이스 초기화
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from data.account_models import Base

# 데이터베이스 URL
DATABASE_URL = "sqlite:///./data/hts.db"

# 엔진 생성
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 테이블 생성
Base.metadata.create_all(bind=engine)

print("✅ 계좌 관리 테이블 생성 완료!")
print(f"   - 데이터베이스: {DATABASE_URL}")
print(f"   - 테이블: trading_accounts")
