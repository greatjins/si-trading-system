"""
SQLite에서 PostgreSQL로 데이터 마이그레이션
"""
import os
import sys
import shutil
from datetime import datetime

# Windows 인코딩 문제 해결
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from data.models import Base, BacktestResultModel, TradeModel, StrategyBuilderModel
from data.account_models import TradingAccount
from api.auth.models import User, APIKey
from utils.logger import setup_logger

logger = setup_logger(__name__)


def backup_sqlite():
    """SQLite 백업"""
    sqlite_path = "data/hts.db"
    if os.path.exists(sqlite_path):
        backup_path = f"data/hts.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"SQLite backed up to: {backup_path}")
        return backup_path
    return None


def create_postgres_tables(pg_engine):
    """PostgreSQL 테이블 생성"""
    logger.info("Creating PostgreSQL tables...")
    Base.metadata.create_all(pg_engine)
    logger.info("✓ Tables created")


def migrate_data(sqlite_engine, pg_engine):
    """데이터 마이그레이션"""
    logger.info("Starting data migration...")
    
    # 세션 생성
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=pg_engine)
    
    sqlite_session = SQLiteSession()
    pg_session = PostgresSession()
    
    try:
        # 테이블 목록
        tables = [
            ('users', User),
            ('api_keys', APIKey),
            ('trading_accounts', TradingAccount),
            ('backtest_results', BacktestResultModel),
            ('trades', TradeModel),
            ('strategy_builder', StrategyBuilderModel),
        ]
        
        for table_name, model_class in tables:
            logger.info(f"Migrating {table_name}...")
            
            # SQLite에서 데이터 읽기
            records = sqlite_session.query(model_class).all()
            
            if records:
                # PostgreSQL에 데이터 쓰기
                for record in records:
                    # 기존 객체를 새 세션에 추가
                    pg_session.merge(record)
                
                pg_session.commit()
                logger.info(f"✓ Migrated {len(records)} records from {table_name}")
            else:
                logger.info(f"  No data in {table_name}")
        
        logger.info("✓ Data migration completed")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        pg_session.rollback()
        raise
    finally:
        sqlite_session.close()
        pg_session.close()


def verify_migration(sqlite_engine, pg_engine):
    """마이그레이션 검증"""
    logger.info("Verifying migration...")
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=pg_engine)
    
    sqlite_session = SQLiteSession()
    pg_session = PostgresSession()
    
    try:
        # 레코드 수 비교
        sqlite_users = sqlite_session.query(User).count()
        pg_users = pg_session.query(User).count()
        sqlite_accounts = sqlite_session.query(TradingAccount).count()
        pg_accounts = pg_session.query(TradingAccount).count()
        
        logger.info(f"Users - SQLite: {sqlite_users}, PostgreSQL: {pg_users}")
        logger.info(f"Accounts - SQLite: {sqlite_accounts}, PostgreSQL: {pg_accounts}")
        
        if sqlite_users == pg_users and sqlite_accounts == pg_accounts:
            logger.info("✓ Verification passed")
            return True
        else:
            logger.error("✗ Verification failed: record count mismatch")
            return False
            
    finally:
        sqlite_session.close()
        pg_session.close()


def main():
    """메인 마이그레이션 프로세스"""
    logger.info("=" * 60)
    logger.info("SQLite → PostgreSQL Migration")
    logger.info("=" * 60)
    
    # 1. SQLite 백업
    backup_path = backup_sqlite()
    if backup_path:
        logger.info(f"✓ Backup created: {backup_path}")
    
    # 2. 데이터베이스 연결
    sqlite_url = "sqlite:///./data/hts.db"
    postgres_url = "postgresql+pg8000://hts_user:hts_password_2024@127.0.0.1:5433/hts"
    
    logger.info("Connecting to databases...")
    sqlite_engine = create_engine(sqlite_url)
    
    # Windows 한글 경로 문제 우회: 환경 변수 초기화
    for key in list(os.environ.keys()):
        if key.startswith('PG') or key.startswith('PSQL'):
            del os.environ[key]
    
    pg_engine = create_engine(
        postgres_url,
        pool_pre_ping=True
    )
    
    try:
        # PostgreSQL 연결 테스트
        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✓ PostgreSQL connected: {version.split(',')[0]}")
        
        # 3. PostgreSQL 테이블 생성
        create_postgres_tables(pg_engine)
        
        # 4. 데이터 마이그레이션
        migrate_data(sqlite_engine, pg_engine)
        
        # 5. 검증
        if verify_migration(sqlite_engine, pg_engine):
            logger.info("=" * 60)
            logger.info("✓ Migration completed successfully!")
            logger.info("=" * 60)
            logger.info("\nNext steps:")
            logger.info("1. Update config.yaml to use PostgreSQL")
            logger.info("2. Restart the application")
            logger.info(f"3. Keep SQLite backup: {backup_path}")
        else:
            logger.error("Migration verification failed!")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1
    finally:
        sqlite_engine.dispose()
        pg_engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
