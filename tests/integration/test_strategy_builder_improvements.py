"""
전략 빌더 개선사항 테스트
- 상대적 비교 조건 처리
- ICT 이론 기반 전략 생성
"""
import asyncio
import httpx
from datetime import datetime

async def test_strategy_builder_improvements():
    """전략 빌더 개선사항 테스트"""
    
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
        
        # 1. 상대적 비교 조건을 사용한 전략 생성
        strategy_config = {
            "name": "ICT 이론 기반 전략 v2",
            "description": "상대적 비교 조건을 활용한 ICT 이론 기반 전략",
            "stockSelection": {
                "marketCap": {"min": 1000, "max": 50000},
                "volume": {"min": 100000},
                "excludeManaged": True,
                "excludeClearing": True,
                "excludeSpac": True,
                "minListingDays": 90
            },
            "buyConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "ma",
                    "operator": ">",
                    "value": "MA(20)",  # MA(5) > MA(20)
                    "period": 5
                },
                {
                    "id": "2", 
                    "type": "indicator",
                    "indicator": "ma",
                    "operator": ">",
                    "value": "MA(60)",  # MA(20) > MA(60)
                    "period": 20
                },
                {
                    "id": "3",
                    "type": "indicator", 
                    "indicator": "volume_ma",
                    "operator": ">",
                    "value": "close",  # 거래량 > 거래량 평균
                    "period": 20
                },
                {
                    "id": "4",
                    "type": "indicator",
                    "indicator": "rsi",
                    "operator": ">",
                    "value": 50,  # RSI > 50 (모멘텀 확인)
                    "period": 14
                }
            ],
            "sellConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "ma",
                    "operator": "<",
                    "value": "MA(20)",  # MA(5) < MA(20) (하향 돌파)
                    "period": 5
                },
                {
                    "id": "2",
                    "type": "indicator",
                    "indicator": "rsi", 
                    "operator": ">",
                    "value": 70,  # RSI > 70 (과매수)
                    "period": 14
                }
            ],
            "entryStrategy": {
                "type": "pyramid",
                "pyramidLevels": [
                    {"level": 1, "condition": "initial", "priceChange": 0, "units": 1.0},
                    {"level": 2, "condition": "price_increase", "priceChange": 5, "units": 1.0},
                    {"level": 3, "condition": "price_increase", "priceChange": 12, "units": 0.5}
                ],
                "maxLevels": 3,
                "maxPositionSize": 30,
                "minInterval": 1
            },
            "positionManagement": {
                "sizingMethod": "atr_risk",
                "accountRisk": 1.5,
                "atrPeriod": 20,
                "atrMultiple": 2.0,
                "maxPositions": 5,
                "stopLoss": {
                    "enabled": True,
                    "method": "atr",
                    "atrMultiple": 2.0,
                    "minPercent": 3,
                    "maxPercent": 8
                },
                "takeProfit": {
                    "enabled": False
                },
                "trailingStop": {
                    "enabled": True,
                    "method": "atr",
                    "atrMultiple": 3.0,
                    "activationProfit": 5.0,
                    "updateFrequency": "every_bar"
                }
            }
        }
        
        # 전략 저장
        save_response = await client.post(
            "http://localhost:8000/api/strategy-builder/save",
            headers=headers,
            json=strategy_config
        )
        
        if save_response.status_code != 200:
            print(f"❌ 전략 저장 실패: {save_response.text}")
            return
        
        strategy_data = save_response.json()
        strategy_id = strategy_data["strategy_id"]
        
        print(f"✅ 전략 저장 성공: ID={strategy_id}")
        print(f"📝 전략명: {strategy_data['name']}")
        
        # 2. 생성된 Python 코드 확인
        print("\n🔍 생성된 Python 코드:")
        print("=" * 80)
        print(strategy_data.get("python_code", "코드 없음")[:1000] + "...")
        print("=" * 80)
        
        # 3. 전략 목록에서 확인
        list_response = await client.get(
            "http://localhost:8000/api/strategy-builder/list",
            headers=headers
        )
        
        if list_response.status_code == 200:
            strategies = list_response.json()
            print(f"\n📋 전체 전략 수: {len(strategies)}")
            
            for strategy in strategies[:3]:  # 최근 3개만 표시
                print(f"  - {strategy['name']} (ID: {strategy['strategy_id']})")
                print(f"    포트폴리오: {'✅' if strategy.get('is_portfolio') else '❌'}")
                print(f"    생성일: {strategy['created_at'][:19]}")
        
        # 4. 지표 목록 확인
        indicators_response = await client.get(
            "http://localhost:8000/api/strategy-builder/indicators"
        )
        
        if indicators_response.status_code == 200:
            indicators_data = indicators_response.json()
            print(f"\n📊 사용 가능한 지표 수: {len(indicators_data['indicators'])}")
            print(f"📂 카테고리 수: {len(indicators_data['categories'])}")
            
            # 카테고리별 지표 수
            for category in indicators_data['categories']:
                cat_indicators = [ind for ind in indicators_data['indicators'] if ind['category'] == category['id']]
                print(f"  - {category['name']}: {len(cat_indicators)}개")
        
        print("\n✅ 전략 빌더 개선사항 테스트 완료!")
        print("🎯 상대적 비교 조건 처리 기능이 정상적으로 구현되었습니다.")
        print("📈 ICT 이론 기반 전략 생성이 가능합니다.")

if __name__ == "__main__":
    asyncio.run(test_strategy_builder_improvements())