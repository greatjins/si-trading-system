#!/usr/bin/env python3
"""
백테스트 목록 API 테스트
"""

import asyncio
import httpx
import json

async def test_backtest_list_api():
    """백테스트 목록 API 테스트"""
    
    print("🔍 백테스트 목록 API 테스트")
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
        
        # 백테스트 목록 조회
        print(f"\n📊 백테스트 목록 API 호출")
        
        list_response = await client.get(
            "http://localhost:8000/api/backtest/results",
            headers=headers
        )
        
        print(f"Status Code: {list_response.status_code}")
        
        if list_response.status_code == 200:
            results = list_response.json()
            
            print(f"\n📋 API 응답 결과:")
            print(f"  총 개수: {len(results)}개")
            
            if len(results) > 0:
                print(f"\n📈 백테스트 목록 (최근 10개):")
                print("-" * 80)
                print(f"{'ID':<5} {'전략명':<20} {'수익률':<10} {'거래수':<8} {'생성일시':<20}")
                print("-" * 80)
                
                for i, bt in enumerate(results[:10]):
                    created_at = bt.get('created_at', 'N/A')[:16] if bt.get('created_at') else 'N/A'
                    return_pct = f"{bt.get('total_return', 0)*100:.2f}%" if bt.get('total_return') else "N/A"
                    
                    print(f"{bt.get('backtest_id', 'N/A'):<5} {bt.get('strategy_name', 'N/A')[:18]:<20} {return_pct:<10} {bt.get('total_trades', 0):<8} {created_at:<20}")
                
                if len(results) > 10:
                    print(f"... 및 {len(results) - 10}개 더")
            
            # 전략별 분포 확인
            strategy_counts = {}
            for bt in results:
                strategy = bt.get('strategy_name', 'Unknown')
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            print(f"\n📈 전략별 분포:")
            for strategy, count in strategy_counts.items():
                print(f"  - {strategy}: {count}개")
        
        else:
            print(f"❌ Error: {list_response.text}")

if __name__ == "__main__":
    asyncio.run(test_backtest_list_api())