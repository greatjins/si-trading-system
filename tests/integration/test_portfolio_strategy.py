#!/usr/bin/env python3
"""
포트폴리오 전략 생성 및 테스트 스크립트
"""

import asyncio
import json
from datetime import datetime
import httpx

async def create_portfolio_strategy():
    """포트폴리오 전략 생성"""
    
    # 로그인
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
        
        # 포트폴리오 전략 설정
        strategy_config = {
            "name": "200일선초과일목상향돌파",
            "description": "200일 이동평균선을 초과하고 일목균형표 상향 돌파하는 종목들의 포트폴리오 전략",
            "stockSelection": {
                "marketCap": {"min": 1000.0, "max": 100000000.0},  # 1000억~100조
                "volume": {"min": 100000},  # 최소 거래량
                "volumeValue": {"min": 100.0},  # 최소 거래대금 100억
                "price": {"min": 1000.0, "max": 100000000.0},  # 1000원~1억원
                "sector": None,
                "market": ["KOSPI", "KOSDAQ"],
                "per": {"min": 1.0, "max": 50.0},  # PER 1~50
                "pbr": {"min": 0.1, "max": 5.0},  # PBR 0.1~5
                "roe": {"min": 5.0},  # ROE 5% 이상
                "debtRatio": {"max": 100.0},  # 부채비율 100% 이하
                "pricePosition": {
                    "from52WeekHigh": {"min": 10, "max": 50},  # 52주 고점 대비 10~50%
                    "from52WeekLow": {"min": 50, "max": 90}   # 52주 저점 대비 50~90%
                },
                "excludeManaged": True,
                "excludeClearing": True,
                "excludePreferred": False,
                "excludeSpac": True,
                "minListingDays": 90
            },
            "buyConditions": [
                {
                    "id": "ma200_condition",
                    "type": "indicator",
                    "indicator": "ma",
                    "operator": ">",
                    "value": "MA(200)",
                    "period": 200
                },
                {
                    "id": "ichimoku_condition", 
                    "type": "indicator",
                    "indicator": "ichimoku",
                    "operator": ">",
                    "value": "CLOUD_TOP",
                    "period": 26
                }
            ],
            "sellConditions": [],
            "entryStrategy": {
                "type": "pyramid",
                "pyramidLevels": [
                    {"level": 1, "condition": "initial", "priceChange": 0.0, "units": 1.0, "description": "첫 진입"},
                    {"level": 2, "condition": "price_increase", "priceChange": 5.0, "units": 1.0, "description": "5% 상승 시"},
                    {"level": 3, "condition": "price_increase", "priceChange": 10.0, "units": 1.0, "description": "10% 상승 시"},
                    {"level": 4, "condition": "price_increase", "priceChange": 15.0, "units": 0.5, "description": "15% 상승 시"}
                ],
                "maxLevels": 4,
                "maxPositionSize": 40.0,
                "minInterval": 1
            },
            "positionManagement": {
                "sizingMethod": "atr_risk",
                "positionSize": 0.05,  # 5%
                "accountRisk": 2.0,    # 2%
                "atrPeriod": 20,
                "atrMultiple": 2.0,
                "winRate": 0.6,
                "winLossRatio": 2.5,
                "kellyFraction": 0.25,
                "volatilityPeriod": 20,
                "volatilityTarget": 2.0,
                "maxPositions": 10,
                "stopLoss": {
                    "enabled": True,
                    "method": "atr",
                    "fixedPercent": 8.0,
                    "atrMultiple": 2.0,
                    "minPercent": 5.0,
                    "maxPercent": 15.0,
                    "timeDays": 30
                },
                "takeProfit": {
                    "enabled": True,
                    "method": "r_multiple",
                    "fixedPercent": 20.0,
                    "rMultiple": 3.0,
                    "partialLevels": [
                        {"percent": 50, "ratio": 2},
                        {"percent": 50, "ratio": 3}
                    ]
                },
                "trailingStop": {
                    "enabled": True,
                    "method": "atr",
                    "atrMultiple": 3.0,
                    "percentage": 8.0,
                    "activationProfit": 10.0,
                    "updateFrequency": "every_bar"
                }
            }
        }
        
        # 전략 생성 요청
        create_response = await client.post(
            "http://localhost:8000/api/strategy-builder/save",
            headers=headers,
            json=strategy_config
        )
        
        if create_response.status_code == 200:
            result = create_response.json()
            print(f"✅ 포트폴리오 전략 생성 성공!")
            print(f"   Strategy ID: {result['strategy_id']}")
            print(f"   Name: {result['name']}")
            print(f"   Description: {result['description']}")
            return result['strategy_id']
        else:
            print(f"❌ 전략 생성 실패: {create_response.status_code}")
            print(f"   Error: {create_response.text}")
            return None

