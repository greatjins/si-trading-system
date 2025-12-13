#!/usr/bin/env python3
"""
차트 최적화된 API 테스트
"""

import asyncio
import httpx
import json

async def test_chart_optimized():
    """차트 최적화된 API 테스트"""
    
    print("📊 차트 최적화된 API 테스트")
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
        
        # 백테스트 결과 조회
        backtest_id = 107
        
        print(f"\n📈 최적화된 백테스트 결과 조회 (ID: {backtest_id})")
        
        result_response = await client.get(
            f"http://localhost:8000/api/backtest/results/{backtest_id}",
            headers=headers
        )
        
        print(f"Status Code: {result_response.status_code}")
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            
            print(f"\n🎯 차트 렌더링 최적화 확인:")
            
            # 기존 필드 확인
            print(f"  ✅ equity_curve: {len(result_data.get('equity_curve', []))}개")
            print(f"  ✅ equity_timestamps: {len(result_data.get('equity_timestamps', []))}개")
            print(f"  ✅ symbol_performances: {len(result_data.get('symbol_performances', []))}개")
            
            # 새로운 차트 최적화 필드 확인
            chart_data = result_data.get('chart_data', [])
            performance_data = result_data.get('performance_data', [])
            
            print(f"\n🚀 차트 렌더링 최적화 필드:")
            print(f"  ✅ chart_data: {len(chart_data)}개 포인트")
            print(f"  ✅ performance_data: {len(performance_data)}개 포인트")
            
            if len(chart_data) > 0:
                print(f"\n📊 Chart Data 샘플:")
                for i, point in enumerate(chart_data[:3]):
                    print(f"    {i+1}. 날짜: {point.get('date')}")
                    print(f"       자산: {point.get('value'):,.0f}원")
                    print(f"       수익률: {point.get('return'):.2f}%")
            
            if len(performance_data) > 0:
                print(f"\n📈 Performance Data 샘플:")
                for i, point in enumerate(performance_data[:3]):
                    print(f"    {i+1}. 날짜: {point.get('date')}, 수익률: {point.get('return'):.2f}%")
            
            # 종목별 성과 확인
            symbol_performances = result_data.get('symbol_performances', [])
            if len(symbol_performances) > 0:
                print(f"\n🏆 종목별 성과 (상위 3개):")
                for i, perf in enumerate(symbol_performances[:3]):
                    print(f"    {i+1}. {perf.get('name')} ({perf.get('symbol')})")
                    print(f"       수익률: {perf.get('total_return'):.2f}%")
                    print(f"       거래: {perf.get('trade_count')}회")
                    print(f"       승률: {perf.get('win_rate'):.1f}%")
        
        else:
            print(f"❌ Error: {result_response.text}")

if __name__ == "__main__":
    asyncio.run(test_chart_optimized())