"""
MockBroker 사용 예제
"""
import asyncio
from datetime import datetime, timedelta

from broker.mock.adapter import MockBroker
from utils.types import Order, OrderSide, OrderType, OrderStatus


async def main():
    print("=" * 60)
    print("MockBroker 테스트")
    print("=" * 60)
    
    # 브로커 초기화
    broker = MockBroker(initial_balance=10_000_000)
    print(f"\n✓ 브로커 초기화 완료 (잔액: 10,000,000원)")
    
    # 계좌 정보 조회
    account = await broker.get_account()
    print(f"\n[계좌 정보]")
    print(f"  - 계좌번호: {account.account_id}")
    print(f"  - 잔액: {account.balance:,.0f}원")
    print(f"  - 자산: {account.equity:,.0f}원")
    
    # OHLC 데이터 조회
    print(f"\n[OHLC 데이터 조회]")
    symbol = "005930"  # 삼성전자
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    ohlc_data = await broker.get_ohlc(
        symbol=symbol,
        interval="1d",
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"  - 종목: {symbol}")
    print(f"  - 기간: {start_date.date()} ~ {end_date.date()}")
    print(f"  - 데이터 수: {len(ohlc_data)}개")
    
    if ohlc_data:
        latest = ohlc_data[-1]
        print(f"\n  [최근 데이터]")
        print(f"    시가: {latest.open:,.0f}원")
        print(f"    고가: {latest.high:,.0f}원")
        print(f"    저가: {latest.low:,.0f}원")
        print(f"    종가: {latest.close:,.0f}원")
        print(f"    거래량: {latest.volume:,}주")
    
    # 현재가 조회
    current_price = await broker.get_current_price(symbol)
    print(f"\n[현재가]")
    print(f"  - {symbol}: {current_price:,.0f}원")
    
    # 주문 제출
    print(f"\n[주문 제출]")
    order = Order(
        order_id="",
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10,
        price=None,
        filled_quantity=0,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
    
    order_id = await broker.place_order(order)
    print(f"  - 주문 ID: {order_id}")
    print(f"  - 종목: {symbol}")
    print(f"  - 방향: {order.side.value}")
    print(f"  - 수량: {order.quantity}주")
    
    # 주문 체결 대기
    await asyncio.sleep(0.2)
    
    # 미체결 주문 조회
    open_orders = await broker.get_open_orders()
    print(f"\n[미체결 주문]")
    print(f"  - 미체결 주문 수: {len(open_orders)}개")
    
    # 포지션 조회
    positions = await broker.get_positions()
    print(f"\n[보유 포지션]")
    print(f"  - 포지션 수: {len(positions)}개")
    
    print(f"\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
