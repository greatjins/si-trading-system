#!/usr/bin/env python3
"""
새로운 백테스트 실행 및 결과 조회
"""

import asyncio
import httpx
import json

async def test_new_backtest():
    """새로운 백테스트 실행 및 결과 조회"""
    
    print("🔍 새로운 백테스트 실행 및 결과 조회")
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
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 새로운 백테스트 실행
        print("\n📊 새로운 백테스트 실행")
        
        backtest_request = {
            "strategy_name": "MACrossStrategy",
            "parameters": {
                "fast_period": 5,
                "slow_period": 20
            },
            "start_date": "2025-08-14",
            "end_date": "2025-11-21",
            "initial_capital": 10000000,
            "symbols": ["005930"]
        }
        
        backtest_response = await client.post(
            "http://localhost:8000/api/backtest/run",
            headers=headers,
            json=backtest_request
        )
        
        print(f"Backtest Status: {backtest_response.status_code}")
        
        if backtest_response.status_code == 200:
            backtest_result = backtest_response.json()
            backtest_id = backtest_result["backtest_id"]
            print(f"New Backtest ID: {backtest_id}")
            
            # 결과 조회
            print(f"\n📋 백테스트 결과 조회 (ID: {backtest_id})")
            
            result_response = await client.get(
                f"http://localhost:8000/api/backtest/results/{backtest_id}",
                headers=headers
            )
            
            print(f"Result Status: {result_response.status_code}")
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                
                print(f"\n📈 결과 구조:")
                for key, value in result_data.items():
                    if isinstance(value, list):
                        print(f"  {key}: {type(value).__name__} (length: {len(value)})")
                        if len(value) > 0 and key in ['equity_curve', 'equity_timestamps']:
                            print(f"    Sample: {value[:3]}")
                    else:
                        print(f"  {key}: {type(value).__name__} = {value}")
            else:
                print(f"Error getting result: {result_response.text}")
        else:
            print(f"Error running backtest: {backtest_response.text}")

if __name__ == "__main__":
    asyncio.run(test_new_backtest())