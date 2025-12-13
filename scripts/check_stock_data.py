"""
DB 종목 데이터 확인
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.repository import get_db_session
from data.models import StockMasterModel

session = get_db_session()

try:
    # 전체 종목 수
    total = session.query(StockMasterModel).filter_by(is_active=True).count()
    print(f"총 종목 수: {total}")
    
    # 재무 정보가 있는 종목 수
    with_financial = session.query(StockMasterModel).filter(
        StockMasterModel.is_active == True,
        StockMasterModel.per.isnot(None),
        StockMasterModel.pbr.isnot(None),
        StockMasterModel.roe.isnot(None)
    ).count()
    print(f"재무 정보 있는 종목: {with_financial}")
    
    # 전략 조건에 맞는 종목 (PER < 10, PBR < 1, ROE > 10)
    value_stocks = session.query(StockMasterModel).filter(
        StockMasterModel.is_active == True,
        StockMasterModel.per > 0,
        StockMasterModel.per < 10,
        StockMasterModel.pbr > 0,
        StockMasterModel.pbr < 1.0,
        StockMasterModel.roe > 10
    ).all()
    
    print(f"\n전략 조건 맞는 종목: {len(value_stocks)}")
    
    if value_stocks:
        print("\n상위 10개:")
        for stock in value_stocks[:10]:
            print(f"  {stock.symbol} {stock.name}: PER={stock.per:.2f}, PBR={stock.pbr:.2f}, ROE={stock.roe:.2f}")
    
    # 샘플 종목 정보
    print("\n\n샘플 종목 (상위 5개):")
    samples = session.query(StockMasterModel).filter_by(is_active=True).limit(5).all()
    for s in samples:
        print(f"  {s.symbol} {s.name}")
        print(f"    PER={s.per}, PBR={s.pbr}, ROE={s.roe}")
        print(f"    거래대금={s.volume_amount}")

finally:
    session.close()