async def test_portfolio_backtest(strategy_id: int):
    """포트폴리오 백테스트 테스트"""
    
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
            "rebalance_days": 5
        }
        
        print(f"🚀 포트폴리오 백테스트 실행 중...")
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

async def test_parallel_backtest():
    """병렬 백테스트 테스트"""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
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
        
        # 사용 가능한 전략 조회
        strategies_response = await client.get(
            "http://localhost:8000/api/strategies/list",
            headers=headers
        )
        
        if strategies_response.status_code == 200:
            strategies = strategies_response.json()
            strategy_names = [s["name"] for s in strategies[:3]]  # 처음 3개 전략
            
            print(f"🚀 병렬 백테스트 실행 중...")
            print(f"   Strategies: {strategy_names}")
            
            # 병렬 백테스트 요청
            parallel_request = {
                "strategy_names": strategy_names,
                "symbol": "005930",  # 삼성전자
                "start_date": "2025-08-14T00:00:00",
                "end_date": "2025-11-21T00:00:00",
                "initial_capital": 10000000,
                "max_workers": 2
            }
            
            parallel_response = await client.post(
                "http://localhost:8000/api/advanced-backtest/parallel",
                headers=headers,
                json=parallel_request
            )
            
            if parallel_response.status_code == 200:
                result = parallel_response.json()
                task_id = result["task_id"]
                
                print(f"✅ 병렬 백테스트 시작!")
                print(f"   Task ID: {task_id}")
                print(f"   Total Strategies: {result['total_strategies']}")
                
                # 상태 확인
                import time
                for i in range(30):  # 최대 30초 대기
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(
                        f"http://localhost:8000/api/advanced-backtest/parallel/{task_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"   Status: {status['status']}, Completed: {status['completed']}/{status['total_strategies']}")
                        
                        if status["status"] == "completed":
                            print(f"✅ 병렬 백테스트 완료!")
                            for result in status["results"]:
                                print(f"     {result['strategy_name']}: Return={result['total_return']:.2%}, MDD={result['mdd']:.2%}")
                            break
                        elif status["status"] == "failed":
                            print(f"❌ 병렬 백테스트 실패: {status.get('error', 'Unknown error')}")
                            break
                
                return task_id
            else:
                print(f"❌ 병렬 백테스트 시작 실패: {parallel_response.status_code}")
                print(f"   Error: {parallel_response.text}")
        
        return None

async def main():
    """메인 함수"""
    print("=" * 60)
    print("🏗️ LS증권 HTS 플랫폼 - 고급 기능 테스트")
    print("=" * 60)
    
    # 1. 포트폴리오 전략 생성
    print("\n1️⃣ 포트폴리오 전략 생성 테스트")
    strategy_id = await create_portfolio_strategy()
    
    if strategy_id:
        # 2. 포트폴리오 백테스트
        print("\n2️⃣ 포트폴리오 백테스트 테스트")
        backtest_id = await test_portfolio_backtest(strategy_id)
    
    # 3. 병렬 백테스트
    print("\n3️⃣ 병렬 백테스트 테스트")
    task_id = await test_parallel_backtest()
    
    print("\n" + "=" * 60)
    print("🎉 모든 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())