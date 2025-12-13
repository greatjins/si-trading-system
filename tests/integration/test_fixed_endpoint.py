#!/usr/bin/env python3
"""
수정된 엔드포인트 테스트
"""

import asyncio
import httpx
import json

async def test_fixed_endpoint():
    """수정된 엔드포인트 테스트"""
    
    print("🔧 수정된 엔드포인트 테스트")
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
        
        # 수정된 엔드포인트 호출
        backtest_id = 107
        
        print(f"\n📊 수정된 엔드포인트 호출 (ID: {backtest_id})")
        
        fixed_response = await client.get(
            f"http://localhost:8000/api/backtest/fixed/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {fixed_response.status_code}")
        
        if fixed_response.status_code == 200:
            fixed_data = fixed_response.json()
            
            print(f"\n📋 수정된 엔드포인트 응답:")
            
            # 핵심 필드들 확인
            key_fields = ['equity_curve', 'equity_timestamps', 'symbol_performances']
            
            for field in key_fields:
                if field in fixed_data:
                    value = fixed_data[field]
                    if isinstance(value, list):
                        print(f"  ✅ {field}: {len(value)}개 항목")
                        if len(value) > 0:
                            print(f"      샘플: {value[:2]}")
                    else:
                        print(f"  ✅ {field}: {type(value).__name__} = {value}")
                else:
                    print(f"  ❌ {field}: 필드 누락!")
            
            # 기본 정보도 확인
            print(f"\n📈 기본 정보:")
            print(f"  전략명: {fixed_data.get('strategy_name')}")
            print(f"  수익률: {fixed_data.get('total_return', 0)*100:.2f}%")
            print(f"  총 거래: {fixed_data.get('total_trades')}회")
                
        else:
            print(f"Error: {fixed_response.text}")

if __name__ == "__main__":
    asyncio.run(test_fixed_endpoint())