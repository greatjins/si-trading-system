"""
전략 빌더 최종 테스트 - 타입 오류 해결 후 검증
"""
import asyncio
import httpx

async def test_strategy_builder_final():
    """전략 빌더 최종 테스트"""
    
    # 로그인
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ 로그인 성공")
        
        # 1. 지표 목록 확인
        indicators_response = await client.get(
            "http://localhost:8000/api/strategy-builder/indicators"
        )
        
        if indicators_response.status_code == 200:
            data = indicators_response.json()
            print(f"📊 총 지표 수: {len(data['indicators'])}")
            print(f"📂 카테고리 수: {len(data['categories'])}")
            
            # ICT 카테고리 확인
            ict_indicators = [ind for ind in data['indicators'] if ind['category'] == 'ict']
            if ict_indicators:
                print(f"🎯 ICT 지표 수: {len(ict_indicators)}")
                for ind in ict_indicators:
                    print(f"  - {ind['name']}: {ind['description']}")
            else:
                print("⚠️ ICT 지표가 없습니다")
        
        # 2. 간단한 전략 생성 테스트
        simple_strategy = {
            "name": "간단한 테스트 전략",
            "description": "타입 오류 수정 후 테스트용 전략",
            "stockSelection": {
                "marketCap": {"min": 1000},
                "excludeManaged": True
            },
            "buyConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "ma",
                    "operator": ">",
                    "value": 50000,  # 숫자 값으로 테스트
                    "period": 20
                }
            ],
            "sellConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "rsi",
                    "operator": ">",
                    "value": 70,
                    "period": 14
                }
            ],
            "entryStrategy": {
                "type": "single"
            },
            "positionManagement": {
                "sizingMethod": "fixed",
                "positionSize": 0.1,
                "maxPositions": 5,
                "stopLoss": {"enabled": False},
                "takeProfit": {"enabled": False},
                "trailingStop": {"enabled": False}
            }
        }
        
        # 전략 저장 테스트
        save_response = await client.post(
            "http://localhost:8000/api/strategy-builder/save",
            headers=headers,
            json=simple_strategy
        )
        
        if save_response.status_code == 200:
            strategy_data = save_response.json()
            print(f"✅ 전략 저장 성공: ID={strategy_data['strategy_id']}")
            
            # 생성된 코드 확인
            if 'python_code' in strategy_data:
                code_lines = strategy_data['python_code'].split('\n')
                print(f"📝 생성된 코드 라인 수: {len(code_lines)}")
                
                # 주요 키워드 확인
                code_text = strategy_data['python_code']
                keywords = ['BaseStrategy', 'on_bar', 'OrderSignal', 'MA', 'RSI']
                found_keywords = [kw for kw in keywords if kw in code_text]
                print(f"🔍 포함된 키워드: {found_keywords}")
            
        else:
            print(f"❌ 전략 저장 실패: {save_response.text}")
        
        # 3. 전략 목록 확인
        list_response = await client.get(
            "http://localhost:8000/api/strategy-builder/list",
            headers=headers
        )
        
        if list_response.status_code == 200:
            strategies = list_response.json()
            print(f"📋 총 전략 수: {len(strategies)}")
            
            for strategy in strategies[-3:]:  # 최근 3개
                print(f"  - {strategy['name']} (ID: {strategy['strategy_id']})")
        
        print("\n✅ 전략 빌더 최종 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_strategy_builder_final())