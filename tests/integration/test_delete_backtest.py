#!/usr/bin/env python3
"""
백테스트 삭제 기능 테스트
"""

import asyncio
import httpx
import json

async def test_delete_backtest():
    """백테스트 삭제 기능 테스트"""
    
    print("🗑️ 백테스트 삭제 기능 테스트")
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
        
        # 1. 현재 백테스트 목록 확인
        print(f"\n📊 현재 백테스트 목록 확인")
        
        list_response = await client.get(
            "http://localhost:8000/api/backtest/results",
            headers=headers
        )
        
        if list_response.status_code == 200:
            backtests = list_response.json()
            print(f"  현재 백테스트 개수: {len(backtests)}개")
            
            if len(backtests) > 0:
                # 가장 오래된 백테스트 선택 (삭제 테스트용)
                oldest_backtest = backtests[-1]
                test_id = oldest_backtest['backtest_id']
                
                print(f"  삭제 테스트 대상: ID={test_id}, 전략={oldest_backtest['strategy_name']}")
                
                # 2. 개별 백테스트 삭제 테스트
                print(f"\n🗑️ 개별 백테스트 삭제 테스트 (ID: {test_id})")
                
                delete_response = await client.delete(
                    f"http://localhost:8000/api/backtest/results/{test_id}",
                    headers=headers
                )
                
                print(f"  삭제 응답 코드: {delete_response.status_code}")
                
                if delete_response.status_code == 200:
                    delete_result = delete_response.json()
                    print(f"  ✅ 삭제 성공: {delete_result['message']}")
                    
                    # 3. 삭제 후 목록 재확인
                    print(f"\n📊 삭제 후 백테스트 목록 재확인")
                    
                    list_response2 = await client.get(
                        "http://localhost:8000/api/backtest/results",
                        headers=headers
                    )
                    
                    if list_response2.status_code == 200:
                        backtests2 = list_response2.json()
                        print(f"  삭제 후 백테스트 개수: {len(backtests2)}개")
                        print(f"  감소된 개수: {len(backtests) - len(backtests2)}개")
                        
                        # 삭제된 백테스트가 목록에 없는지 확인
                        deleted_ids = [bt['backtest_id'] for bt in backtests2]
                        if test_id not in deleted_ids:
                            print(f"  ✅ 백테스트 ID {test_id}가 목록에서 제거됨")
                        else:
                            print(f"  ❌ 백테스트 ID {test_id}가 여전히 목록에 존재")
                else:
                    print(f"  ❌ 삭제 실패: {delete_response.text}")
                
                # 4. 일괄 삭제 테스트 (최근 2개)
                if len(backtests2) >= 2:
                    print(f"\n🗑️ 일괄 삭제 테스트 (최근 2개)")
                    
                    batch_ids = [backtests2[0]['backtest_id'], backtests2[1]['backtest_id']]
                    print(f"  삭제 대상 IDs: {batch_ids}")
                    
                    # httpx에서 DELETE 요청에 JSON 데이터 전송
                    batch_delete_response = await client.request(
                        "DELETE",
                        "http://localhost:8000/api/backtest/results/batch",
                        headers=headers,
                        json=batch_ids
                    )
                    
                    print(f"  일괄 삭제 응답 코드: {batch_delete_response.status_code}")
                    
                    if batch_delete_response.status_code == 200:
                        batch_result = batch_delete_response.json()
                        print(f"  ✅ 일괄 삭제 성공: {batch_result['message']}")
                        print(f"  삭제된 개수: {batch_result['deleted_count']}")
                        print(f"  실패한 IDs: {batch_result['failed_ids']}")
                    else:
                        print(f"  ❌ 일괄 삭제 실패: {batch_delete_response.text}")
            else:
                print("  삭제할 백테스트가 없습니다.")
        else:
            print(f"❌ 백테스트 목록 조회 실패: {list_response.text}")

if __name__ == "__main__":
    asyncio.run(test_delete_backtest())