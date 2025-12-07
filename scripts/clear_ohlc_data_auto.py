"""
OHLC 데이터 자동 삭제 스크립트 (확인 없이)
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

print("🗑️  OHLC 데이터 삭제 중...\n")

with engine.connect() as conn:
    # 현재 데이터 개수 확인
    result = conn.execute(text("SELECT COUNT(*) FROM ohlc_data"))
    count_before = result.scalar()
    print(f"삭제 전 데이터: {count_before:,}개")
    
    # 데이터 삭제
    conn.execute(text("TRUNCATE TABLE ohlc_data"))
    conn.commit()
    
    # 삭제 후 확인
    result = conn.execute(text("SELECT COUNT(*) FROM ohlc_data"))
    count_after = result.scalar()
    
    print(f"\n✅ 삭제 완료!")
    print(f"  - 삭제 전: {count_before:,}개")
    print(f"  - 삭제 후: {count_after:,}개")
    print(f"  - 삭제됨: {count_before - count_after:,}개")
    
    print(f"\n📝 변경사항:")
    print(f"  - 수정주가: N → Y (적용)")
    print(f"  - 거래소 구분: K → U (통합)")
    
    print(f"\n🔄 다음 단계:")
    print(f"  데이터 재수집 필요")

print("\n완료!")
