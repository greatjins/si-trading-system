#!/usr/bin/env python3
"""
ICT 지표를 사용한 전략 생성 테스트
"""
import requests
import json

def test_ict_strategy_creation():
    """ICT 지표를 사용한 전략 생성 테스트"""
    
    base_url = "http://localhost:8000"
    
    # ICT 기반 전략 데이터
    strategy_data = {
        "name": "ICT 브레이크아웃 전략",
        "description": "BOS와 Fair Value Gap을 활용한 ICT 이론 기반 전략",
        "stockSelection": {
            "marketCap": {"min": 1000, "max": 50000},
            "volume": {"min": 100000},
            "market": ["KOSPI", "KOSDAQ"]
        },
        "buyConditions": [
            {
                "id": "buy_1",
                "type": "indicator",
                "indicator": "bos",
                "operator": ">",
                "value": 0,
                "lookback": 20
            },
            {
                "id": "buy_2", 
                "type": "indicator",
                "indicator": "fvg",
                "operator": ">",
                "value": 0,
                "min_gap": 0.002
            }
        ],
        "sellConditions": [
            {
                "id": "sell_1",
                "type": "indicator", 
                "indicator": "smart_money",
                "operator": "<",
                "value": 0,
                "period": 20
            }
        ],
        "riskManagement": {
            "stopLoss": {"enabled": True, "percentage": 3.0},
            "takeProfit": {"enabled": True, "percentage": 8.0},
            "maxPositions": 5
        },
        "positionManagement": {
            "sizingMethod": "equal_weight",
            "maxPositionSize": 20.0
        }
    }
    
    try:
        print("🚀 ICT 전략 생성 테스트 시작...")
        
        # 전략 생성 API 호출
        response = requests.post(
            f"{base_url}/api/strategy-builder/save",
            json=strategy_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ICT 전략 생성 성공!")
            print(f"   전략 ID: {result.get('id', 'N/A')}")
            print(f"   전략명: {result.get('name', 'N/A')}")
            
            # 생성된 전략 코드 확인
            if 'generated_code' in result:
                code_lines = result['generated_code'].split('\n')
                ict_lines = [line for line in code_lines if any(keyword in line.lower() for keyword in ['bos', 'fair value gap', 'smart money'])]
                
                if ict_lines:
                    print("✅ ICT 지표 코드가 정상 생성됨:")
                    for line in ict_lines[:3]:  # 처음 3줄만 표시
                        print(f"   {line.strip()}")
                else:
                    print("⚠️ ICT 지표 코드를 찾을 수 없습니다.")
            
        else:
            print(f"❌ 전략 생성 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패. 백엔드 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_ict_strategy_creation()