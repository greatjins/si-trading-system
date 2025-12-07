"""
거래대금 단위 수정 스크립트

기존 데이터의 거래대금이 백만원 단위로 저장되어 있어서
원 단위로 변환 (x 1,000,000)
"""
from data.repository import get_db_session
from data.models import StockMasterModel
from utils.logger import setup_logger

logger = setup_logger(__name__)


def fix_volume_amount():
    """거래대금 단위 수정"""
    session = get_db_session()
    
    try:
        stocks = session.query(StockMasterModel).all()
        
        logger.info(f"총 {len(stocks)}개 종목 처리 중...")
        
        for stock in stocks:
            # 백만원 → 원 (x 1,000,000)
            old_value = stock.volume_amount
            new_value = old_value * 1_000_000
            
            stock.volume_amount = new_value
            
            logger.info(
                f"{stock.symbol} {stock.name}: "
                f"{old_value:,} → {new_value:,}원 ({new_value/100000000:.0f}억)"
            )
        
        session.commit()
        logger.info("✅ 거래대금 단위 수정 완료!")
    
    except Exception as e:
        session.rollback()
        logger.error(f"오류 발생: {e}")
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    fix_volume_amount()
