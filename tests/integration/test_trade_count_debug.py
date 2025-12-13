#!/usr/bin/env python3
"""
거래횟수 차이 디버깅 테스트
"""

import asyncio
import httpx

async def debug_trade_count():
    """거래횟수 차이 디버깅"""
    
    print("🔍 거래횟수 차이 디버깅")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 로그인
        login_response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 백테스트 목록에서 첫 번째 항목 조회
        list_response = await client.get(
            "http://localhost:8000/api/backtest/results?limit=1",
            headers=headers
        )
        
        if list_response.status_code == 200:
            backtests = list_response.json()
            if backtests:
                backtest = backtests[0]
                backtest_id = backtest['backtest_id']
                
                print(f"📊 백테스트 ID: {backtest_id}")
                print(f"전략명: {backtest['strategy_name']}")
                print(f"목록에서 총 거래: {backtest['total_trades']}회")
                
                # 상세 결과 조회
                detail_response = await client.get(
                    f"http://localhost:8000/api/backtest/results/{backtest_id}",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    
                    print(f"\n📈 상세보기 결과:")
                    print(f"총 거래: {detail['total_trades']}회")
                    
                    symbol_performances = detail.get('symbol_performances', [])
                    print(f"\n🏢 종목별 성과:")
                    
                    total_symbol_trades = 0
                    for perf in symbol_performances:
                        print(f"  {perf['symbol']} ({perf['name']}): {perf['trade_count']}회 완결된 거래")
                        total_symbol_trades += perf['trade_count']
                    
                    print(f"\n📊 분석:")
                    print(f"  - 백테스트 엔진 total_trades: {detail['total_trades']}회 (모든 개별 거래)")
                    print(f"  - 종목별 완결된 거래 합계: {total_symbol_trades}회 (매수→매도 쌍)")
                    print(f"  - 차이: {detail['total_trades'] - total_symbol_trades * 2}회")
                    
                    if detail['total_trades'] == total_symbol_trades * 2:
                        print("  ✅ 정상: 개별 거래 = 완결된 거래 × 2")
                    else:
                        print("  ⚠️ 불일치: 추가 조사 필요")
                        
                        # 실제 거래 내역 확인
                        from data.repository import get_db_session
                        from data.models import TradeModel
                        
                        db = get_db_session()
                        try:
                            trades = db.query(TradeModel).filter(
                                TradeModel.backtest_id == backtest_id
                            ).all()
                            
                            print(f"\n🔍 실제 DB 거래 내역:")
                            print(f"  - DB에 저장된 거래: {len(trades)}회")
                            
                            buy_count = len([t for t in trades if t.side == 'BUY'])
                            sell_count = len([t for t in trades if t.side == 'SELL'])
                            
                            print(f"  - 매수 거래: {buy_count}회")
                            print(f"  - 매도 거래: {sell_count}회")
                            print(f"  - 합계: {buy_count + sell_count}회")
                            
                        finally:
                            db.close()
                else:
                    print(f"❌ 상세 결과 조회 실패: {detail_response.text}")
            else:
                print("백테스트 목록이 비어있습니다.")
        else:
            print(f"❌ 백테스트 목록 조회 실패: {list_response.text}")

if __name__ == "__main__":
    asyncio.run(debug_trade_count())