#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
"""

import sys
import asyncio
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트를 Python 경로에 추가
sys.path.append('.')

from data.models import Base, BacktestResultModel
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def get_database_url():
    """데이터베이스 URL 생성"""
    db_config = config.get("database", {})
    
    if db_config.get("type") == "postgresql":
        return (
            f"postgresql+pg8000://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
    else:
        # SQLite 폴백
        return f"sqlite:///{db_config.get('sqlite_fallback', 'data/hts.db')}"


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """컬럼 존재 여부 확인"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    
    print("🔧 데이터베이스 마이그레이션 시작")
    print("=" * 50)
    
    try:
        # 데이터베이스 연결
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        print(f"📡 데이터베이스 연결: {database_url.split('@')[0]}@***")
        
        # 연결 테스트
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 데이터베이스 연결 성공")
        
        # 테이블 존재 확인
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"\n📋 기존 테이블: {len(existing_tables)}개")
        for table in existing_tables:
            print(f"   - {table}")
        
        # 누락된 컬럼 확인 및 추가
        migrations_needed = []
        
        # backtest_results 테이블 확인
        if 'backtest_results' in existing_tables:
            print(f"\n🔍 backtest_results 테이블 컬럼 확인")
            
            columns = inspector.get_columns('backtest_results')
            existing_columns = [col['name'] for col in columns]
            
            print(f"   기존 컬럼: {existing_columns}")
            
            # equity_timestamps 컬럼 확인
            if 'equity_timestamps' not in existing_columns:
                migrations_needed.append({
                    'table': 'backtest_results',
                    'column': 'equity_timestamps',
                    'type': 'JSON',
                    'sql': 'ALTER TABLE backtest_results ADD COLUMN equity_timestamps JSON'
                })
                print("   ❌ equity_timestamps 컬럼 누락")
            else:
                print("   ✅ equity_timestamps 컬럼 존재")
            
            # value 컬럼 확인 (OHLC 테이블용)
            if 'ohlc_data' in existing_tables:
                ohlc_columns = inspector.get_columns('ohlc_data')
                ohlc_column_names = [col['name'] for col in ohlc_columns]
                
                if 'value' not in ohlc_column_names:
                    migrations_needed.append({
                        'table': 'ohlc_data',
                        'column': 'value',
                        'type': 'FLOAT',
                        'sql': 'ALTER TABLE ohlc_data ADD COLUMN value FLOAT'
                    })
                    print("   ❌ ohlc_data.value 컬럼 누락")
        
        # 마이그레이션 실행
        if migrations_needed:
            print(f"\n🚀 마이그레이션 실행: {len(migrations_needed)}개 작업")
            
            with engine.connect() as conn:
                for migration in migrations_needed:
                    try:
                        print(f"   실행: {migration['sql']}")
                        conn.execute(text(migration['sql']))
                        conn.commit()
                        print(f"   ✅ {migration['table']}.{migration['column']} 추가 완료")
                    except Exception as e:
                        print(f"   ❌ {migration['table']}.{migration['column']} 추가 실패: {e}")
        else:
            print("\n✅ 마이그레이션이 필요한 항목이 없습니다")
        
        # 테이블이 없으면 생성
        if not existing_tables:
            print("\n🏗️ 테이블 생성 중...")
            Base.metadata.create_all(engine)
            print("✅ 모든 테이블 생성 완료")
        
        # 최종 확인
        print(f"\n🔍 마이그레이션 후 상태 확인")
        inspector = inspect(engine)
        
        if 'backtest_results' in inspector.get_table_names():
            columns = inspector.get_columns('backtest_results')
            column_names = [col['name'] for col in columns]
            
            if 'equity_timestamps' in column_names:
                print("✅ equity_timestamps 컬럼 확인됨")
            else:
                print("❌ equity_timestamps 컬럼 여전히 누락")
        
        print("\n" + "=" * 50)
        print("🎉 데이터베이스 마이그레이션 완료!")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        logger.error(f"Database migration failed: {e}")
        return False
    
    return True


def verify_migration():
    """마이그레이션 검증"""
    
    print("\n🔍 마이그레이션 검증 중...")
    
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # 테스트 쿼리 실행
        with engine.connect() as conn:
            # equity_timestamps 컬럼 사용 쿼리 테스트
            result = conn.execute(text("""
                SELECT id, strategy_name, equity_timestamps 
                FROM backtest_results 
                LIMIT 1
            """))
            
            print("✅ equity_timestamps 컬럼 쿼리 성공")
            
            # 샘플 데이터 확인
            row = result.fetchone()
            if row:
                print(f"   샘플 데이터: ID={row[0]}, Strategy={row[1]}")
            else:
                print("   데이터 없음 (정상)")
        
        return True
        
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False


if __name__ == "__main__":
    success = migrate_database()
    
    if success:
        verify_migration()
    else:
        sys.exit(1)