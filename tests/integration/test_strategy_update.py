#!/usr/bin/env python3
"""
기존 전략 업데이트 및 테스트 스크립트
"""

import asyncio
import json
from datetime import datetime
import httpx

async def update_existing_strategy():
    """기존 전략 업데이트"""
    
    async with httpx.AsyncClient() as client:
        # 로그인
        login_response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 기존 전략 목록 조회
        list_response = await client.get(
            "http://localhost:8000/api/strategy-builder/list",
            headers=headers
        )
        
        if list_response.status_code == 200:
            strategies = list_response.json()
            print(f"📋 기존 전략 목록:")
            for strategy in strategies:
                print(f"   ID: {strategy['id']}, Name: {strategy['name']}")
            
            if strategies:
                # 첫 번째 전략 업데이트
                strategy_id = strategies[0]['id']
                
                # 업데이트할 전략 설정
                updated_config = {
                    "strategy_id": strategy_id,  # 수정 모드
                    "name": "고급포트폴리오전략_v2",
                    "description": "업데이트된 고급 포트폴리오 전략 - 리스크 관리 강화",
                    "stockSelection": {
                        "marketCap": {"min": 2000.0, "max": 100000000.0},  # 2000억~100조
                        "volume": {"min": 200000},  # 최소 거래량 증가
                        "volumeValue": {"min": 200.0},  # 최소 거래대금 200억
                        "price": {"min": 5000.0, "max": 500000.0},  # 5000원~50만원
                        "sector": None,
                        "market": ["KOSPI", "KOSDAQ"],
                        "per": {"min": 3.0, "max": 25.0},  # PER 3~25
                        "pbr": {"min": 0.3, "max": 3.0},  # PBR 0.3~3
                        "roe": {"min": 10.0},  # ROE 10% 이상
                        "debtRatio": {"max": 70.0},  # 부채비율 70% 이하
                        "pricePosition": {
                            "from52WeekHigh": {"min": 20, "max": 60},  # 52주 고점 대비 20~60%
                            "from52WeekLow": {"min": 60, "max": 95}   # 52주 저점 대비 60~95%
                        },
                        "excludeManaged": True,
                        "excludeClearing": True,
                        "excludePreferred": True,
                        "excludeSpac": True,
                        "minListingDays": 180  # 상장 6개월 이상
                    },
                    "buyConditions": [
                        {
                            "id": "ma50_condition",
                            "type": "indicator",
                            "indicator": "ma",
                            "operator": ">",
                            "value": "MA(50)",
                            "period": 50
                        },
                        {
                            "id": "rsi_condition", 
                            "type": "indicator",
                            "indicator": "rsi",
                            "operator": "<",
                            "value": "70",
                            "period": 14
                        }
                    ],
                    "sellConditions": [
                        {
                            "id": "ma20_sell",
                            "type": "indicator",
                            "indicator": "ma",
                            "operator": "<",
                            "value": "MA(20)",
                            "period": 20
                        }
                    ],
                    "entryStrategy": {
                        "type": "single",
                        "maxPositionSize": 20.0,  # 단일 종목 최대 20%
                        "minInterval": 3
                    },
                    "positionManagement": {
                        "sizingMethod": "volatility",
                        "positionSize": 0.08,  # 8%
                        "accountRisk": 1.5,    # 1.5%
                        "atrPeriod": 14,
                        "atrMultiple": 2.5,
                        "winRate": 0.65,
                        "winLossRatio": 2.0,
                        "kellyFraction": 0.3,
                        "volatilityPeriod": 30,
                        "volatilityTarget": 1.5,
                        "maxPositions": 8,  # 최대 8개 종목
                        "stopLoss": {
                            "enabled": True,
                            "method": "atr",
                            "fixedPercent": 6.0,
                            "atrMultiple": 2.5,
                            "minPercent": 4.0,
                            "maxPercent": 12.0,
                            "timeDays": 21
                        },
                        "takeProfit": {
                            "enabled": True,
                            "method": "r_multiple",
                            "fixedPercent": 15.0,
                            "rMultiple": 2.5,
                            "partialLevels": [
                                {"percent": 60, "ratio": 2},
                                {"percent": 40, "ratio": 3}
                            ]
                        },
                        "trailingStop": {
                            "enabled": True,
                            "method": "atr",
                            "atrMultiple": 2.5,
                            "percentage": 6.0,
                            "activationProfit": 8.0,
                            "updateFrequency": "every_bar"
                        }
                    }
                }
                
                # 전략 업데이트 요청
                update_response = await client.post(
                    "http://localhost:8000/api/strategy-builder/save",
                    headers=headers,
                    json=updated_config
                )
                
                if update_response.status_code == 200:
                    result = update_response.json()
                    print(f"✅ 전략 업데이트 성공!")
                    print(f"   Strategy ID: {result['strategy_id']}")
                    print(f"   Name: {result['name']}")
                    print(f"   Description: {result['description']}")
                    return result['strategy_id']
                else:
                    print(f"❌ 전략 업데이트 실패: {update_response.status_code}")
                    print(f"   Error: {update_response.text}")
                    return None
        
        return None

