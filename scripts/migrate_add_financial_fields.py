"""
StockMasterModel에 재무 정보 필드 추가 마이그레이션
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate():
    """재무 정보 필드 추가"""
    
    # 데이터베이스 연결
    db_type = config.get("database.type", "sqlite")
    if db_type == "sqlite":
        db_path = config.get("database.path", "data/hts.db")
        db_url = f"sqlite:///{db_path}"
    else:
        host = config.get("database.host", "localhost")
        port = config.get("database.port", 5432)
        database = config.get("database.database", "hts")
        username = config.get("database.user", "hts_user")
        password = config.get("database.password", "")
        db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
    
    logger.info(f"데이터베이스 연결: {db_type}")
    engine = create_engine(db_url, echo=True)
    
    # 추가할 컬럼 목록
    new_columns = [
        ("market_cap", "FLOAT"),
        ("shares", "FLOAT"),
        ("per", "FLOAT"),
        ("pbr", "FLOAT"),
        ("eps", "FLOAT"),
        ("bps", "FLOAT"),
        ("roe", "FLOAT"),
        ("roa", "FLOAT"),
        ("dividend_yield", "FLOAT"),
        ("foreign_ratio", "FLOAT"),
    ]
    
    with engine.connect() as conn:
        # 테이블 존재 확인 (DB별 쿼리)
        if db_type == "sqlite":
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_master'"
            ))
        else:  # PostgreSQL
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='stock_master'"
            ))
        
        if not result.fetchone():
            logger.info("stock_master 테이블이 없습니다. 새로 생성됩니다.")
            return
        
        # 기존 컬럼 확인 (DB별 쿼리)
        if db_type == "sqlite":
            result = conn.execute(text("PRAGMA table_info(stock_master)"))
            existing_columns = {row[1] for row in result.fetchall()}
        else:  # PostgreSQL
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='stock_master'"
            ))
            existing_columns = {row[0] for row in result.fetchall()}
        
        logger.info(f"기존 컬럼: {existing_columns}")
        
        # 새 컬럼 추가
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE stock_master ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"✓ 컬럼 추가: {col_name} ({col_type})")
                except Exception as e:
                    logger.error(f"✗ 컬럼 추가 실패: {col_name} - {e}")
            else:
                logger.info(f"⊙ 컬럼 이미 존재: {col_name}")
        
        logger.info("마이그레이션 완료!")


if __name__ == "__main__":
    migrate()
