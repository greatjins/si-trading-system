"""
OHLC 데이터 확인 스크립트
"""
import yaml
from sqlalchemy import create_engine, text
from datetime import datetime

# config.yaml 로드
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# 데이터베이스 연결
db_url = f"postgresql+pg8000://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
engine = create_engine(db_url)

print("📊 OHLC 데이터 확인 중...\n")

with engine.connect() as conn:
    # 005930 일봉 데이터 개수 확인
    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM ohlc_data
        WHERE symbol = '005930'
        AND interval = '1d'
    """))
    
    count = result.scalar()
    print(f"✅ 005930 일봉 데이터: {count}개\n")
    
    # 날짜 범위 확인
    result = conn.execute(text("""
        SELECT 
            MIN(timestamp) as first_date,
            MAX(timestamp) as last_date
        FROM ohlc_data
        WHERE symbol = '005930'
        AND interval = '1d'
    """))
    
    row = result.fetchone()
    if row and row[0]:
        first_date = row[0]
        last_date = row[1]
        
        # 날짜 차이 계산
        if isinstance(first_date, str):
            first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        
        days_diff = (last_date - first_date).days
        
        print(f"📅 데이터 기간:")
        print(f"  - 시작일: {first_date.strftime('%Y-%m-%d')}")
        print(f"  - 종료일: {last_date.strftime('%Y-%m-%d')}")
        print(f"  - 기간: {days_diff}일\n")
    
    # 최근 5개 데이터 샘플
    result = conn.execute(text("""
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM ohlc_data
        WHERE symbol = '005930'
        AND interval = '1d'
        ORDER BY timestamp DESC
        LIMIT 5
    """))
    
    rows = result.fetchall()
    
    if rows:
        print(f"📈 최근 5개 데이터:")
        print(f"{'날짜':<12} {'시가':>10} {'고가':>10} {'저가':>10} {'종가':>10} {'거래량':>12}")
        print("-" * 70)
        
        for row in rows:
            timestamp = row[0]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            date_str = timestamp.strftime('%Y-%m-%d')
            open_price = f"{row[1]:,.0f}"
            high_price = f"{row[2]:,.0f}"
            low_price = f"{row[3]:,.0f}"
            close_price = f"{row[4]:,.0f}"
            volume = f"{row[5]:,.0f}"
            
            print(f"{date_str:<12} {open_price:>10} {high_price:>10} {low_price:>10} {close_price:>10} {volume:>12}")
    else:
        print("❌ 데이터가 없습니다")
    
    # 전체 통계
    print(f"\n📊 전체 OHLC 데이터 통계:")
    result = conn.execute(text("""
        SELECT 
            symbol,
            interval,
            COUNT(*) as count,
            MIN(timestamp) as first_date,
            MAX(timestamp) as last_date
        FROM ohlc_data
        GROUP BY symbol, interval
        ORDER BY symbol, interval
    """))
    
    rows = result.fetchall()
    
    if rows:
        print(f"\n{'종목코드':<10} {'인터벌':<8} {'데이터 수':>10} {'시작일':<12} {'종료일':<12}")
        print("-" * 60)
        
        for row in rows:
            symbol = row[0]
            interval = row[1]
            count = row[2]
            first = row[3]
            last = row[4]
            
            if isinstance(first, str):
                first = datetime.fromisoformat(first.replace('Z', '+00:00'))
            if isinstance(last, str):
                last = datetime.fromisoformat(last.replace('Z', '+00:00'))
            
            first_str = first.strftime('%Y-%m-%d')
            last_str = last.strftime('%Y-%m-%d')
            
            print(f"{symbol:<10} {interval:<8} {count:>10} {first_str:<12} {last_str:<12}")
    else:
        print("  데이터 없음")

print("\n완료!")
