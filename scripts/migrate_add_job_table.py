"""
데이터 수집 작업 테이블 추가 마이그레이션
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate():
    """data_collection_jobs 테이블 추가"""
    # DB URL 생성
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
    
    engine = create_engine(db_url)
    
    logger.info(f"데이터베이스 연결: {db_url}")
    
    # 테이블 존재 여부 확인
    inspector = inspect(engine)
    if "data_collection_jobs" in inspector.get_table_names():
        logger.info("✓ data_collection_jobs 테이블이 이미 존재합니다")
        return
    
    # PostgreSQL / SQLite 구분
    is_postgres = "postgresql" in db_url
    
    if is_postgres:
        create_table_sql = """
        CREATE TABLE data_collection_jobs (
            id SERIAL PRIMARY KEY,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            current_symbol VARCHAR(100),
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            logs JSON,
            error TEXT,
            count INTEGER NOT NULL,
            days INTEGER NOT NULL,
            strategy VARCHAR(20) NOT NULL,
            volume_ratio FLOAT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        """
    else:
        create_table_sql = """
        CREATE TABLE data_collection_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            current_symbol VARCHAR(100),
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            logs TEXT,
            error TEXT,
            count INTEGER NOT NULL,
            days INTEGER NOT NULL,
            strategy VARCHAR(20) NOT NULL,
            volume_ratio REAL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
        logger.info("✓ data_collection_jobs 테이블 생성 완료")
    
    logger.info("✅ 마이그레이션 완료!")


if __name__ == "__main__":
    migrate()
