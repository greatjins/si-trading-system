"""
LS증권 주문 실행 테스트
"""
import asyncio
from broker.ls.client import LSClient
from broker.ls.services.order import LSOrderService


async def test_place_order():
    """주문 실행 테스트 (모의투자)"""
    print("=" * 80)
    print("LS증권 주문 실행 테스트")
    print("=" * 80)
    print()
    
    print("⚠️  주의: 모의투자 계정에서 실행됩니다.")
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 주문 서비스 생성
            order_service = LSOrderService(client)
            
            # 매수 주문 (삼성전자)
            print("매수 주문 실행 중... (삼성전자 1주)")
            order_id = await order_service.place_order(
                account_id=client.account_id,
                symbol="005930",  # 삼성전자
                side="buy",
                quantity=1,
                order_type="limit",
                price=70000
            )
            
            print(f"✅ 주문번호: {order_id}")
            print()
    
    except Exception as e:
        print(f"❌ 주문 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def test_get_orders():
    """주문 내역 조회 테스트"""
    print("=" * 80)
    print("LS증권 주문 내역 조회")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 주문 서비스 생성
            order_service = LSOrderService(client)
            
            # 주문 내역 조회
            print("주문 내역 조회 중...")
            orders = await order_service.get_orders(client.account_id)
            
            if not orders:
                print("주문 내역이 없습니다.")
            else:
                print(f"✅ 주문 내역: {len(orders)}건")
                print()
                
                for order in orders:
                    print(f"주문번호: {order.order_id}")
                    print(f"  종목: {order.symbol}")
                    print(f"  구분: {order.side}")
                    print(f"  수량: {order.quantity}주")
                    print(f"  가격: {order.price:,.0f}원")
                    print(f"  상태: {order.status}")
                    print()
    
    except Exception as e:
        print(f"❌ 주문 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def test_modify_order():
    """주문 정정 테스트"""
    print("=" * 80)
    print("LS증권 주문 정정 테스트")
    print("=" * 80)
    print()
    
    print("⚠️  주의: 실제 주문이 있어야 정정이 가능합니다.")
    print("⚠️  테스트를 위해서는 먼저 주문을 실행하세요.")
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 주문 서비스 생성
            order_service = LSOrderService(client)
            
            # 주문 정정 (예시)
            # order_id = "12345"  # 실제 주문번호
            # new_order_id = await order_service.modify_order(
            #     account_id=client.account_id,
            #     order_id=order_id,
            #     symbol="005930",
            #     quantity=2,
            #     price=71000
            # )
            # print(f"✅ 정정주문번호: {new_order_id}")
            
            print("ℹ️  주문 정정 테스트는 실제 주문이 필요하여 비활성화되어 있습니다.")
            print()
    
    except Exception as e:
        print(f"❌ 주문 정정 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def main():
    """메인 함수"""
    print("\n")
    print("📝 LS증권 주문 실행 테스트")
    print()
    print("-" * 80)
    print()
    
    # await test_place_order()
    await test_get_orders()
    # await test_modify_order()
    
    print("=" * 80)
    print("✅ 주문 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
