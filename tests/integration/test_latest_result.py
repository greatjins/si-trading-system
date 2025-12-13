#!/usr/bin/env python3
"""
최신 백테스트 결과 확인
"""

import asyncio
import httpx
import json

async def test_latest_result():
    """최신 백테스트 결과 확인"""
    
    print("🔍 최신 백테스트 결과 확인 (ID: 107)")
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
        
        # 백테스트 ID 107 결과 조회
        backtest_id = 107
        
        print(f"\n📊 백테스트 결과 조회 (ID: {backtest_id})")
        
        result_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {result_response.status_code}")
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            
            print(f"\n📋 응답 필드 확인:")
            
            # 핵심 필드들 확인
            key_fields = ['equity_curve', 'equity_timestamps', 'symbol_performances']
            
            for field in key_fields:
                if field in result_data:
                    value = result_data[field]
                    if isinstance(value, list):
                        print(f"  ✅ {field}: {len(value)}개 항목")
                        if len(value) > 0:
                            print(f"      샘플: {value[:2]}")
                    else:
                        print(f"  ✅ {field}: {type(value).__name__} = {value}")
                else:
                    print(f"  ❌ {field}: 필드 누락!")
            
            # 전체 필드 목록
            print(f"\n📝 전체 응답 필드:")
            for key in result_data.keys():
                print(f"  - {key}")
                
        else:
            print(f"Error: {result_response.text}")

if __name__ == "__main__":
    asyncio.run(test_latest_result())