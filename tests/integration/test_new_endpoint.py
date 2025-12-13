#!/usr/bin/env python3
"""
새로운 엔드포인트 테스트
"""

import asyncio
import httpx
import json

async def test_new_endpoint():
    """새로운 엔드포인트 테스트"""
    
    print("🔍 새로운 엔드포인트 테스트")
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
        
        # 새로운 엔드포인트 호출
        backtest_id = 104
        
        print(f"\n📊 새로운 엔드포인트 호출 (ID: {backtest_id})")
        
        new_response = await client.get(
            f"http://localhost:8000/api/backtest/results-new/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {new_response.status_code}")
        
        if new_response.status_code == 200:
            new_data = new_response.json()
            
            print(f"\n📋 새로운 엔드포인트 응답 구조:")
            for key, value in new_data.items():
                if isinstance(value, list):
                    print(f"  {key}: {type(value).__name__} (length: {len(value)})")
                    if len(value) > 0 and key in ['equity_curve', 'equity_timestamps', 'symbol_performances']:
                        print(f"    Sample: {value[:2]}")
                else:
                    print(f"  {key}: {type(value).__name__} = {value}")
        else:
            print(f"Error: {new_response.text}")

if __name__ == "__main__":
    asyncio.run(test_new_endpoint())