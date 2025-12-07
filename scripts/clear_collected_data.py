"""
수집된 데이터 삭제 스크립트

stock_master와 ohlc_data 테이블의 모든 데이터를 삭제합니다.
"""
from data.repository import get_db_session
from data.models import StockMasterModel, OHLCModel, StockUniverseModel
from utils.logger import setup_logger

logger = setup_logger(__name__)


def clear_all_data():
    """모든 수집 데이터 삭제"""
    session = get_db_session()
    
    try:
        # 1. OHLC 데이터 삭제
        ohlc_count = session.query(OHLCModel).count()
        session.query(OHLCModel).delete()
        logger.info(f"✓ OHLC 데이터 {ohlc_count:,}개 삭제")
        
        # 2. 종목 유니버스 삭제
        universe_count = session.query(StockUniverseModel).count()
        session.query(StockUniverseModel).delete()
        logger.info(f"✓ 종목 유니버스 {universe_count:,}개 삭제")
        
        # 3. 종목 마스터 삭제
        stock_count = session.query(StockMasterModel).count()
        session.query(StockMasterModel).delete()
        logger.info(f"✓ 종목 마스터 {stock_count:,}개 삭제")
        
        session.commit()
        logger.info("✅ 모든 데이터 삭제 완료!")
        
        return {
            "ohlc_count": ohlc_count,
            "universe_count": universe_count,
            "stock_count": stock_count
        }
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 오류 발생: {e}")
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    
    # 확인 메시지
    print("⚠️  경고: 모든 수집 데이터가 삭제됩니다!")
    print("   - stock_master (종목 마스터)")
    print("   - stock_universe (종목 유니버스)")
    print("   - ohlc_data (OHLC 데이터)")
    print()
    
    confirm = input("정말 삭제하시겠습니까? (yes/no): ")
    
    if confirm.lower() == "yes":
        result = clear_all_data()
        print()
        print("삭제 완료:")
        print(f"  - 종목 마스터: {result['stock_count']:,}개")
        print(f"  - 종목 유니버스: {result['universe_count']:,}개")
        print(f"  - OHLC 데이터: {result['ohlc_count']:,}개")
    else:
        print("취소되었습니다.")
        sys.exit(0)
