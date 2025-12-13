#!/usr/bin/env python3
"""
실시간 백테스트 결과 디버깅
"""

import asyncio
import httpx
import json

async def test_realtime_debug():
    """실시간 백테스트 결과 디버깅"""
    
    print("🔍 실시간 백테스트 결과 디버깅")
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
        
        # 화면에 표시된 삼성전자 종목 상세 조회 (005930)
        backtest_id = 107  # 현재 화면의 백테스트 ID
        symbol = "005930"  # 삼성전자
        
        print(f"\n📊 삼성전자 종목 상세 조회 (백테스트 ID: {backtest_id})")
        
        # 1. 전체 백테스트 결과 확인
        result_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}",
            headers=headers
        )
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            
            print(f"\n📈 전체 결과 요약:")
            print(f"  전략명: {result_data.get('strategy_name')}")
            print(f"  수익률: {result_data.get('total_return', 0)*100:.2f}%")
            print(f"  총 거래: {result_data.get('total_trades')}회")
            
            # 자산곡선 데이터 확인
            equity_curve = result_data.get('equity_curve', [])
            equity_timestamps = result_data.get('equity_timestamps', [])
            
            print(f"\n💰 자산곡선 데이터:")
            print(f"  포인트 수: {len(equity_curve)}")
            print(f"  타임스탬프 수: {len(equity_timestamps)}")
            
            if len(equity_curve) > 0:
                print(f"  시작 자산: {equity_curve[0]:,.0f}원")
                print(f"  최종 자산: {equity_curve[-1]:,.0f}원")
                print(f"  첫 3개 포인트: {equity_curve[:3]}")
                print(f"  마지막 3개 포인트: {equity_curve[-3:]}")
            
            if len(equity_timestamps) > 0:
                print(f"  시작일: {equity_timestamps[0]}")
                print(f"  종료일: {equity_timestamps[-1]}")
            
            # 종목별 성과 확인
            symbol_performances = result_data.get('symbol_performances', [])
            print(f"\n📊 종목별 성과:")
            print(f"  종목 수: {len(symbol_performances)}")
            
            for i, perf in enumerate(symbol_performances):
                print(f"  {i+1}. {perf.get('name')} ({perf.get('symbol')})")
                print(f"     수익률: {perf.get('total_return', 0):.2f}%")
                print(f"     거래횟수: {perf.get('trade_count')}회")
                print(f"     승률: {perf.get('win_rate', 0):.1f}%")
        
        # 2. 삼성전자 종목 상세 조회
        print(f"\n🔍 삼성전자 종목 상세 조회")
        
        symbol_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}/symbols/{symbol}",
            headers=headers
        )
        
        if symbol_response.status_code == 200:
            symbol_data = symbol_response.json()
            
            print(f"  종목명: {symbol_data.get('name')}")
            print(f"  수익률: {symbol_data.get('total_return', 0):.2f}%")
            print(f"  거래횟수: {symbol_data.get('trade_count')}회")
            
            # 완결된 거래 확인
            completed_trades = symbol_data.get('completed_trades', [])
            print(f"  완결된 거래: {len(completed_trades)}건")
            
            if len(completed_trades) > 0:
                print(f"  첫 번째 거래:")
                first_trade = completed_trades[0]
                print(f"    진입일: {first_trade.get('entry_date')}")
                print(f"    진입가: {first_trade.get('entry_price'):,.0f}원")
                print(f"    청산일: {first_trade.get('exit_date')}")
                print(f"    청산가: {first_trade.get('exit_price'):,.0f}원")
                print(f"    손익: {first_trade.get('pnl'):,.0f}원")
                print(f"    수익률: {first_trade.get('return_pct'):.2f}%")
        
        # 3. OHLC 데이터 확인
        print(f"\n📈 삼성전자 OHLC 데이터 확인")
        
        ohlc_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}/ohlc/{symbol}",
            headers=headers
        )
        
        if ohlc_response.status_code == 200:
            ohlc_data = ohlc_response.json()
            
            print(f"  OHLC 데이터 포인트: {len(ohlc_data)}개")
            
            if len(ohlc_data) > 0:
                first_ohlc = ohlc_data[0]
                last_ohlc = ohlc_data[-1]
                
                print(f"  첫 번째 데이터:")
                print(f"    날짜: {first_ohlc.get('timestamp')}")
                print(f"    시가: {first_ohlc.get('open'):,.0f}원")
                print(f"    고가: {first_ohlc.get('high'):,.0f}원")
                print(f"    저가: {first_ohlc.get('low'):,.0f}원")
                print(f"    종가: {first_ohlc.get('close'):,.0f}원")
                
                print(f"  마지막 데이터:")
                print(f"    날짜: {last_ohlc.get('timestamp')}")
                print(f"    종가: {last_ohlc.get('close'):,.0f}원")

if __name__ == "__main__":
    asyncio.run(test_realtime_debug())