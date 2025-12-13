"""
StockMaster 테이블 확인
"""
from data.repository import get_db_session
from data.models import StockMasterModel

db = get_db_session()

try:
    # 전체 종목 수
    total = db.query(StockMasterModel).count()
    print(f"✅ 전체 종목 수: {total}")
    
    # 시가총액 1000억 이상
    query1 = db.query(StockMasterModel).filter(StockMasterModel.market_cap >= 100000000000.0)
    count1 = query1.count()
    print(f"\n📊 시가총액 >= 1000억: {count1}개")
    
    # 거래대금 100억 이상
    query2 = query1.filter(StockMasterModel.volume_amount >= 10000000000.0)
    count2 = query2.count()
    print(f"📊 + 거래대금 >= 100억: {count2}개")
    
    # 가격 1000원 이상
    query3 = query2.filter(StockMasterModel.current_price >= 1000.0)
    count3 = query3.count()
    print(f"📊 + 가격 >= 1000원: {count3}개")
    
    # 시장 필터
    query4 = query3.filter(StockMasterModel.market.in_(['KOSPI', 'KOSDAQ']))
    count4 = query4.count()
    print(f"📊 + 시장 (KOSPI/KOSDAQ): {count4}개")
    
    # 활성 종목
    query5 = query4.filter(StockMasterModel.is_active == True)
    count5 = query5.count()
    print(f"📊 + 활성 종목: {count5}개")
    
    # PER 있는 종목
    if hasattr(StockMasterModel, 'per'):
        query6 = query5.filter(StockMasterModel.per.isnot(None))
        count6 = query6.count()
        print(f"📊 + PER 있음: {count6}개")
        
        # 상위 10개 출력
        stocks = query6.order_by(StockMasterModel.per.asc()).limit(10).all()
        print(f"\n📋 PER 낮은 순 상위 10개:")
        for s in stocks:
            print(f"  {s.symbol} {s.name}: PER={s.per:.2f}, 시총={s.market_cap/100000000:.0f}억")
    else:
        print("\n⚠️ StockMasterModel에 per 필드가 없습니다")
        
        # 그냥 상위 10개 출력
        stocks = query5.limit(10).all()
        print(f"\n📋 조건 만족 종목 10개:")
        for s in stocks:
            mcap = s.market_cap / 100000000 if s.market_cap else 0
            vol = s.volume_amount / 100000000 if s.volume_amount else 0
            print(f"  {s.symbol} {s.name}: 시총={mcap:.0f}억, 거래대금={vol:.0f}억, 가격={s.current_price}")
    
finally:
    db.close()
