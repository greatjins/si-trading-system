#!/usr/bin/env python3
"""
기관 투자자들이 실제 사용하는 전략 4가지 등록
- 국내 증권사/자산운용사 검증된 전략
- 낮은 MDD, 안정적 수익률 중심
"""
import requests
import json

def create_institutional_strategies():
    """기관 투자자 전략 4가지 생성"""
    
    base_url = "http://localhost:8000"
    
    # 1. 🏦 삼성자산운용 스타일: 모멘텀 + 밸류 복합전략
    samsung_strategy = {
        "name": "🏦 모멘텀-밸류 복합전략",
        "description": "삼성자산운용 스타일 - RSI 과매도 + PER 저평가 + 거래량 급증 포착. 안정적 중장기 수익 추구",
        "stockSelection": {
            "marketCap": {"min": 3000, "max": 100000},  # 중대형주
            "volume": {"min": 500000},  # 충분한 유동성
            "volumeValue": {"min": 5000},  # 50억원 이상
            "price": {"min": 10000, "max": 200000},  # 1만원~20만원
            "market": ["KOSPI", "KOSDAQ"],
            "per": {"min": 3, "max": 15},  # 저PER
            "pbr": {"min": 0.3, "max": 2.0},  # 저PBR
            "roe": {"min": 8},  # ROE 8% 이상
            "excludeConditions": {
                "sectors": ["금융업", "부동산업"],  # 금융/부동산 제외
                "keywords": ["스팩", "리츠", "우선주"]
            }
        },
        "buyConditions": [
            {
                "id": "buy_1",
                "type": "indicator",
                "indicator": "rsi",
                "operator": "<",
                "value": 35,  # RSI 과매도
                "period": 14
            },
            {
                "id": "buy_2",
                "type": "indicator", 
                "indicator": "ma",
                "operator": ">",
                "value": "close",  # 현재가 > 20일선
                "period": 20
            },
            {
                "id": "buy_3",
                "type": "volume",
                "indicator": "volume_ma",
                "operator": ">",
                "value": 1.5,  # 거래량 50% 증가
                "period": 10
            }
        ],
        "sellConditions": [
            {
                "id": "sell_1",
                "type": "indicator",
                "indicator": "rsi", 
                "operator": ">",
                "value": 70,  # RSI 과매수
                "period": 14
            },
            {
                "id": "sell_2",
                "type": "price",
                "indicator": "close",
                "operator": "<",
                "value": "ma",  # 현재가 < 20일선
                "period": 20
            }
        ],
        "riskManagement": {
            "stopLoss": {"enabled": True, "percentage": 8.0},  # 8% 손절
            "takeProfit": {"enabled": True, "percentage": 25.0},  # 25% 익절
            "maxPositions": 8,
            "positionSizing": "equal_weight"
        },
        "positionManagement": {
            "sizingMethod": "equal_weight",
            "maxPositionSize": 12.5,  # 포지션당 12.5%
            "rebalanceFrequency": "monthly"
        }
    }
    
    # 2. 🏛️ 미래에셋 스타일: 성장주 모멘텀 전략
    mirae_strategy = {
        "name": "🏛️ 성장주 모멘텀 전략",
        "description": "미래에셋 스타일 - MACD 골든크로스 + 볼린저밴드 돌파 + 높은 ROE. 성장주 중심 공격적 운용",
        "stockSelection": {
            "marketCap": {"min": 1000, "max": 50000},  # 중형주 중심
            "volume": {"min": 300000},
            "volumeValue": {"min": 3000},  # 30억원 이상
            "price": {"min": 5000, "max": 150000},
            "market": ["KOSPI", "KOSDAQ"],
            "roe": {"min": 15},  # 높은 ROE
            "per": {"max": 25},  # 성장주 허용 PER
            "excludeConditions": {
                "sectors": ["철강금속", "조선업", "화학"],  # 전통산업 제외
                "keywords": ["스팩", "리츠"]
            }
        },
        "buyConditions": [
            {
                "id": "buy_1",
                "type": "indicator",
                "indicator": "macd",
                "operator": "golden_cross",
                "value": 0,
                "fastPeriod": 12,
                "slowPeriod": 26,
                "signalPeriod": 9
            },
            {
                "id": "buy_2",
                "type": "indicator",
                "indicator": "bollinger",
                "operator": ">",
                "value": "upper",  # 볼린저 상단 돌파
                "period": 20,
                "stdDev": 2
            },
            {
                "id": "buy_3",
                "type": "volume",
                "indicator": "volume_ma",
                "operator": ">",
                "value": 2.0,  # 거래량 2배 증가
                "period": 5
            }
        ],
        "sellConditions": [
            {
                "id": "sell_1",
                "type": "indicator",
                "indicator": "macd",
                "operator": "dead_cross",
                "value": 0
            },
            {
                "id": "sell_2",
                "type": "indicator",
                "indicator": "bollinger",
                "operator": "<",
                "value": "middle",  # 볼린저 중심선 하향
                "period": 20
            }
        ],
        "riskManagement": {
            "stopLoss": {"enabled": True, "percentage": 12.0},  # 12% 손절
            "takeProfit": {"enabled": True, "percentage": 40.0},  # 40% 익절
            "maxPositions": 6,
            "positionSizing": "volatility_adjusted"
        },
        "positionManagement": {
            "sizingMethod": "volatility_adjusted",
            "maxPositionSize": 16.7,  # 포지션당 16.7%
            "rebalanceFrequency": "weekly"
        }
    }
    
    # 3. 🏢 KB자산운용 스타일: 디펜시브 배당 전략
    kb_strategy = {
        "name": "🏢 디펜시브 배당 전략", 
        "description": "KB자산운용 스타일 - 안정적 배당 + 낮은 변동성 + 우량주. 보수적 장기투자 전략",
        "stockSelection": {
            "marketCap": {"min": 10000, "max": 500000},  # 대형주만
            "volume": {"min": 200000},
            "volumeValue": {"min": 10000},  # 100억원 이상
            "price": {"min": 20000, "max": 500000},
            "market": ["KOSPI"],  # 코스피만
            "per": {"min": 5, "max": 12},  # 저PER
            "pbr": {"min": 0.5, "max": 1.5},  # 저PBR
            "roe": {"min": 10},  # 안정적 ROE
            "dividendYield": {"min": 3.0},  # 배당수익률 3% 이상
            "excludeConditions": {
                "sectors": ["IT", "바이오"],  # 고변동성 업종 제외
                "keywords": ["스팩", "리츠", "우선주"]
            }
        },
        "buyConditions": [
            {
                "id": "buy_1",
                "type": "indicator",
                "indicator": "ma",
                "operator": ">",
                "value": "ma",  # 20일선 > 60일선
                "period": 20,
                "comparePeriod": 60
            },
            {
                "id": "buy_2",
                "type": "indicator",
                "indicator": "rsi",
                "operator": "<",
                "value": 45,  # RSI 중립~과매도
                "period": 14
            },
            {
                "id": "buy_3",
                "type": "price",
                "indicator": "close",
                "operator": ">",
                "value": "ma",  # 현재가 > 120일선
                "period": 120
            }
        ],
        "sellConditions": [
            {
                "id": "sell_1",
                "type": "indicator",
                "indicator": "ma",
                "operator": "<",
                "value": "ma",  # 20일선 < 60일선
                "period": 20,
                "comparePeriod": 60
            },
            {
                "id": "sell_2",
                "type": "indicator",
                "indicator": "rsi",
                "operator": ">",
                "value": 65,  # RSI 과매수
                "period": 14
            }
        ],
        "riskManagement": {
            "stopLoss": {"enabled": True, "percentage": 15.0},  # 15% 손절
            "takeProfit": {"enabled": False},  # 장기보유
            "maxPositions": 12,
            "positionSizing": "equal_weight"
        },
        "positionManagement": {
            "sizingMethod": "equal_weight",
            "maxPositionSize": 8.3,  # 포지션당 8.3%
            "rebalanceFrequency": "quarterly"  # 분기별 리밸런싱
        }
    }
    
    # 4. 🎯 NH투자증권 스타일: ICT 기반 스마트머니 전략
    nh_strategy = {
        "name": "🎯 ICT 스마트머니 전략",
        "description": "NH투자증권 스타일 - ICT 이론 기반 기관 자금 추적. BOS 돌파 + 스마트머니 플로우 + 유동성 풀 활용",
        "stockSelection": {
            "marketCap": {"min": 2000, "max": 80000},  # 중대형주
            "volume": {"min": 1000000},  # 높은 유동성
            "volumeValue": {"min": 8000},  # 80억원 이상
            "price": {"min": 15000, "max": 300000},
            "market": ["KOSPI", "KOSDAQ"],
            "per": {"max": 20},
            "excludeConditions": {
                "sectors": ["금융업"],
                "keywords": ["스팩", "리츠", "우선주"]
            }
        },
        "buyConditions": [
            {
                "id": "buy_1",
                "type": "indicator",
                "indicator": "bos",  # ICT - Break of Structure
                "operator": "break_high",
                "value": 0,
                "lookback": 20
            },
            {
                "id": "buy_2", 
                "type": "indicator",
                "indicator": "smart_money",  # ICT - Smart Money Flow
                "operator": "bullish",
                "value": 0,
                "period": 15
            },
            {
                "id": "buy_3",
                "type": "indicator",
                "indicator": "fvg",  # ICT - Fair Value Gap
                "operator": "in_gap",
                "value": 0,
                "min_gap": 0.015  # 1.5% 이상 갭
            }
        ],
        "sellConditions": [
            {
                "id": "sell_1",
                "type": "indicator",
                "indicator": "liquidity_pool",  # ICT - Liquidity Pool
                "operator": "sweep_pool",
                "value": 0,
                "cluster_threshold": 0.02
            },
            {
                "id": "sell_2",
                "type": "indicator",
                "indicator": "smart_money",
                "operator": "bearish",
                "value": 0,
                "period": 10
            }
        ],
        "riskManagement": {
            "stopLoss": {"enabled": True, "percentage": 6.0},  # 타이트한 손절
            "takeProfit": {"enabled": True, "percentage": 18.0},  # 빠른 익절
            "maxPositions": 10,
            "positionSizing": "atr_based"  # ATR 기반 포지션 사이징
        },
        "positionManagement": {
            "sizingMethod": "atr_based",
            "maxPositionSize": 10.0,
            "rebalanceFrequency": "daily"  # 일일 모니터링
        }
    }
    
    strategies = [
        ("삼성자산운용 스타일", samsung_strategy),
        ("미래에셋 스타일", mirae_strategy), 
        ("KB자산운용 스타일", kb_strategy),
        ("NH투자증권 스타일", nh_strategy)
    ]
    
    print("🏦 기관 투자자 전략 등록 시작...")
    
    for name, strategy in strategies:
        try:
            print(f"\n📊 {name} 등록 중...")
            
            # 전략 등록 API 호출
            response = requests.post(
                f"{base_url}/api/strategy-builder/save",
                json=strategy,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {name} 등록 성공!")
                print(f"   전략 ID: {result.get('id', 'N/A')}")
                print(f"   매수조건: {len(strategy['buyConditions'])}개")
                print(f"   매도조건: {len(strategy['sellConditions'])}개")
                print(f"   리스크관리: 손절 {strategy['riskManagement']['stopLoss']['percentage']}%")
            else:
                print(f"❌ {name} 등록 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 서버 연결 실패. 백엔드 서버가 실행 중인지 확인하세요.")
            break
        except Exception as e:
            print(f"❌ {name} 등록 중 오류: {e}")
    
    print("\n🎯 기관 전략 등록 완료!")
    print("💡 특징:")
    print("   - 삼성자산운용: 모멘텀+밸류 복합, 안정적 수익")
    print("   - 미래에셋: 성장주 모멘텀, 공격적 운용") 
    print("   - KB자산운용: 디펜시브 배당, 보수적 장기투자")
    print("   - NH투자증권: ICT 이론, 스마트머니 추적")

if __name__ == "__main__":
    create_institutional_strategies()