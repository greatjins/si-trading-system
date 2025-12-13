"""
재무정보 확인 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.repository import get_db_session
from data.models import StockMasterModel

def main():
    """재무정보 확인"""
    session = get_db_session()
    
    try:
        # 전체 종목 수
        total_count = session.query(StockMasterModel).count()
        print(f"총 종목 수: {total_count}")
        
        # 재무정보가 있는 종목 수
        with_per = session.query(StockMasterModel).filter(StockMasterModel.per.isnot(None)).count()
        with_pbr = session.query(StockMasterModel).filter(StockMasterModel.pbr.isnot(None)).count()
        with_roe = session.query(StockMasterModel).filter(StockMasterModel.roe.isnot(None)).count()
        
        print(f"PER 있는 종목: {with_per}")
        print(f"PBR 있는 종목: {with_pbr}")
        print(f"ROE 있는 종목: {with_roe}")
        
        # 샘플 데이터 출력
        print("\n샘플 데이터 (상위 10개):")
        stocks = session.query(StockMasterModel).limit(10).all()
        for stock in stocks:
            print(f"{stock.symbol} {stock.name}: PER={stock.per}, PBR={stock.pbr}, ROE={stock.roe}")
        
        # 재무정보가 있는 종목 샘플
        print("\n재무정보가 있는 종목 (상위 10개):")
        stocks_with_financial = session.query(StockMasterModel).filter(
            StockMasterModel.per.isnot(None),
            StockMasterModel.pbr.isnot(None),
            StockMasterModel.roe.isnot(None)
        ).limit(10).all()
        
        for stock in stocks_with_financial:
            print(f"{stock.symbol} {stock.name}: PER={stock.per:.2f}, PBR={stock.pbr:.2f}, ROE={stock.roe:.2f}")
    
    finally:
        session.close()


if __name__ == "__main__":
    main()
