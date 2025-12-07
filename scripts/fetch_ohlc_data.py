"""
LS증권 API를 통해 종목 데이터를 수집하여 PostgreSQL에 저장

전략:
1. 종목 마스터 업데이트 (전체 종목 메타데이터)
2. 필터링으로 유니버스 생성 (거래대금 1000억 이상)
3. 선별된 종목만 과거 데이터 수집 (6개월)

사용법:
    # 전략별 유니버스 기반 수집 (추천)
    python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180
    python scripts/fetch_ohlc_data.py --strategy momentum --days 180
    
    # 특정 종목 수집
    python scripts/fetch_ohlc_data.py --symbols 005930,000660 --days 180
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List

from broker.ls.adapter import LSAdapter
from data.repository import OHLCRepository
from data.stock_filter import StockFilter
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


async def fetch_and_save_ohlc(
    symbols: List[str],
    interval: str,
    days: int,
    incremental: bool = True
):
    """
    종목 데이터를 수집하여 DB에 저장
    
    Args:
        symbols: 종목 코드 리스트
        interval: 시간 간격 (1d, 1m, 5m, 10m, 30m, 60m)
        days: 조회 기간 (일)
        incremental: 증분 업데이트 여부 (마지막 시점 이후만 수집)
    """
    # Repository 초기화
    repo = OHLCRepository()
    
    # 날짜 범위 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Fetching OHLC data for {len(symbols)} symbols")
    logger.info(f"Interval: {interval}, Period: {start_date.date()} ~ {end_date.date()}")
    logger.info(f"Incremental: {incremental}")
    
    # LS증권 어댑터 초기화
    async with LSAdapter() as adapter:
        total_saved = 0
        
        for idx, symbol in enumerate(symbols, 1):
            try:
                logger.info(f"[{idx}/{len(symbols)}] Processing {symbol}...")
                
                # 증분 업데이트: 마지막 데이터 시점 확인
                if incremental:
                    latest_ts = repo.get_latest_timestamp(symbol, interval)
                    if latest_ts:
                        start_date = latest_ts + timedelta(days=1)
                        logger.info(f"Latest data: {latest_ts.date()}, fetching from {start_date.date()}")
                        
                        if start_date >= end_date:
                            logger.info(f"Already up-to-date, skipping")
                            continue
                
                # OHLC 데이터 조회
                ohlc_list = await adapter.get_ohlc(
                    symbol=symbol,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not ohlc_list:
                    logger.warning(f"No data found for {symbol}")
                    continue
                
                logger.info(f"Fetched {len(ohlc_list)} records")
                
                # 배치 저장 (더 빠름)
                saved_count = await repo.save_ohlc_batch(ohlc_list, interval)
                total_saved += saved_count
                
                logger.info(f"✓ Saved {saved_count} records for {symbol}")
                
                # API Rate Limit 고려 (t8451: 초당 1건)
                await asyncio.sleep(1.1)  # 1.1초 대기
                
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")
                continue
    
    logger.info(f"Data fetch completed: {total_saved} total records saved")


async def fetch_by_universe(
    strategy_type: str,
    days: int = 180,
    interval: str = "1d"
):
    """
    전략별 유니버스 기반 데이터 수집
    
    Args:
        strategy_type: 전략 타입 (mean_reversion, momentum)
        days: 조회 기간 (일)
        interval: 시간 간격
    """
    logger.info(f"Fetching data for {strategy_type} universe")
    
    # 필터링 엔진
    stock_filter = StockFilter()
    
    # 유니버스 생성
    symbols = stock_filter.get_universe(
        strategy_type=strategy_type,
        min_volume_amount=100_000_000_000,  # 1000억원
        limit=200
    )
    
    if not symbols:
        logger.warning("No symbols in universe")
        return
    
    # 유니버스 저장
    stock_filter.save_universe(strategy_type, symbols)
    
    # 데이터 수집
    await fetch_and_save_ohlc(symbols, interval, days, incremental=True)


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="스마트 데이터 수집 시스템")
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["mean_reversion", "momentum"],
        help="전략 타입 (유니버스 기반 수집)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="종목 코드 리스트 (쉼표 구분, 예: 005930,000660)"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        choices=["1d", "1m", "5m", "10m", "30m", "60m"],
        help="시간 간격 (기본: 1d)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="조회 기간 (일, 기본: 180 = 6개월)"
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="증분 업데이트 비활성화 (전체 재수집)"
    )
    
    args = parser.parse_args()
    
    # 전략별 유니버스 수집
    if args.strategy:
        await fetch_by_universe(
            strategy_type=args.strategy,
            days=args.days,
            interval=args.interval
        )
    
    # 특정 종목 수집
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
        await fetch_and_save_ohlc(
            symbols=symbols,
            interval=args.interval,
            days=args.days,
            incremental=not args.no_incremental
        )
    
    else:
        logger.error("Please specify --strategy or --symbols")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
잠