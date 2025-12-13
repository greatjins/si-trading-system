#!/usr/bin/env python3
"""
라우터 테스트
"""

import asyncio
import httpx

async def test_router():
    """라우터 테스트"""
    
    print("🔍 라우터 테스트")
    print("=" * 30)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
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
        
        # 테스트 엔드포인트 호출
        print("\n1️⃣ 테스트 엔드포인트 호출")
        test_response = await client.get(
            "http://localhost:8000/api/backtest/test",
            headers=headers
        )
        
        print(f"Status: {test_response.status_code}")
        print(f"Response: {test_response.json()}")
        
        # 백테스트 결과 엔드포인트 호출
        print("\n2️⃣ 백테스트 결과 엔드포인트 호출")
        result_response = await client.get(
            "http://localhost:8000/api/backtest/results/104",
            headers=headers
        )
        
        print(f"Status: {result_response.status_code}")
        if result_response.status_code == 200:
            result = result_response.json()
            print(f"Keys: {list(result.keys())}")
            print(f"Has equity_curve: {'equity_curve' in result}")
            print(f"Has equity_timestamps: {'equity_timestamps' in result}")
            print(f"Has symbol_performances: {'symbol_performances' in result}")
        else:
            print(f"Error: {result_response.text}")

if __name__ == "__main__":
    asyncio.run(test_router())