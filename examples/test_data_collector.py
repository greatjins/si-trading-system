"""
DataCollector 사용 예제
"""
import asyncio
from datetime import datetime, timedelta

from broker.mock.adapter import MockBroker
from data.storage import FileStorage
from data.collector import DataCollector


async def main():
    print("=" * 60)
    print("DataCollector 테스트")
    print("=" * 60)
    
    # 브로커 및 저장소 초기화
    broker = MockBroker(initial_balance=10_000_000)
    storage = FileStorage(base_path="data/ohlc")
    
    # 데이터 수집기 초기화
    collector = DataCollector(
        broker=broker,
        storage=storage
    )
    
    print(f"\n✓ DataCollector 초기화 완료")
    
    # OHLC 데이터 수집
    print(f"\n[OHLC 데이터 수집]")
    symbol = "005930"
    interval = "1d"
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    print(f"  - 종목: {symbol}")
    print(f"  - 기간: {start_date.date()} ~ {end_date.date()}")
    
    # 첫 번째 호출 (브로커에서 가져오기)
    print(f"\n  [첫 번째 호출 - 브로커에서 가져오기]")
    data1 = await collector.get_ohlc(symbol, interval, start_date, end_date)
    print(f"    데이터 수: {len(data1)}개")
    
    if data1:
        latest = data1[-1]
        print(f"    최근 종가: {latest.close:,.0f}원")
    
    # 두 번째 호출 (저장소에서 가져오기)
    print(f"\n  [두 번째 호출 - 저장소에서 가져오기]")
    data2 = await collector.get_ohlc(symbol, interval, start_date, end_date)
    print(f"    데이터 수: {len(data2)}개")
    print(f"    ✓ 캐시 히트!")
    
    # 현재가 조회
    print(f"\n[현재가 조회]")
    price = await collector.get_current_price(symbol)
    print(f"  - {symbol}: {price:,.0f}원")
    
    # 저장소 정보
    print(f"\n[저장소 정보]")
    info = collector.get_storage_info()
    print(f"  - 저장된 종목 수: {info['symbols_count']}개")
    print(f"  - 저장소 크기: {info['size_mb']} MB")
    
    if info['symbols']:
        print(f"  - 종목 목록: {', '.join(info['symbols'])}")
    
    # 캐시 새로고침
    print(f"\n[캐시 새로고침]")
    success = await collector.refresh_cache(symbol, interval, start_date, end_date)
    if success:
        print(f"  ✓ 캐시 새로고침 완료")
    
    print(f"\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print(f"\n💡 데이터는 'data/ohlc' 디렉토리에 저장됩니다.")


if __name__ == "__main__":
    asyncio.run(main())
