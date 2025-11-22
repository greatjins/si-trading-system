"""
WebSocket 실시간 통신 테스트
"""
import asyncio
import websockets
import json
import httpx


async def test_websocket():
    """WebSocket 테스트"""
    
    base_url = "http://localhost:8000"
    ws_url = "ws://localhost:8000"
    
    # 1. 로그인하여 토큰 획득
    print("=== Login ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        if response.status_code != 200:
            print("Login failed. Please register first:")
            print("python examples/test_auth.py")
            return
        
        tokens = response.json()
        access_token = tokens["access_token"]
        print(f"Access Token: {access_token[:50]}...\n")
    
    # 2. WebSocket 연결
    print("=== WebSocket Connection ===")
    uri = f"{ws_url}/api/ws?token={access_token}"
    
    async with websockets.connect(uri) as websocket:
        # 환영 메시지 수신
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 3. 시세 구독
        print("=== Subscribe to Price ===")
        await websocket.send(json.dumps({
            "type": "subscribe",
            "topic": "price:005930"
        }))
        
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 4. 현재가 조회
        print("=== Get Current Price ===")
        await websocket.send(json.dumps({
            "type": "get_price",
            "symbol": "005930"
        }))
        
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 5. 계좌 정보 조회
        print("=== Get Account ===")
        await websocket.send(json.dumps({
            "type": "get_account"
        }))
        
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 6. Ping/Pong 테스트
        print("=== Ping/Pong ===")
        await websocket.send(json.dumps({
            "type": "ping",
            "timestamp": "2024-01-01T00:00:00"
        }))
        
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 7. 실시간 시세 수신 (10초간)
        print("=== Real-time Price Updates (10 seconds) ===")
        try:
            for i in range(10):
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                
                if data.get("type") == "price_update":
                    price_data = data["data"]
                    print(f"[{i+1}] {data['symbol']}: {price_data['price']:,.0f}원 "
                          f"({price_data['change_percent']:+.2f}%)")
        
        except asyncio.TimeoutError:
            print("No price updates received")
        
        print()
        
        # 8. 구독 해제
        print("=== Unsubscribe ===")
        await websocket.send(json.dumps({
            "type": "unsubscribe",
            "topic": "price:005930"
        }))
        
        message = await websocket.recv()
        print(f"Received: {message}\n")
        
        # 9. 다중 종목 구독
        print("=== Subscribe to Multiple Symbols ===")
        symbols = ["005930", "000660", "035420"]
        
        for symbol in symbols:
            await websocket.send(json.dumps({
                "type": "subscribe",
                "topic": f"price:{symbol}"
            }))
            message = await websocket.recv()
            print(f"Subscribed to {symbol}")
        
        print()
        
        # 10. 다중 종목 실시간 시세 (5초간)
        print("=== Multi-Symbol Real-time Updates (5 seconds) ===")
        try:
            for i in range(5):
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                
                if data.get("type") == "price_update":
                    price_data = data["data"]
                    print(f"[{i+1}] {data['symbol']}: {price_data['price']:,.0f}원 "
                          f"({price_data['change_percent']:+.2f}%)")
        
        except asyncio.TimeoutError:
            print("No price updates received")
        
        print("\n=== Test Complete ===")


async def test_websocket_status():
    """WebSocket 상태 조회"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/api/ws/status")
        
        if response.status_code == 200:
            status = response.json()
            print("\n=== WebSocket Status ===")
            print(f"Active Connections: {status['active_connections']}")
            print(f"Active Users: {status['active_users']}")
            print(f"Price Streamer: {'Running' if status['price_streamer_running'] else 'Stopped'}")
            print(f"Subscriptions: {status['subscriptions']}")


if __name__ == "__main__":
    print("FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("서버 시작: python -m uvicorn api.main:app --reload\n")
    
    asyncio.run(test_websocket())
    asyncio.run(test_websocket_status())
