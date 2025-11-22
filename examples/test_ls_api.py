"""
LS증권 API 테스트
"""
import asyncio
from datetime import datetime, timedelta

from broker.ls.adapter import LSAdapter
from broker.ls.services import LSAccountService, LSOrderService, LSMarketService
from broker.ls.client import LSClient


async def test_account_api():
    """계좌 API 테스트"""
    print("=" * 80)
    print("LS증권 계좌 API 테스트")
    print("=" * 80)
    print()
    
    try:
        # LSAdapter 사용
        async with LSAdapter() as adapter:
            # 1. 계좌 정보 조회
            print("1. 계좌 정보 조회...")
            account = await adapter.get_account()
            print(f"   ✅ 계좌번호: {account.account_id}")
            print(f"   ✅ 예수금: {account.balance:,.0f}원")
            print(f"   ✅ 총 자산: {account.equity:,.0f}원")
            print()
            
            # 2. 보유 종목 조회
            print("2. 보유 종목 조회...")
            positions = await adapter.get_positions()
            print(f"   ✅ 보유 종목 수: {len(positions)}개")
            
            for pos in positions:
                print(f"      - {pos.symbol}: {pos.quantity}주 @ {pos.avg_price:,.0f}원")
                print(f"        평가손익: {pos.unrealized_pnl:+,.0f}원")
            print()
    
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        print()


async def test_market_api():
    """시세 API 테스트"""
    print("=" * 80)
    print("LS증권 시세 API 테스트")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            market_service = LSMarketService(client)
            
            # 1. 현재가 조회
            print("1. 현재가 조회 (삼성전자)...")
            quote = await market_service.get_current_price("005930")
            print(f"   ✅ 종목명: {quote.name}")
            print(f"   ✅ 현재가: {quote.price:,.0f}원")
            print(f"   ✅ 등락률: {quote.change_percent:+.2f}%")
            print(f"   ✅ 거래량: {quote.volume:,}주")
            print()
            
            # 2. 호가 조회
            print("2. 호가 조회...")
            orderbook = await market_service.get_orderbook("005930")
            print(f"   ✅ 매도 호가 1단계: {orderbook.ask_prices[0].price:,.0f}원 ({orderbook.ask_prices[0].quantity:,}주)")
            print(f"   ✅ 매수 호가 1단계: {orderbook.bid_prices[0].price:,.0f}원 ({orderbook.bid_prices[0].quantity:,}주)")
            print()
            
            # 3. 일봉 조회
            print("3. 일봉 조회 (최근 5일)...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            ohlc_list = await market_service.get_ohlc_daily("005930", start_date, end_date)
            print(f"   ✅ 데이터 수: {len(ohlc_list)}개")
            
            for ohlc in ohlc_list[-5:]:
                print(f"      {ohlc.timestamp.strftime('%Y-%m-%d')}: "
                      f"시가 {ohlc.open:,.0f} / 고가 {ohlc.high:,.0f} / "
                      f"저가 {ohlc.low:,.0f} / 종가 {ohlc.close:,.0f}")
            print()
            
            # 4. 종목 검색
            print("4. 종목 검색 (삼성)...")
            results = await market_service.search_stock("삼성")
            print(f"   ✅ 검색 결과: {len(results)}개")
            
            for result in results[:5]:
                print(f"      - {result['symbol']}: {result['name']}")
            print()
    
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        print()


async def test_order_api():
    """주문 API 테스트 (주의: 실제 주문 실행됨!)"""
    print("=" * 80)
    print("LS증권 주문 API 테스트")
    print("=" * 80)
    print()
    print("⚠️  주의: 이 테스트는 실제 주문을 실행합니다!")
    print("⚠️  테스트 계좌 또는 모의투자 계좌에서만 실행하세요!")
    print()
    
    # 안전을 위해 주석 처리
    print("   ℹ️  주문 테스트는 안전을 위해 비활성화되어 있습니다.")
    print("   ℹ️  실제 테스트를 원하시면 코드의 주석을 해제하세요.")
    print()
    
    # try:
    #     async with LSAdapter() as adapter:
    #         # 1. 주문 실행 (매수)
    #         print("1. 주문 실행 (매수 1주)...")
    #         order_id = await adapter.place_order(
    #             symbol="005930",
    #             side="buy",
    #             quantity=1,
    #             order_type="limit",
    #             price=70000  # 낮은 가격으로 체결 방지
    #         )
    #         print(f"   ✅ 주문번호: {order_id}")
    #         print()
    #         
    #         # 2. 주문 조회
    #         print("2. 주문 조회...")
    #         order = await adapter.order_service.get_order(adapter.account_id, order_id)
    #         print(f"   ✅ 주문 상태: {order.status.value}")
    #         print(f"   ✅ 주문 수량: {order.quantity}주")
    #         print(f"   ✅ 체결 수량: {order.filled_quantity}주")
    #         print()
    #         
    #         # 3. 주문 취소
    #         print("3. 주문 취소...")
    #         success = await adapter.cancel_order(order_id)
    #         print(f"   ✅ 취소 {'성공' if success else '실패'}")
    #         print()
    # 
    # except Exception as e:
    #     print(f"   ❌ 테스트 실패: {e}")
    #     print()


async def test_adapter_integration():
    """LSAdapter 통합 테스트"""
    print("=" * 80)
    print("LSAdapter 통합 테스트")
    print("=" * 80)
    print()
    
    try:
        async with LSAdapter() as adapter:
            # 1. OHLC 조회 (BrokerBase 인터페이스)
            print("1. OHLC 조회 (일봉)...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            ohlc_list = await adapter.get_ohlc("005930", "1d", start_date, end_date)
            print(f"   ✅ 데이터 수: {len(ohlc_list)}개")
            print(f"   ✅ 최근 종가: {ohlc_list[-1].close:,.0f}원")
            print()
            
            # 2. 계좌 정보
            print("2. 계좌 정보...")
            account = await adapter.get_account()
            print(f"   ✅ 총 자산: {account.equity:,.0f}원")
            print()
            
            # 3. 포지션 정보
            print("3. 포지션 정보...")
            positions = await adapter.get_positions()
            print(f"   ✅ 보유 종목: {len(positions)}개")
            print()
            
            print("✅ 통합 테스트 완료!")
            print()
    
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        print()


async def main():
    """메인 함수"""
    print("\n")
    print("🚀 LS증권 API 테스트")
    print()
    print("⚠️  주의: config.yaml에 LS증권 API 키 설정이 필요합니다:")
    print()
    print("ls:")
    print("  appkey: \"YOUR_APPKEY\"")
    print("  appsecretkey: \"YOUR_APPSECRETKEY\"")
    print("  account_id: \"YOUR_ACCOUNT_ID\"")
    print()
    print("-" * 80)
    print()
    
    # 테스트 실행
    await test_account_api()
    await test_market_api()
    await test_order_api()
    await test_adapter_integration()
    
    print("=" * 80)
    print("✅ 모든 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
