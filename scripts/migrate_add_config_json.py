"""
StrategyBuilderModel에 config_json 필드 추가 마이그레이션
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def migrate():
    """config_json 필드 추가"""
    
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
    engine = create_engine(db_url, echo=False)
    
    is_postgres = "postgresql" in db_url
    
    with engine.connect() as conn:
        # 테이블 존재 확인
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'strategy_builder' not in existing_tables:
            logger.info("strategy_builder 테이블이 없습니다. 새로 생성됩니다.")
            # 테이블이 없으면 모델에서 생성
            from data.models import Base, StrategyBuilderModel
            Base.metadata.create_all(engine, tables=[StrategyBuilderModel.__table__])
            logger.info("✓ strategy_builder 테이블 생성 완료")
            return
        
        # 기존 컬럼 확인
        columns = inspector.get_columns('strategy_builder')
        existing_columns = {col['name'] for col in columns}
        
        logger.info(f"기존 컬럼: {existing_columns}")
        
        # config_json 컬럼 추가
        if 'config_json' not in existing_columns:
            try:
                if is_postgres:
                    # PostgreSQL
                    sql = "ALTER TABLE strategy_builder ADD COLUMN config_json JSON"
                else:
                    # SQLite
                    sql = "ALTER TABLE strategy_builder ADD COLUMN config_json TEXT"
                
                conn.execute(text(sql))
                conn.commit()
                logger.info("✓ config_json 컬럼 추가 완료")
            except Exception as e:
                logger.error(f"✗ config_json 컬럼 추가 실패: {e}")
                conn.rollback()
                raise
        else:
            logger.info("⊙ config_json 컬럼 이미 존재")
    
    logger.info("✅ 마이그레이션 완료!")


if __name__ == "__main__":
    migrate()