async def test_updated_strategy(strategy_id: int):
    """업데이트된 전략으로 백테스트"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
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
        
        # 포트폴리오 백테스트 실행
        backtest_request = {
            "strategy_id": strategy_id,
            "start_date": "2025-08-14T00:00:00",
            "end_date": "2025-11-21T00:00:00",
            "initial_capital": 100000000,  # 1억원
            "commission": 0.0015,
            "slippage": 0.0005,
            "rebalance_days": 7  # 주간 리밸런싱
        }
        
        print(f"🚀 업데이트된 전략 백테스트 실행 중...")
        print(f"   Strategy ID: {strategy_id}")
        print(f"   Period: {backtest_request['start_date']} ~ {backtest_request['end_date']}")
        
        backtest_response = await client.post(
            "http://localhost:8000/api/backtest/portfolio",
            headers=headers,
            json=backtest_request
        )
        
        if backtest_response.status_code == 200:
            result = backtest_response.json()
            print(f"✅ 포트폴리오 백테스트 성공!")
            print(f"   Backtest ID: {result['backtest_id']}")
            print(f"   Total Return: {result['total_return']:.2%}")
            print(f"   MDD: {result['mdd']:.2%}")
            print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"   Total Trades: {result['total_trades']}")
            return result['backtest_id']
        else:
            print(f"❌ 백테스트 실패: {backtest_response.status_code}")
            print(f"   Error: {backtest_response.text}")
            return None

async def test_risk_analysis(backtest_id: int):
    """리스크 분석 테스트"""
    
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
        
        # 리스크 분석 요청
        risk_request = {
            "backtest_ids": [backtest_id],
            "sector_mapping": {
                "005930": "반도체",
                "000660": "반도체", 
                "035420": "인터넷",
                "051910": "화학",
                "006400": "배터리"
            }
        }
        
        print(f"📊 리스크 분석 실행 중...")
        print(f"   Backtest ID: {backtest_id}")
        
        risk_response = await client.post(
            "http://localhost:8000/api/advanced-backtest/risk-analysis",
            headers=headers,
            json=risk_request
        )
        
        if risk_response.status_code == 200:
            result = risk_response.json()
            print(f"✅ 리스크 분석 완료!")
            print(f"   Portfolio VaR: {result['portfolio_var']:.2%}")
            print(f"   Max Drawdown: {result['max_drawdown']:.2%}")
            print(f"   Volatility: {result['volatility']:.2%}")
            print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            print(f"   Risk Level: {result['risk_level']}")
            print(f"   Concentration Risk: {result['concentration_risk']:.2%}")
            
            if result['sector_exposure']:
                print(f"   Sector Exposure:")
                for sector, exposure in result['sector_exposure'].items():
                    print(f"     {sector}: {exposure:.1%}")
            
            return result
        else:
            print(f"❌ 리스크 분석 실패: {risk_response.status_code}")
            print(f"   Error: {risk_response.text}")
            return None

async def main():
    """메인 함수"""
    print("=" * 70)
    print("🏗️ LS증권 HTS 플랫폼 - 전략 업데이트 및 고급 기능 테스트")
    print("=" * 70)
    
    # 1. 기존 전략 업데이트
    print("\n1️⃣ 기존 전략 업데이트")
    strategy_id = await update_existing_strategy()
    
    if strategy_id:
        # 2. 업데이트된 전략으로 백테스트
        print("\n2️⃣ 업데이트된 전략 백테스트")
        backtest_id = await test_updated_strategy(strategy_id)
        
        if backtest_id:
            # 3. 리스크 분석
            print("\n3️⃣ 포트폴리오 리스크 분석")
            risk_result = await test_risk_analysis(backtest_id)
    
    print("\n" + "=" * 70)
    print("🎉 모든 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())