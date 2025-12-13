#!/usr/bin/env python3
"""
기관 투자자 전략을 데이터베이스에 직접 등록
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

def create_institutional_strategies_db():
    """기관 투자자 전략을 DB에 직접 등록"""
    
    # 데이터베이스 연결
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/trading_system"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 전략 데이터
    strategies = [
        {
            "name": "🏦 삼성자산운용 모멘텀-밸류 복합전략",
            "description": "RSI 과매도 + PER 저평가 + 거래량 급증 포착. 중대형주 중심 안정적 중장기 수익 추구. MDD 5% 이하 목표",
            "config": {
                "stockSelection": {
                    "marketCap": {"min": 3000, "max": 100000},
                    "volume": {"min": 500000},
                    "volumeValue": {"min": 5000},
                    "price": {"min": 10000, "max": 200000},
                    "market": ["KOSPI", "KOSDAQ"],
                    "per": {"min": 3, "max": 15},
                    "pbr": {"min": 0.3, "max": 2.0},
                    "roe": {"min": 8}
                },
                "buyConditions": [
                    {"id": "buy_1", "type": "indicator", "indicator": "rsi", "operator": "<", "value": 35, "period": 14},
                    {"id": "buy_2", "type": "indicator", "indicator": "ma", "operator": ">", "value": "close", "period": 20},
                    {"id": "buy_3", "type": "volume", "indicator": "volume_ma", "operator": ">", "value": 1.5, "period": 10}
                ],
                "sellConditions": [
                    {"id": "sell_1", "type": "indicator", "indicator": "rsi", "operator": ">", "value": 70, "period": 14},
                    {"id": "sell_2", "type": "price", "indicator": "close", "operator": "<", "value": "ma", "period": 20}
                ],
                "riskManagement": {
                    "stopLoss": {"enabled": True, "percentage": 8.0},
                    "takeProfit": {"enabled": True, "percentage": 25.0},
                    "maxPositions": 8
                },
                "positionManagement": {
                    "sizingMethod": "equal_weight",
                    "maxPositionSize": 12.5
                }
            }
        },
        {
            "name": "🏛️ 미래에셋 성장주 모멘텀 전략",
            "description": "MACD 골든크로스 + 볼린저밴드 돌파 + 높은 ROE. 성장주 중심 공격적 운용. 연 25% 수익률 목표",
            "config": {
                "stockSelection": {
                    "marketCap": {"min": 1000, "max": 50000},
                    "volume": {"min": 300000},
                    "volumeValue": {"min": 3000},
                    "price": {"min": 5000, "max": 150000},
                    "market": ["KOSPI", "KOSDAQ"],
                    "roe": {"min": 15},
                    "per": {"max": 25}
                },
                "buyConditions": [
                    {"id": "buy_1", "type": "indicator", "indicator": "macd", "operator": "golden_cross", "value": 0, "fastPeriod": 12, "slowPeriod": 26, "signalPeriod": 9},
                    {"id": "buy_2", "type": "indicator", "indicator": "bollinger", "operator": ">", "value": "upper", "period": 20, "stdDev": 2},
                    {"id": "buy_3", "type": "volume", "indicator": "volume_ma", "operator": ">", "value": 2.0, "period": 5}
                ],
                "sellConditions": [
                    {"id": "sell_1", "type": "indicator", "indicator": "macd", "operator": "dead_cross", "value": 0},
                    {"id": "sell_2", "type": "indicator", "indicator": "bollinger", "operator": "<", "value": "middle", "period": 20}
                ],
                "riskManagement": {
                    "stopLoss": {"enabled": True, "percentage": 12.0},
                    "takeProfit": {"enabled": True, "percentage": 40.0},
                    "maxPositions": 6
                },
                "positionManagement": {
                    "sizingMethod": "volatility_adjusted",
                    "maxPositionSize": 16.7
                }
            }
        },
        {
            "name": "🏢 KB자산운용 디펜시브 배당 전략",
            "description": "안정적 배당 + 낮은 변동성 + 우량주. 대형주만 선별하여 보수적 장기투자. 연 12% 안정 수익",
            "config": {
                "stockSelection": {
                    "marketCap": {"min": 10000, "max": 500000},
                    "volume": {"min": 200000},
                    "volumeValue": {"min": 10000},
                    "price": {"min": 20000, "max": 500000},
                    "market": ["KOSPI"],
                    "per": {"min": 5, "max": 12},
                    "pbr": {"min": 0.5, "max": 1.5},
                    "roe": {"min": 10}
                },
                "buyConditions": [
                    {"id": "buy_1", "type": "indicator", "indicator": "ma", "operator": ">", "value": "ma", "period": 20, "comparePeriod": 60},
                    {"id": "buy_2", "type": "indicator", "indicator": "rsi", "operator": "<", "value": 45, "period": 14},
                    {"id": "buy_3", "type": "price", "indicator": "close", "operator": ">", "value": "ma", "period": 120}
                ],
                "sellConditions": [
                    {"id": "sell_1", "type": "indicator", "indicator": "ma", "operator": "<", "value": "ma", "period": 20, "comparePeriod": 60},
                    {"id": "sell_2", "type": "indicator", "indicator": "rsi", "operator": ">", "value": 65, "period": 14}
                ],
                "riskManagement": {
                    "stopLoss": {"enabled": True, "percentage": 15.0},
                    "takeProfit": {"enabled": False},
                    "maxPositions": 12
                },
                "positionManagement": {
                    "sizingMethod": "equal_weight",
                    "maxPositionSize": 8.3
                }
            }
        },
        {
            "name": "🎯 NH투자증권 ICT 스마트머니 전략",
            "description": "ICT 이론 기반 기관 자금 추적. BOS 돌파 + 스마트머니 플로우 + 유동성 풀 활용. 단기 고수익 추구",
            "config": {
                "stockSelection": {
                    "marketCap": {"min": 2000, "max": 80000},
                    "volume": {"min": 1000000},
                    "volumeValue": {"min": 8000},
                    "price": {"min": 15000, "max": 300000},
                    "market": ["KOSPI", "KOSDAQ"],
                    "per": {"max": 20}
                },
                "buyConditions": [
                    {"id": "buy_1", "type": "indicator", "indicator": "bos", "operator": "break_high", "value": 0, "lookback": 20},
                    {"id": "buy_2", "type": "indicator", "indicator": "smart_money", "operator": "bullish", "value": 0, "period": 15},
                    {"id": "buy_3", "type": "indicator", "indicator": "fvg", "operator": "in_gap", "value": 0, "min_gap": 0.015}
                ],
                "sellConditions": [
                    {"id": "sell_1", "type": "indicator", "indicator": "liquidity_pool", "operator": "sweep_pool", "value": 0, "cluster_threshold": 0.02},
                    {"id": "sell_2", "type": "indicator", "indicator": "smart_money", "operator": "bearish", "value": 0, "period": 10}
                ],
                "riskManagement": {
                    "stopLoss": {"enabled": True, "percentage": 6.0},
                    "takeProfit": {"enabled": True, "percentage": 18.0},
                    "maxPositions": 10
                },
                "positionManagement": {
                    "sizingMethod": "atr_based",
                    "maxPositionSize": 10.0
                }
            }
        }
    ]
    
    try:
        db = SessionLocal()
        
        print("🏦 기관 투자자 전략 DB 등록 시작...")
        
        for strategy in strategies:
            # 전략 등록 SQL
            insert_sql = text("""
                INSERT INTO strategies (name, description, config, created_at, updated_at, is_active)
                VALUES (:name, :description, :config, :created_at, :updated_at, :is_active)
            """)
            
            db.execute(insert_sql, {
                "name": strategy["name"],
                "description": strategy["description"], 
                "config": json.dumps(strategy["config"], ensure_ascii=False),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            })
            
            print(f"✅ {strategy['name']} 등록 완료")
        
        db.commit()
        print("\n🎯 모든 기관 전략 등록 성공!")
        
        # 등록된 전략 확인
        result = db.execute(text("SELECT id, name FROM strategies WHERE name LIKE '%🏦%' OR name LIKE '%🏛️%' OR name LIKE '%🏢%' OR name LIKE '%🎯%'"))
        strategies_list = result.fetchall()
        
        print(f"\n📊 등록된 전략 목록 ({len(strategies_list)}개):")
        for strategy in strategies_list:
            print(f"   ID {strategy[0]}: {strategy[1]}")
            
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_institutional_strategies_db()