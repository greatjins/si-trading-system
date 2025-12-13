"""
데이터베이스 연결 테스트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_connection():
    """데이터베이스 연결 테스트"""
    
    db_type = config.get("database.type", "sqlite")
    
    print("=" * 60)
    print(f"데이터베이스 연결 테스트: {db_type.upper()}")
    print("=" * 60)
    print()
    
    # 연결 문자열 생성
    if db_type == "sqlite":
        db_path = config.get("database.path", "data/hts.db")
        db_url = f"sqlite:///{db_path}"
        print(f"SQLite 경로: {db_path}")
    else:
        host = config.get("database.host", "localhost")
        port = config.get("database.port", 5432)
        database = config.get("database.database", "hts")
        username = config.get("database.user", "hts_user")
        password = config.get("database.password", "")
        db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
        
        print(f"PostgreSQL 설정:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  User: {username}")
        print(f"  Password: {'*' * len(password)}")
    
    print()
    print(f"연결 문자열: {db_url.replace(password, '***')}")
    print()
    
    try:
        # 엔진 생성
        print("[1/4] 엔진 생성 중...")
        engine = create_engine(db_url, echo=False)
        print("✓ 엔진 생성 성공")
        print()
        
        # 연결 테스트
        print("[2/4] 데이터베이스 연결 중...")
        with engine.connect() as conn:
            print("✓ 연결 성공")
            print()
            
            # 버전 확인
            print("[3/4] 데이터베이스 버전 확인...")
            if db_type == "sqlite":
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                print(f"✓ SQLite 버전: {version}")
            else:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✓ PostgreSQL 버전: {version}")
            print()
            
            # 테이블 목록 확인
            print("[4/4] 테이블 목록 확인...")
            if db_type == "sqlite":
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ))
            else:
                result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
                ))
            
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print(f"✓ 테이블 {len(tables)}개 발견:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠ 테이블이 없습니다 (첫 실행 시 정상)")
            print()
        
        print("=" * 60)
        print("✅ 데이터베이스 연결 테스트 성공!")
        print("=" * 60)
        return True
    
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 데이터베이스 연결 실패!")
        print("=" * 60)
        print()
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        print()
        
        # 해결 방법 제안
        print("해결 방법:")
        if db_type == "postgresql":
            print("1. Docker Desktop이 실행 중인지 확인")
            print("2. PostgreSQL 컨테이너 시작: start_postgres.bat")
            print("3. 컨테이너 상태 확인: docker-compose ps")
            print("4. 로그 확인: docker-compose logs postgres")
            print("5. 임시로 SQLite 사용: config.yaml에서 type을 'sqlite'로 변경")
        else:
            print("1. data 폴더가 존재하는지 확인")
            print("2. 파일 권한 확인")
        
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
