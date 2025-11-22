"""
LS증권 시세 조회 테스트
"""
import asyncio
from broker.ls.client import LSClient
from broker.ls.services.market import LSMarketService


async def test_current_price():
    """현재가 조회 테스트"""
    print("=" * 80)
    print("LS증권 현재가 조회")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 시세 서비스 생성
            market_service = LSMarketService(client)
            
            # 현재가 조회 (삼성전자)
            print("현재가 조회 중... (삼성전자)")
            quote = await market_service.get_current_price("005930")
            
            print(f"✅ 종목코드: {quote.symbol}")
            print(f"✅ 종목명: {quote.name}")
            print(f"✅ 현재가: {quote.price:,.0f}원")
            print(f"✅ 전일대비: {quote.change:+,.0f}원 ({quote.change_rate:+.2f}%)")
            print(f"✅ 거래량: {quote.volume:,}주")
            print()
    
    except Exception as e:
        print(f"❌ 현재가 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def test_orderbook():
    """호가 조회 테스트"""
    print("=" * 80)
    print("LS증권 호가 조회")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 시세 서비스 생성
            market_service = LSMarketService(client)
            
            # 호가 조회 (삼성전자)
            print("호가 조회 중... (삼성전자)")
            orderbook = await market_service.get_orderbook("005930")
            
            print(f"✅ 종목코드: {orderbook.symbol}")
            print()
            print("매도 호가:")
            for i, (price, qty) in enumerate(zip(orderbook.ask_prices[:5], orderbook.ask_volumes[:5]), 1):
                print(f"  {i}. {price:>8,}원 x {qty:>8,}주")
            print()
            print("매수 호가:")
            for i, (price, qty) in enumerate(zip(orderbook.bid_prices[:5], orderbook.bid_volumes[:5]), 1):
                print(f"  {i}. {price:>8,}원 x {qty:>8,}주")
            print()
    
    except Exception as e:
        print(f"❌ 호가 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def main():
    """메인 함수"""
    print("\n")
    print("📊 LS증권 시세 조회 테스트")
    print()
    print("-" * 80)
    print()
    
    await test_current_price()
    # await test_orderbook()
    
    print("=" * 80)
    print("✅ 시세 조회 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
