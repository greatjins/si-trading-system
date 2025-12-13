#!/usr/bin/env python3
"""
API 응답 직접 확인
"""

import asyncio
import httpx
import json

async def test_api_response():
    """API 응답 직접 확인"""
    
    print("🔍 API 응답 직접 확인")
    print("=" * 40)
    
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
        
        # 백테스트 ID 104 결과 조회
        backtest_id = 104
        
        print(f"\n📊 백테스트 결과 조회 (ID: {backtest_id})")
        
        detail_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            detail = detail_response.json()
            
            # 전체 응답 구조 출력
            print(f"\n📋 응답 구조:")
            for key, value in detail.items():
                if isinstance(value, list):
                    print(f"  {key}: {type(value).__name__} (length: {len(value)})")
                    if len(value) > 0:
                        print(f"    First item: {value[0]}")
                else:
                    print(f"  {key}: {type(value).__name__} = {value}")
            
            # 자산 곡선 상세 확인
            equity_curve = detail.get('equity_curve')
            if equity_curve:
                print(f"\n💰 Equity Curve 상세:")
                print(f"  Length: {len(equity_curve)}")
                print(f"  First 5: {equity_curve[:5]}")
                print(f"  Last 5: {equity_curve[-5:]}")
            
            # 타임스탬프 상세 확인
            equity_timestamps = detail.get('equity_timestamps')
            if equity_timestamps:
                print(f"\n⏰ Equity Timestamps 상세:")
                print(f"  Length: {len(equity_timestamps)}")
                print(f"  First 3: {equity_timestamps[:3]}")
                print(f"  Last 3: {equity_timestamps[-3:]}")
            
            # 종목별 성과 상세 확인
            symbol_performances = detail.get('symbol_performances')
            if symbol_performances:
                print(f"\n📈 Symbol Performances 상세:")
                print(f"  Length: {len(symbol_performances)}")
                for sp in symbol_performances:
                    print(f"    {sp}")
        
        else:
            print(f"Error: {detail_response.text}")

if __name__ == "__main__":
    asyncio.run(test_api_response())