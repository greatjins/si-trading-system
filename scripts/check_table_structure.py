"""
테이블 구조 확인 스크립트
"""
import yaml
from sqlalchemy import create_engine, text

# config.yaml 로드
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# 데이터베이스 연결
db_url = f"postgresql+pg8000://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
engine = create_engine(db_url)

print("🔍 테이블 구조 확인 중...")

with engine.connect() as conn:
    # 테이블 목록 확인
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    
    tables = [row[0] for row in result.fetchall()]
    
    print(f"\n📋 테이블 목록 ({len(tables)}개):")
    for table in tables:
        print(f"  - {table}")
    
    # trading_accounts 테이블이 있으면 컬럼 확인
    if 'trading_accounts' in tables:
        print(f"\n📊 trading_accounts 테이블 구조:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'trading_accounts'
            ORDER BY ordinal_position
        """))
        
        for row in result.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # 데이터 확인
        result = conn.execute(text("SELECT * FROM trading_accounts LIMIT 5"))
        rows = result.fetchall()
        
        if rows:
            print(f"\n📝 데이터 샘플 ({len(rows)}개):")
            columns = result.keys()
            for row in rows:
                print("\n  레코드:")
                for col, val in zip(columns, row):
                    if 'password' in col.lower() or 'secret' in col.lower():
                        print(f"    {col}: ****")
                    else:
                        print(f"    {col}: {val}")
        else:
            print("\n❌ 데이터가 없습니다")
    else:
        print("\n❌ trading_accounts 테이블이 없습니다")

print("\n완료!")
