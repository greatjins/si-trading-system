"""
데이터베이스 스키마 확인 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_schema():
    """데이터베이스 스키마 확인"""
    
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
    logger.info(f"DB URL: {db_url.split('@')[0]}@***")  # 비밀번호 숨김
    
    engine = create_engine(db_url, echo=False)
    is_postgres = "postgresql" in db_url
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"데이터베이스 스키마 확인")
            logger.info(f"{'='*60}")
            logger.info(f"테이블 개수: {len(existing_tables)}")
            
            # strategy_builder 테이블 확인
            if 'strategy_builder' in existing_tables:
                logger.info(f"\n✓ strategy_builder 테이블 존재")
                
                columns = inspector.get_columns('strategy_builder')
                column_names = [col['name'] for col in columns]
                
                logger.info(f"\n컬럼 목록:")
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col.get('default') else ""
                    logger.info(f"  - {col['name']}: {col_type} {nullable}{default}")
                
                # config_json 필드 확인
                if 'config_json' in column_names:
                    logger.info(f"\n✅ config_json 필드가 존재합니다!")
                else:
                    logger.warning(f"\n❌ config_json 필드가 없습니다!")
                    logger.info(f"   마이그레이션 실행: python scripts/migrate_add_config_json.py")
            else:
                logger.warning(f"\n❌ strategy_builder 테이블이 없습니다!")
                logger.info(f"   테이블 생성 필요")
            
            # 다른 주요 테이블 확인
            logger.info(f"\n{'='*60}")
            logger.info(f"주요 테이블 목록:")
            for table in sorted(existing_tables):
                columns = inspector.get_columns(table)
                logger.info(f"  - {table}: {len(columns)}개 컬럼")
            
            logger.info(f"\n{'='*60}")
            logger.info("스키마 확인 완료")
            
    except Exception as e:
        logger.error(f"스키마 확인 실패: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    check_schema()

