"""
StockMaster 데이터 상세 확인
"""
from data.repository import get_db_session
from data.models import StockMasterModel

db = get_db_session()

try:
    # 샘플 데이터 10개
    stocks = db.query(StockMasterModel).limit(10).all()
    
    print("📋 StockMaster 샘플 데이터:")
    print("-" * 100)
    
    for s in stocks:
        print(f"\n종목: {s.symbol} {s.name}")
        print(f"  시장: {s.market}")
        print(f"  시가총액: {s.market_cap}")
        print(f"  거래대금: {s.volume_amount}")
        print(f"  현재가: {s.current_price}")
        print(f"  활성: {s.is_active}")
        if hasattr(s, 'per'):
            print(f"  PER: {s.per}")
        if hasattr(s, 'pbr'):
            print(f"  PBR: {s.pbr}")
    
    # 컬럼 확인
    print("\n\n📊 StockMasterModel 컬럼:")
    for col in StockMasterModel.__table__.columns:
        print(f"  - {col.name}: {col.type}")
    
finally:
    db.close()
