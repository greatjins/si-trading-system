"""
종목 마스터 업데이트 스크립트

전체 종목의 메타데이터를 수집하여 stock_master 테이블에 저장
- 현재가, 거래대금, 52주 최고/최저가 등

사용법:
    python scripts/update_stock_master.py
    python scripts/update_stock_master.py --symbols 005930,000660
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from broker.ls.adapter import LSAdapter
from data.models import Base, StockMasterModel
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


# KOSPI 200 대표 종목 (샘플)
DEFAULT_SYMBOLS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035720",  # 카카오
    "035420",  # NAVER
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "005380",  # 현대차
    "000270",  # 기아
    "068270",  # 셀트리온
    "207940",  # 삼성바이오로직스
    "005490",  # POSCO홀딩스
    "012330",  # 현대모비스
    "028260",  # 삼성물산
    "066570",  # LG전자
    "003670",  # 포스코퓨처엠
    "096770",  # SK이노베이션
    "017670",  # SK텔레콤
    "009150",  # 삼성전기
    "034730",  # SK
    "018260",  # 삼성에스디에스
]


def get_db_session():
    """데이터베이스 세션 생성"""
    db_type = config.get("database.type", "sqlite")
    if db_type == "sqlite":
        db_path = config.get("database.path", "data/hts.db")
        db_url = f"sqlite:///{db_path}"
    else:
        # PostgreSQL
        host = config.get("database.host", "localhost")
        port = config.get("database.port", 5432)
        database = config.get("database.database", "hts")
        username = config.get("database.user", "hts_user")
        password = config.get("database.password", "")
        db_url = f"postgresql+pg8000://{username}:{password}@{host}:{port}/{database}"
    
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


async def update_stock_master_from_top_volume(count: int = 200):
    """
    거래대금 상위 종목으로 마스터 업데이트 (최적화 버전)
    
    Args:
        count: 조회할 종목 수 (기본: 200)
    """
    logger.info(f"Updating stock master from top {count} volume stocks")
    
    session = get_db_session()
    
    async with LSAdapter() as adapter:
        # 1. 거래대금 상위 종목 조회 (1회 API 호출로 200종목 획득!)
        top_stocks = await adapter.market_service.get_top_volume_stocks(
            market="0",  # 0:전체
            count=count
        )
        
        logger.info(f"Fetched {len(top_stocks)} top volume stocks")
        
        # 2. 각 종목의 52주 최고/최저가 계산
        for idx, stock_info in enumerate(top_stocks, 1):
            try:
                symbol = stock_info["symbol"]
                logger.info(f"[{idx}/{len(top_stocks)}] Processing {symbol} ({stock_info['name']})...")
                
                # 52주 최고/최저가 계산 (최근 1년 일봉)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                ohlc_list = await adapter.get_ohlc(
                    symbol=symbol,
                    interval="1d",
                    start_date=start_date,
                    end_date=end_date
                )
                
                if ohlc_list:
                    high_52w = max([o.high for o in ohlc_list])
                    low_52w = min([o.low for o in ohlc_list])
                    current_price = ohlc_list[-1].close  # 최근 종가
                    price_position = current_price / high_52w if high_52w > 0 else 0
                else:
                    high_52w = stock_info["price"]
                    low_52w = stock_info["price"]
                    current_price = stock_info["price"]
                    price_position = 1.0
                
                # DB 저장
                stock = StockMasterModel(
                    symbol=symbol,
                    name=stock_info["name"],
                    market="KOSPI" if stock_info.get("market") == "1" else "KOSDAQ",
                    sector=None,
                    current_price=current_price,
                    volume_amount=stock_info["volume_amount"],
                    high_52w=high_52w,
                    low_52w=low_52w,
                    price_position=price_position,
                    is_active=True,
                    updated_at=datetime.now()
                )
                
                session.merge(stock)
                session.commit()
                
                logger.info(
                    f"✓ {symbol} ({stock_info['name']}): "
                    f"₩{current_price:,.0f}, "
                    f"거래대금 {stock_info['volume_amount']/100000000:.0f}억, "
                    f"위치 {price_position:.1%}"
                )
                
                # API Rate Limit 고려 (t8451: 초당 1건)
                await asyncio.sleep(1.1)  # 1.1초 대기
            
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {e}")
                continue
    
    session.close()
    logger.info("Stock master update completed")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="종목 마스터 업데이트")
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="거래대금 상위 종목 수 (기본: 200)"
    )
    
    args = parser.parse_args()
    
    # 거래대금 상위 종목으로 업데이트 (최적화)
    await update_stock_master_from_top_volume(count=args.count)


if __name__ == "__main__":
    asyncio.run(main())
