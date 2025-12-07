"""
OHLC 데이터 삭제 스크립트
수정주가 적용 및 거래소 구분 변경을 위해 기존 데이터 삭제
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
    
    # 종목별 통계
    result = conn.execute(text("""
        SELECT symbol, COUNT(*) as count
        FROM ohlc_data
        GROUP BY symbol
        ORDER BY count DESC
        LIMIT 10
    """))
    
    print(f"\n주요 종목:")
    for row in result.fetchall():
        print(f"  - {row[0]}: {row[1]:,}개")
    
    # 삭제 확인
    print(f"\n⚠️  경고: {count_before:,}개의 OHLC 데이터를 삭제합니다.")
    print("이유: 수정주가 적용 및 거래소 구분 변경 (K → U)")
    
    confirm = input("\n계속하시겠습니까? (yes/no): ")
    
    if confirm.lower() == 'yes':
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
        
        print(f"\n📝 다음 단계:")
        print(f"  1. 데이터 재수집: python scripts/fetch_ohlc_data.py")
        print(f"  2. 또는 수집 API 사용: POST /api/data/collect/start")
    else:
        print("\n❌ 취소되었습니다.")

print("\n완료!")
