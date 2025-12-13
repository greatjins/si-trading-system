#!/usr/bin/env python3
"""
백테스트 상세보기 자산곡선 데이터 디버깅
"""

import asyncio
import httpx

async def debug_chart_data():
    """자산곡선 데이터 디버깅"""
    
    print("📈 자산곡선 데이터 디버깅")
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
        
        # 백테스트 목록에서 첫 번째 항목 조회
        list_response = await client.get(
            "http://localhost:8000/api/backtest/results?limit=1",
            headers=headers
        )
        
        if list_response.status_code == 200:
            backtests = list_response.json()
            if backtests:
                backtest_id = backtests[0]['backtest_id']
                
                print(f"📊 백테스트 ID: {backtest_id}")
                
                # 상세 결과 조회
                detail_response = await client.get(
                    f"http://localhost:8000/api/backtest/results/{backtest_id}",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    
                    print(f"\n📈 자산곡선 데이터 확인:")
                    print(f"  - equity_curve 길이: {len(detail.get('equity_curve', []))}")
                    print(f"  - equity_timestamps 길이: {len(detail.get('equity_timestamps', []))}")
                    print(f"  - chart_data 길이: {len(detail.get('chart_data', []))}")
                    
                    if detail.get('equity_curve'):
                        print(f"  - equity_curve 샘플: {detail['equity_curve'][:3]}...")
                    
                    if detail.get('equity_timestamps'):
                        print(f"  - equity_timestamps 샘플: {detail['equity_timestamps'][:3]}...")
                    
                    if detail.get('chart_data'):
                        print(f"  - chart_data 샘플: {detail['chart_data'][:2]}")
                    
                    print(f"\n📊 기본 정보:")
                    print(f"  - initial_capital: {detail.get('initial_capital')}")
                    print(f"  - final_equity: {detail.get('final_equity')}")
                    print(f"  - total_return: {detail.get('total_return')}")
                    
                    # 자산곡선 데이터가 없는 경우
                    if not detail.get('equity_curve') or len(detail.get('equity_curve', [])) == 0:
                        print("\n❌ 자산곡선 데이터가 없습니다!")
                        print("  가능한 원인:")
                        print("  1. 백테스트 실행 시 자산곡선 저장 실패")
                        print("  2. 데이터베이스에서 조회 실패")
                        print("  3. API 응답에서 누락")
                    else:
                        print("\n✅ 자산곡선 데이터 정상")
                        
                else:
                    print(f"❌ 상세 결과 조회 실패: {detail_response.text}")
            else:
                print("백테스트 목록이 비어있습니다.")
        else:
            print(f"❌ 백테스트 목록 조회 실패: {list_response.text}")

if __name__ == "__main__":
    asyncio.run(debug_chart_data())