"""
데이터베이스 시퀀스 수정 스크립트
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

print("🔧 데이터베이스 시퀀스 수정 중...")

with engine.connect() as conn:
    # users 테이블 시퀀스 수정
    result = conn.execute(text("""
        SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
    """))
    conn.commit()
    print(f"✅ users_id_seq 수정 완료: {result.scalar()}")
    
    # accounts 테이블 시퀀스 수정 (있다면)
    try:
        result = conn.execute(text("""
            SELECT setval('accounts_id_seq', (SELECT COALESCE(MAX(id), 1) FROM accounts));
        """))
        conn.commit()
        print(f"✅ accounts_id_seq 수정 완료: {result.scalar()}")
    except Exception as e:
        print(f"⚠️ accounts_id_seq 수정 실패 (테이블이 없을 수 있음): {e}")
    
    # strategies 테이블 시퀀스 수정 (있다면)
    try:
        result = conn.execute(text("""
            SELECT setval('strategies_id_seq', (SELECT COALESCE(MAX(id), 1) FROM strategies));
        """))
        conn.commit()
        print(f"✅ strategies_id_seq 수정 완료: {result.scalar()}")
    except Exception as e:
        print(f"⚠️ strategies_id_seq 수정 실패 (테이블이 없을 수 있음): {e}")

print("\n✅ 시퀀스 수정 완료!")
