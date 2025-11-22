"""
LS증권 계좌 조회 테스트
"""
import asyncio
from broker.ls.client import LSClient
from broker.ls.services.account import LSAccountService


async def test_account_balance():
    """계좌 잔고 조회 테스트"""
    print("=" * 80)
    print("LS증권 계좌 잔고 조회")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 계좌 서비스 생성
            account_service = LSAccountService(client)
            
            # 계좌 잔고 조회
            print("계좌 잔고 조회 중...")
            balance = await account_service.get_account_balance(client.account_id)
            
            print(f"✅ 계좌번호: {balance.account_id}")
            print(f"✅ 총 자산(순자산): {balance.equity:,.0f}원")
            print(f"✅ 예수금: {balance.balance:,.0f}원")
            print(f"✅ 주식 평가액: {balance.stock_value:,.0f}원")
            print(f"✅ 평가 손익: {balance.profit_loss:,.0f}원")
            print(f"✅ 수익률: {balance.profit_loss_rate:.2f}%")
            print()
    
    except Exception as e:
        print(f"❌ 계좌 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def test_account_positions():
    """보유 종목 조회 테스트"""
    print("=" * 80)
    print("LS증권 보유 종목 조회")
    print("=" * 80)
    print()
    
    try:
        async with LSClient() as client:
            print(f"✅ 클라이언트 연결: {client.account_id}")
            print()
            
            # 계좌 서비스 생성
            account_service = LSAccountService(client)
            
            # 보유 종목 조회
            print("보유 종목 조회 중...")
            positions = await account_service.get_positions(client.account_id)
            
            if not positions:
                print("보유 종목이 없습니다.")
            else:
                print(f"✅ 보유 종목 수: {len(positions)}개")
                print()
                
                for pos in positions:
                    print(f"종목: {pos.symbol} ({pos.name})")
                    print(f"  수량: {pos.quantity}주")
                    print(f"  평균단가: {pos.average_price:,.0f}원")
                    print(f"  현재가: {pos.current_price:,.0f}원")
                    print(f"  평가액: {pos.market_value:,.0f}원")
                    print(f"  손익: {pos.profit_loss:,.0f}원 ({pos.profit_loss_rate:.2f}%)")
                    print()
    
    except Exception as e:
        print(f"❌ 보유 종목 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print()


async def main():
    """메인 함수"""
    print("\n")
    print("🏦 LS증권 계좌 조회 테스트")
    print()
    print("-" * 80)
    print()
    
    await test_account_balance()
    await test_account_positions()
    
    print("=" * 80)
    print("✅ 계좌 조회 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
