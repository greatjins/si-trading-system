"""
업데이트된 조건으로 종목 선택 테스트
"""
from data.repository import get_db_session
from data.models import StockMasterModel

db = get_db_session()

try:
    # 업데이트된 조건
    query = db.query(StockMasterModel.symbol, StockMasterModel.name, StockMasterModel.market_cap, StockMasterModel.volume_amount)
    query = query.filter(StockMasterModel.market_cap >= 100000.0)  # 1000억
    query = query.filter(StockMasterModel.volume_amount >= 1000000000000.0)  # 100억
    query = query.filter(StockMasterModel.current_price >= 1000.0)
    query = query.filter(StockMasterModel.market.in_(['KOSPI', 'KOSDAQ']))
    query = query.filter(StockMasterModel.is_active == True)
    
    count = query.count()
    print(f"✅ 조건 만족 종목: {count}개")
    
    # PER 정렬
    query = query.filter(StockMasterModel.per.isnot(None))
    query = query.order_by(StockMasterModel.per.asc())
    
    stocks = query.limit(10).all()
    print(f"\n📋 PER 낮은 순 상위 10개:")
    for s in stocks:
        mcap = s.market_cap / 100 if s.market_cap else 0
        vol = s.volume_amount / 100000000 if s.volume_amount else 0
        print(f"  {s.symbol} {s.name}: 시총={mcap:.0f}억, 거래대금={vol:.0f}억")
    
finally:
    db.close()
