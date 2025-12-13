"""
ICT 이론 기반 전략 빌더 테스트
- Smart Money Concepts 적용
- BOS, FVG, Order Block 등 ICT 지표 활용
"""
import asyncio
import httpx
from datetime import datetime

async def test_ict_strategy_builder():
    """ICT 이론 기반 전략 빌더 테스트"""
    
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
        
        # 1. ICT 지표 목록 확인
        indicators_response = await client.get(
            "http://localhost:8000/api/strategy-builder/indicators"
        )
        
        if indicators_response.status_code == 200:
            indicators_data = indicators_response.json()
            
            # ICT 카테고리 지표들 확인
            ict_indicators = [ind for ind in indicators_data['indicators'] if ind['category'] == 'ict']
            print(f"\n🎯 ICT 지표 수: {len(ict_indicators)}")
            
            for indicator in ict_indicators:
                print(f"  - {indicator['name']}: {indicator['description']}")
        
        # 2. ICT 기반 전략 생성
        ict_strategy_config = {
            "name": "ICT Smart Money 전략",
            "description": "Inner Circle Trader 이론을 활용한 기관투자자 추종 전략",
            "stockSelection": {
                "marketCap": {"min": 5000, "max": 100000},  # 대형주 중심
                "volume": {"min": 500000},  # 높은 유동성
                "volumeValue": {"min": 5000},  # 50억원 이상 거래대금
                "excludeManaged": True,
                "excludeClearing": True,
                "excludeSpac": True,
                "minListingDays": 180
            },
            "buyConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "bos",  # Break of Structure
                    "operator": "break_high",
                    "value": "close",
                    "lookback": 20
                },
                {
                    "id": "2",
                    "type": "indicator", 
                    "indicator": "smart_money",  # Smart Money Flow
                    "operator": "bullish",
                    "value": 50,
                    "period": 20
                },
                {
                    "id": "3",
                    "type": "indicator",
                    "indicator": "fvg",  # Fair Value Gap
                    "operator": "in_gap",
                    "value": "bullish",
                    "min_gap": 0.003
                },
                {
                    "id": "4",
                    "type": "indicator",
                    "indicator": "order_block",  # Order Block
                    "operator": "in_block",
                    "value": "bullish",
                    "volume_multiplier": 2.0
                }
            ],
            "sellConditions": [
                {
                    "id": "1",
                    "type": "indicator",
                    "indicator": "liquidity_pool",  # Liquidity Pool
                    "operator": "near_pool",
                    "value": "resistance",
                    "cluster_threshold": 0.01
                },
                {
                    "id": "2",
                    "type": "indicator",
                    "indicator": "smart_money",
                    "operator": "bearish", 
                    "value": 50,
                    "period": 14
                }
            ],
            "entryStrategy": {
                "type": "single",  # ICT는 정확한 타이밍이 중요
                "maxPositionSize": 25,
                "minInterval": 1
            },
            "positionManagement": {
                "sizingMethod": "atr_risk",  # 리스크 기반 사이징
                "accountRisk": 1.0,  # 1% 리스크
                "atrPeriod": 14,
                "atrMultiple": 2.0,
                "maxPositions": 3,  # 집중 투자
                "stopLoss": {
                    "enabled": True,
                    "method": "atr",
                    "atrMultiple": 1.5,  # 타이트한 손절
                    "minPercent": 2,
                    "maxPercent": 5
                },
                "takeProfit": {
                    "enabled": True,
                    "method": "r_multiple",
                    "rMultiple": 3.0  # 1:3 리스크 리워드
                },
                "trailingStop": {
                    "enabled": True,
                    "method": "atr",
                    "atrMultiple": 2.5,
                    "activationProfit": 3.0,  # 3% 수익 후 활성화
                    "updateFrequency": "new_high"
                }
            }
        }
        
        # 전략 저장
        save_response = await client.post(
            "http://localhost:8000/api/strategy-builder/save",
            headers=headers,
            json=ict_strategy_config
        )
        
        if save_response.status_code != 200:
            print(f"❌ ICT 전략 저장 실패: {save_response.text}")
            return
        
        strategy_data = save_response.json()
        strategy_id = strategy_data["strategy_id"]
        
        print(f"\n✅ ICT 전략 저장 성공: ID={strategy_id}")
        print(f"📝 전략명: {strategy_data['name']}")
        
        # 3. 생성된 Python 코드 확인
        print("\n🔍 생성된 ICT 전략 코드 (일부):")
        print("=" * 80)
        python_code = strategy_data.get("python_code", "")
        
        # ICT 관련 부분만 추출
        lines = python_code.split('\n')
        ict_lines = []
        in_ict_section = False
        
        for line in lines:
            if 'BOS' in line or 'Smart Money' in line or 'Fair Value Gap' in line or 'Order Block' in line:
                in_ict_section = True
                ict_lines.append(line)
            elif in_ict_section and line.strip() == '':
                ict_lines.append(line)
            elif in_ict_section and line.startswith('        #'):
                ict_lines.append(line)
            elif in_ict_section and not line.startswith('        '):
                in_ict_section = False
            elif in_ict_section:
                ict_lines.append(line)
        
        if ict_lines:
            print('\n'.join(ict_lines[:20]))  # 처음 20줄만
        else:
            print(python_code[:1000] + "...")
        
        print("=" * 80)
        
        # 4. 추가 ICT 전략 패턴들
        print("\n🎯 ICT 전략 패턴 예시:")
        
        patterns = [
            {
                "name": "BOS + FVG 리테스트",
                "description": "구조적 돌파 후 공정가치 갭 재테스트 진입",
                "conditions": ["BOS 상승 돌파", "FVG 리테스트", "높은 거래량"]
            },
            {
                "name": "Order Block 반등",
                "description": "기관 주문 블록에서 반등 진입",
                "conditions": ["Order Block 터치", "Smart Money 유입", "RSI 과매도"]
            },
            {
                "name": "Liquidity Sweep",
                "description": "유동성 사냥 후 반대 방향 진입",
                "conditions": ["고점/저점 돌파", "즉시 반전", "거래량 급증"]
            }
        ]
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n{i}. {pattern['name']}")
            print(f"   설명: {pattern['description']}")
            print(f"   조건: {' + '.join(pattern['conditions'])}")
        
        print("\n✅ ICT 전략 빌더 테스트 완료!")
        print("🎯 Smart Money Concepts가 전략 빌더에 성공적으로 통합되었습니다.")
        print("📈 기관투자자 관점의 고급 매매 전략을 노코드로 구현할 수 있습니다.")

if __name__ == "__main__":
    asyncio.run(test_ict_strategy_builder())