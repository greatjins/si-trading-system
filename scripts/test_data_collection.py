"""
데이터 수집 시스템 테스트

단계별로 각 컴포넌트를 테스트합니다.
"""
import asyncio
from datetime import datetime, timedelta

from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


async def test_database_connection():
    """PostgreSQL 연결 테스트"""
    logger.info("=" * 50)
    logger.info("Test 1: Database Connection")
    logger.info("=" * 50)
    
    try:
        from data.repository import get_db_session
        from sqlalchemy import text
        
        session = get_db_session()
        
        # 간단한 쿼리 실행 (SQLAlchemy 2.0 문법)
        result = session.execute(text("SELECT 1"))
        logger.info("✓ PostgreSQL 연결 성공")
        session.close()
        return True
    
    except Exception as e:
        logger.error(f"✗ PostgreSQL 연결 실패: {e}")
        return False


async def test_ls_api_connection():
    """LS증권 API 연결 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("Test 2: LS API Connection")
    logger.info("=" * 50)
    
    try:
        from broker.ls.adapter import LSAdapter
        
        async with LSAdapter() as adapter:
            logger.info("✓ LS증권 API 인증 성공")
            logger.info(f"  - Access Token: {adapter.client.oauth.access_token[:20]}...")
            return True
    
    except Exception as e:
        logger.error(f"✗ LS증권 API 연결 실패: {e}")
        return False


async def test_fetch_current_price():
    """현재가 조회 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("Test 3: Fetch Current Price")
    logger.info("=" * 50)
    
    try:
        from broker.ls.adapter import LSAdapter
        
        async with LSAdapter() as adapter:
            # 삼성전자 현재가 조회
            quote = await adapter.market_service.get_current_price("005930")
            
            logger.info("✓ 현재가 조회 성공")
            logger.info(f"  - 종목: {quote.name} ({quote.symbol})")
            logger.info(f"  - 현재가: {quote.price:,.0f}원")
            logger.info(f"  - 거래량: {quote.volume:,}주")
            logger.info(f"  - 등락률: {quote.change_rate:+.2f}%")
            return True
    
    except Exception as e:
        logger.error(f"✗ 현재가 조회 실패: {e}")
        return False


async def test_fetch_ohlc():
    """OHLC 데이터 조회 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("Test 4: Fetch OHLC Data")
    logger.info("=" * 50)
    
    try:
        from broker.ls.adapter import LSAdapter
        
        async with LSAdapter() as adapter:
            # 삼성전자 최근 10일 일봉
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            
            ohlc_list = await adapter.get_ohlc(
                symbol="005930",
                interval="1d",
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info("✓ OHLC 데이터 조회 성공")
            logger.info(f"  - 조회 기간: {start_date.date()} ~ {end_date.date()}")
            logger.info(f"  - 데이터 개수: {len(ohlc_list)}개")
            
            if ohlc_list:
                latest = ohlc_list[-1]
                logger.info(f"  - 최근 데이터: {latest.timestamp.date()}")
                logger.info(f"    Open: {latest.open:,.0f}, High: {latest.high:,.0f}")
                logger.info(f"    Low: {latest.low:,.0f}, Close: {latest.close:,.0f}")
                logger.info(f"    Volume: {latest.volume:,}")
            
            return True
    
    except Exception as e:
        logger.error(f"✗ OHLC 데이터 조회 실패: {e}")
        return False


async def test_save_ohlc():
    """OHLC 데이터 저장 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("Test 5: Save OHLC Data")
    logger.info("=" * 50)
    
    try:
        from broker.ls.adapter import LSAdapter
        from data.repository import OHLCRepository
        
        # 데이터 조회
        async with LSAdapter() as adapter:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            
            ohlc_list = await adapter.get_ohlc(
                symbol="005930",
                interval="1d",
                start_date=start_date,
                end_date=end_date
            )
        
        # 데이터 저장
        repo = OHLCRepository()
        saved_count = await repo.save_ohlc_batch(ohlc_list, "1d")
        
        logger.info("✓ OHLC 데이터 저장 성공")
        logger.info(f"  - 저장된 레코드: {saved_count}개")
        
        # 저장된 데이터 조회
        df = repo.get_ohlc("005930", "1d", start_date, end_date)
        logger.info(f"  - DB 조회 결과: {len(df)}개")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ OHLC 데이터 저장 실패: {e}")
        return False


async def test_stock_filter():
    """종목 필터링 테스트"""
    logger.info("\n" + "=" * 50)
    logger.info("Test 6: Stock Filtering")
    logger.info("=" * 50)
    
    try:
        from data.stock_filter import StockFilter
        
        stock_filter = StockFilter()
        
        # 거래대금 필터 (테스트용으로 낮은 기준)
        symbols = stock_filter.filter_by_liquidity(min_volume_amount=10_000_000_000)  # 100억
        
        logger.info("✓ 종목 필터링 성공")
        logger.info(f"  - 필터링된 종목 수: {len(symbols)}개")
        
        if symbols:
            logger.info(f"  - 샘플: {symbols[:5]}")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ 종목 필터링 실패: {e}")
        return False


async def main():
    """전체 테스트 실행"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "데이터 수집 시스템 테스트" + " " * 23 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("LS API Connection", test_ls_api_connection),
        ("Fetch Current Price", test_fetch_current_price),
        ("Fetch OHLC Data", test_fetch_ohlc),
        ("Save OHLC Data", test_save_ohlc),
        ("Stock Filtering", test_stock_filter),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            results.append((name, False))
    
    # 결과 요약
    logger.info("\n" + "=" * 50)
    logger.info("Test Results Summary")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("=" * 50)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 50)
    
    if passed == total:
        logger.info("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
    else:
        logger.warning(f"\n⚠️  {total - passed}개 테스트 실패. 위 로그를 확인하세요.")


if __name__ == "__main__":
    asyncio.run(main())
