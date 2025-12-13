#!/usr/bin/env python3
"""
백테스트 자산 곡선 디버깅 테스트
"""

import asyncio
import httpx
import json

async def test_backtest_with_debug():
    """백테스트 실행 및 결과 확인"""
    
    print("🔍 백테스트 자산 곡선 디버깅 테스트")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 로그인
        login_response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 단일 종목 백테스트 실행
        print("\n1️⃣ 단일 종목 백테스트 실행")
        backtest_request = {
            "strategy_name": "MACrossStrategy",
            "parameters": {"fast_period": 5, "slow_period": 20},
            "symbol": "005930",
            "start_date": "2025-08-14T00:00:00",
            "end_date": "2025-11-21T00:00:00",
            "initial_capital": 10000000,
            "commission": 0.0015,
            "slippage": 0.0005
        }
        
        backtest_response = await client.post(
            "http://localhost:8000/api/backtest/run",
            headers=headers,
            json=backtest_request
        )
        
        if backtest_response.status_code == 200:
            result = backtest_response.json()
            backtest_id = result['backtest_id']
            
            print(f"   ✅ 백테스트 성공 (ID: {backtest_id})")
            print(f"     Total Return: {result['total_return']:.2%}")
            print(f"     Total Trades: {result['total_trades']}")
            
            # 상세 결과 조회
            print(f"\n2️⃣ 백테스트 결과 상세 조회 (ID: {backtest_id})")
            
            detail_response = await client.get(
                f"http://localhost:8000/api/backtest/results/{backtest_id}",
                headers=headers
            )
            
            if detail_response.status_code == 200:
                detail = detail_response.json()
                
                print(f"   ✅ 상세 조회 성공")
                print(f"     Equity Curve Points: {len(detail.get('equity_curve', []))}")
                print(f"     Equity Timestamps: {len(detail.get('equity_timestamps', []))}")
                print(f"     Symbol Performances: {len(detail.get('symbol_performances', []))}")
                
                # 자산 곡선 샘플 출력
                equity_curve = detail.get('equity_curve', [])
                if equity_curve:
                    print(f"     First Equity: {equity_curve[0]:,.0f}")
                    print(f"     Last Equity: {equity_curve[-1]:,.0f}")
                else:
                    print("     ❌ 자산 곡선 데이터 없음")
                
                # 타임스탬프 샘플 출력
                equity_timestamps = detail.get('equity_timestamps', [])
                if equity_timestamps:
                    print(f"     First Timestamp: {equity_timestamps[0]}")
                    print(f"     Last Timestamp: {equity_timestamps[-1]}")
                else:
                    print("     ❌ 타임스탬프 데이터 없음")
                
                # 종목별 성과 출력
                symbol_performances = detail.get('symbol_performances', [])
                if symbol_performances:
                    print(f"     Symbol Performances:")
                    for sp in symbol_performances:
                        print(f"       - {sp['symbol']} ({sp['name']}): {sp['total_return']:.2%}, {sp['trade_count']} trades")
                else:
                    print("     ❌ 종목별 성과 데이터 없음")
                
            else:
                print(f"   ❌ 상세 조회 실패: {detail_response.status_code}")
                print(f"     Error: {detail_response.text}")
        
        else:
            print(f"   ❌ 백테스트 실패: {backtest_response.status_code}")
            print(f"     Error: {backtest_response.text}")

async def main():
    await test_backtest_with_debug()

if __name__ == "__main__":
    asyncio.run(main())