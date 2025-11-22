"""
LSAdapter 사용 예제 (Mock 모드)
"""
import asyncio
from datetime import datetime, timedelta

from broker.ls.adapter import LSAdapter
from utils.types import Order, OrderSide, OrderType, OrderStatus


async def main():
    print("=" * 60)
    print("LSAdapter 테스트 (Mock 모드)")
    print("=" * 60)
    
    # LSAdapter 초기화 (Mock 인증)
    adapter = LSAdapter(
        api_key="MOCK_API_KEY",
        api_secret="MOCK_API_SECRET",
        account_id="MOCK_ACCOUNT"
    )
    
    async with adapter:
        print(f"\n✓ LSAdapter 초기화 완료")
        
        # 계좌 정보 조회
        print(f"\n[계좌 정보]")
        account = await adapter.get_account()
        print(f"  - 계좌번호: {account.account_id}")
        print(f"  - 잔액: {account.balance:,.0f}원")
        print(f"  - 자산: {account.equity:,.0f}원")
        
        # OHLC 데이터 조회 (Mock)
        print(f"\n[OHLC 데이터 조회]")
        symbol = "005930"
        print(f"  - 종목: {symbol}")
        print(f"  - 상태: Mock 모드 (실제 API 구현 필요)")
        
        # 현재가 조회
        print(f"\n[현재가 조회]")
        print(f"  - 상태: Mock 모드 (실제 API 구현 필요)")
        
        # 주문 제출 (Mock)
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
        
        order_id = await adapter.place_order(order)
        print(f"  - 주문 ID: {order_id}")
        print(f"  - 상태: Mock 모드")
        
        # 포지션 조회
        print(f"\n[보유 포지션]")
        positions = await adapter.get_positions()
        print(f"  - 포지션 수: {len(positions)}개")
        print(f"  - 상태: Mock 모드")
        
        # 미체결 주문 조회
        print(f"\n[미체결 주문]")
        open_orders = await adapter.get_open_orders()
        print(f"  - 미체결 주문 수: {len(open_orders)}개")
        print(f"  - 상태: Mock 모드")
    
    print(f"\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n⚠️  주의: 현재 Mock 모드로 동작합니다.")
    print("실제 LS증권 API를 사용하려면 다음을 구현해야 합니다:")
    print("  1. broker/ls/client.py - 실제 인증 로직")
    print("  2. broker/ls/ohlc.py - 실제 OHLC API 호출")
    print("  3. broker/ls/order.py - 실제 주문 API 호출")
    print("  4. broker/ls/account.py - 실제 계좌 API 호출")
    print("  5. broker/ls/realtime.py - 실제 WebSocket 연결")


if __name__ == "__main__":
    asyncio.run(main())
