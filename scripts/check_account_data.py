"""
계좌 데이터 확인 스크립트
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

print("🔍 계좌 데이터 확인 중...")

with engine.connect() as conn:
    # 계좌 테이블 확인
    result = conn.execute(text("""
        SELECT 
            id,
            user_id,
            broker,
            account_number_encrypted,
            alias,
            is_active
        FROM trading_accounts
        ORDER BY id
    """))
    
    accounts = result.fetchall()
    
    if not accounts:
        print("❌ 등록된 계좌가 없습니다")
    else:
        print(f"\n✅ 총 {len(accounts)}개 계좌 발견:\n")
        for acc in accounts:
            print(f"ID: {acc[0]}")
            print(f"User ID: {acc[1]}")
            print(f"Broker: {acc[2]}")
            print(f"Account Number (암호화): {acc[3][:50]}...")
            print(f"Alias: {acc[4]}")
            print(f"Active: {acc[5]}")
            print("-" * 60)

print("\n완료!")
