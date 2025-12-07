"""
일봉 연속조회 테스트
"""
import asyncio
from datetime import datetime, timedelta
from broker.ls.adapter import LSAdapter
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_continuous_ohlc():
    """일봉 연속조회 테스트"""
    
    symbol = "005930"  # 삼성전자
    end_date = datetime.now()
    start_date = end_date - timedelta(days=300)  # 300일
    
    logger.info(f"Testing continuous OHLC for {symbol}")
    logger.info(f"Period: {start_date.date()} ~ {end_date.date()}")
    
    async with LSAdapter() as adapter:
        ohlc_list = await adapter.get_ohlc(
            symbol=symbol,
            interval="1d",
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Total OHLC records: {len(ohlc_list)}")
        
        if ohlc_list:
            logger.info(f"First record: {ohlc_list[0].timestamp.date()}")
            logger.info(f"Last record: {ohlc_list[-1].timestamp.date()}")
            
            # 날짜별 개수 확인
            dates = [o.timestamp.date() for o in ohlc_list]
            logger.info(f"Date range: {min(dates)} ~ {max(dates)}")
            logger.info(f"Total days: {len(dates)}")


if __name__ == "__main__":
    asyncio.run(test_continuous_ohlc())
