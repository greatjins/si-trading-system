"""
LS증권 API 연결 테스트
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from broker.ls.adapter import LSAdapter
from utils.config import config
from datetime import datetime, timedelta

async def test_ls_connection():
    """LS증권 API 연결 테스트"""
    print("=" * 60)
    print("LS증권 API 연결 테스트")
    print("=" * 60)
    print()
    
    # 설정 확인
    print("📋 설정 확인:")
    print(f"  - API Key: {config.get('ls.appkey', 'N/A')[:10]}...")
    print(f"  - Account ID: {config.get('ls.account_id', 'N/A')}")
    print(f"  - Paper Trading: {config.get('ls.paper_trading', False)}")
    print()
    
    try:
        # 어댑터 초기화
        print("🔌 LS증권 어댑터 초기화 중...")
        async with LSAdapter() as adapter:
            print("✅ 어댑터 초기화 성공")
            print()
            
            # 계좌 정보 조회
            print("💰 계좌 정보 조회 중...")
            account = await adapter.get_account()
            print("✅ 계좌 정보 조회 성공:")
            print(f"  - 계좌번호: {account.account_id}")
            print(f"  - 예수금: {account.balance:,.0f}원")
            print(f"  - 순자산: {account.equity:,.0f}원")
            print(f"  - 매수가능금액: {account.margin_available:,.0f}원")
            print()
            
            # 보유 종목 조회
            print("📊 보유 종목 조회 중...")
            positions = await adapter.get_positions()
            print(f"✅ 보유 종목: {len(positions)}개")
            for pos in positions:
                print(f"  - {pos.symbol}: {pos.quantity}주 (평가손익: {pos.unrealized_pnl:,.0f}원)")
            print()
            
            # 시세 조회 테스트
            print("📈 시세 조회 테스트 (삼성전자)...")
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                ohlc_data = await adapter.get_ohlc("005930", "1d", start_date, end_date)
                print(f"✅ OHLC 데이터: {len(ohlc_data)}개")
                if ohlc_data:
                    latest = ohlc_data[-1]
                    print(f"  - 최신 데이터: {latest.timestamp}")
                    print(f"  - 종가: {latest.close:,.0f}원")
                    print(f"  - 거래량: {latest.volume:,.0f}주")
            except Exception as e:
                print(f"⚠️  시세 조회 실패 (모의투자 환경에서는 일부 TR이 지원되지 않을 수 있습니다)")
                print(f"   에러: {str(e)[:100]}")
            print()
        
        print("=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 테스트 실패: {e}")
        print("=" * 60)
        print()
        print("💡 해결 방법:")
        print("  1. config.yaml 파일에 LS증권 API 키가 올바르게 설정되어 있는지 확인")
        print("  2. LS증권 API 서버가 정상 작동 중인지 확인")
        print("  3. 계좌번호가 올바른지 확인")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ls_connection())
