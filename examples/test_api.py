"""
FastAPI 서버 테스트 예제
"""
import asyncio
import httpx
from datetime import datetime, timedelta


async def test_api():
    """API 엔드포인트 테스트"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. 헬스 체크
        print("=== Health Check ===")
        response = await client.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 2. 계좌 요약 조회
        print("=== Account Summary ===")
        response = await client.get(f"{base_url}/api/account/summary")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 3. 포지션 조회
        print("=== Positions ===")
        response = await client.get(f"{base_url}/api/account/positions")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 4. 주문 생성
        print("=== Create Order ===")
        order_data = {
            "symbol": "005930",
            "side": "buy",
            "quantity": 10,
            "order_type": "market"
        }
        response = await client.post(f"{base_url}/api/orders/", json=order_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 5. 종목 목록 조회
        print("=== Symbols ===")
        response = await client.get(f"{base_url}/api/price/symbols")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        # 6. OHLC 데이터 조회
        print("=== OHLC Data ===")
        response = await client.get(
            f"{base_url}/api/price/005930/ohlc",
            params={"interval": "1d", "limit": 5}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Symbol: {data.get('symbol')}")
        print(f"Count: {data.get('count')}\n")
        
        # 7. 전략 시작
        print("=== Start Strategy ===")
        strategy_data = {
            "strategy_name": "MomentumStrategy",
            "parameters": {
                "lookback": 20,
                "threshold": 0.02
            },
            "symbols": ["005930", "000660"]
        }
        response = await client.post(f"{base_url}/api/strategy/start", json=strategy_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}\n")
        
        if response.status_code == 200:
            strategy_id = result["strategy_id"]
            
            # 8. 전략 조회
            print("=== Get Strategy ===")
            response = await client.get(f"{base_url}/api/strategy/{strategy_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}\n")
            
            # 9. 전략 중지
            print("=== Stop Strategy ===")
            response = await client.post(f"{base_url}/api/strategy/{strategy_id}/stop")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}\n")


if __name__ == "__main__":
    print("FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("서버 시작: python -m uvicorn api.main:app --reload\n")
    
    asyncio.run(test_api())
