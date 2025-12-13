#!/usr/bin/env python3
"""
디버그 API 응답 확인
"""

import asyncio
import httpx
import json

async def test_debug_api():
    """디버그 API 응답 확인"""
    
    print("🔍 디버그 API 응답 확인")
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
        
        # 디버그 엔드포인트 호출
        backtest_id = 104
        
        print(f"\n📊 디버그 엔드포인트 호출 (ID: {backtest_id})")
        
        debug_response = await client.get(
            f"http://localhost:8000/api/backtest/debug/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {debug_response.status_code}")
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            
            print(f"\n📋 디버그 응답:")
            for key, value in debug_data.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_debug_api())