"""
통합 테스트 - 전체 시스템 테스트
"""
import asyncio
import httpx
import websockets
import json
from datetime import datetime


class IntegrationTest:
    """통합 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.access_token = None
        self.refresh_token = None
        self.test_user = {
            "username": "testuser_integration",
            "email": "integration@test.com",
            "password": "testpass123",
            "full_name": "Integration Test User"
        }
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 80)
        print("LS HTS 플랫폼 통합 테스트 시작")
        print("=" * 80)
        print()
        
        try:
            # Phase 1: 인증 테스트
            await self.test_authentication()
            
            # Phase 2: 전략 레지스트리 테스트
            await self.test_strategy_registry()
            
            # Phase 3: REST API 테스트
            await self.test_rest_api()
            
            # Phase 4: WebSocket 테스트
            await self.test_websocket()
            
            print("\n" + "=" * 80)
            print("✅ 모든 통합 테스트 통과!")
            print("=" * 80)
        
        except Exception as e:
            print("\n" + "=" * 80)
            print(f"❌ 테스트 실패: {e}")
            print("=" * 80)
            raise
    
    async def test_authentication(self):
        """인증 시스템 테스트"""
        print("📋 Phase 1: 인증 시스템 테스트")
        print("-" * 80)
        
        async with httpx.AsyncClient() as client:
            # 1. 사용자 등록
            print("1. 사용자 등록...")
            response = await client.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user
            )
            
            if response.status_code == 200:
                print("   ✅ 사용자 등록 성공")
            elif response.status_code == 400 and "already registered" in response.text:
                print("   ℹ️  사용자 이미 존재 (계속 진행)")
            else:
                raise Exception(f"사용자 등록 실패: {response.text}")
            
            # 2. 로그인
            print("2. 로그인...")
            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"로그인 실패: {response.text}")
            
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens.get("refresh_token")
            print(f"   ✅ 로그인 성공 (토큰: {self.access_token[:30]}...)")
            
            # 3. 현재 사용자 정보 조회
            print("3. 현재 사용자 정보 조회...")
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await client.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"사용자 정보 조회 실패: {response.text}")
            
            user = response.json()
            print(f"   ✅ 사용자: {user['username']} (역할: {user['role']})")
        
        print("✅ Phase 1 완료\n")
    
    async def test_strategy_registry(self):
        """전략 레지스트리 테스트"""
        print("📋 Phase 2: 전략 레지스트리 테스트")
        print("-" * 80)
        
        async with httpx.AsyncClient() as client:
            # 1. 전략 목록 조회
            print("1. 전략 목록 조회...")
            response = await client.get(f"{self.base_url}/api/strategies/list")
            
            if response.status_code != 200:
                raise Exception(f"전략 목록 조회 실패: {response.text}")
            
            strategies = response.json()
            print(f"   ✅ 등록된 전략: {len(strategies)}개")
            
            for strategy in strategies:
                print(f"      - {strategy['name']} (v{strategy['version']})")
            
            if not strategies:
                print("   ⚠️  등록된 전략이 없습니다. 전략을 재탐색합니다...")
                response = await client.post(f"{self.base_url}/api/strategies/discover")
                if response.status_code == 200:
                    print(f"   ✅ {response.json()['message']}")
                    # 다시 조회
                    response = await client.get(f"{self.base_url}/api/strategies/list")
                    strategies = response.json()
            
            # 2. 전략 상세 정보 조회
            if strategies:
                strategy_name = strategies[0]["name"]
                print(f"\n2. 전략 상세 정보 조회: {strategy_name}...")
                response = await client.get(
                    f"{self.base_url}/api/strategies/{strategy_name}"
                )
                
                if response.status_code != 200:
                    raise Exception(f"전략 상세 조회 실패: {response.text}")
                
                detail = response.json()
                print(f"   ✅ 파라미터: {len(detail['parameters'])}개")
                for param_name in detail['parameters'].keys():
                    print(f"      - {param_name}")
        
        print("✅ Phase 2 완료\n")
    
    async def test_rest_api(self):
        """REST API 테스트"""
        print("📋 Phase 3: REST API 테스트")
        print("-" * 80)
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient() as client:
            # 1. 계좌 정보 조회
            print("1. 계좌 정보 조회...")
            response = await client.get(
                f"{self.base_url}/api/account/summary",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"계좌 조회 실패: {response.text}")
            
            account = response.json()
            print(f"   ✅ 잔고: {account['balance']:,.0f}원")
            print(f"      자산: {account['equity']:,.0f}원")
            
            # 2. 포지션 조회
            print("2. 포지션 조회...")
            response = await client.get(
                f"{self.base_url}/api/account/positions",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"포지션 조회 실패: {response.text}")
            
            positions = response.json()
            print(f"   ✅ 보유 포지션: {len(positions)}개")
            
            # 3. 종목 목록 조회
            print("3. 종목 목록 조회...")
            response = await client.get(f"{self.base_url}/api/price/symbols")
            
            if response.status_code != 200:
                raise Exception(f"종목 목록 조회 실패: {response.text}")
            
            symbols = response.json()
            print(f"   ✅ 종목 수: {symbols['count']}개")
            
            # 4. OHLC 데이터 조회
            if symbols['count'] > 0:
                symbol = symbols['symbols'][0]
                print(f"4. OHLC 데이터 조회: {symbol}...")
                response = await client.get(
                    f"{self.base_url}/api/price/{symbol}/ohlc",
                    params={"interval": "1d", "limit": 5}
                )
                
                if response.status_code != 200:
                    print(f"   ⚠️  OHLC 조회 실패 (데이터 없음): {response.status_code}")
                else:
                    data = response.json()
                    print(f"   ✅ 데이터: {data.get('count', 0)}개")
            
            # 5. 주문 생성 (테스트)
            print("5. 주문 생성 테스트...")
            response = await client.post(
                f"{self.base_url}/api/orders/",
                headers=headers,
                json={
                    "symbol": "005930",
                    "side": "buy",
                    "quantity": 1,
                    "order_type": "market"
                }
            )
            
            if response.status_code != 200:
                print(f"   ⚠️  주문 생성 실패 (예상됨): {response.status_code}")
            else:
                order = response.json()
                print(f"   ✅ 주문 ID: {order['order_id']}")
        
        print("✅ Phase 3 완료\n")
    
    async def test_websocket(self):
        """WebSocket 테스트"""
        print("📋 Phase 4: WebSocket 실시간 통신 테스트")
        print("-" * 80)
        
        uri = f"{self.ws_url}/api/ws?token={self.access_token}"
        
        try:
            async with websockets.connect(uri) as websocket:
                # 1. 연결 확인
                print("1. WebSocket 연결...")
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") != "connected":
                    raise Exception(f"연결 실패: {data}")
                
                print(f"   ✅ {data['message']}")
                
                # 2. 시세 구독
                print("2. 시세 구독: 005930...")
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "topic": "price:005930"
                }))
                
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") != "subscribed":
                    raise Exception(f"구독 실패: {data}")
                
                print(f"   ✅ {data['message']}")
                
                # 3. 현재가 조회
                print("3. 현재가 조회...")
                await websocket.send(json.dumps({
                    "type": "get_price",
                    "symbol": "005930"
                }))
                
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "price":
                    price_data = data["data"]
                    print(f"   ✅ 현재가: {price_data['price']:,.0f}원")
                
                # 4. 실시간 시세 수신 (3초간)
                print("4. 실시간 시세 수신 (3초)...")
                received_count = 0
                
                try:
                    for i in range(3):
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "price_update":
                            received_count += 1
                            price_data = data["data"]
                            print(f"   [{i+1}] {data['symbol']}: {price_data['price']:,.0f}원 "
                                  f"({price_data['change_percent']:+.2f}%)")
                
                except asyncio.TimeoutError:
                    pass
                
                if received_count > 0:
                    print(f"   ✅ {received_count}개 업데이트 수신")
                else:
                    print("   ⚠️  실시간 업데이트 없음 (스트리머 미실행)")
                
                # 5. Ping/Pong
                print("5. Ping/Pong 테스트...")
                await websocket.send(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }))
                
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "pong":
                    print("   ✅ Pong 수신")
                
                # 6. 구독 해제
                print("6. 구독 해제...")
                await websocket.send(json.dumps({
                    "type": "unsubscribe",
                    "topic": "price:005930"
                }))
                
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "unsubscribed":
                    print(f"   ✅ {data['message']}")
        
        except asyncio.TimeoutError:
            raise Exception("WebSocket 응답 타임아웃")
        except Exception as e:
            raise Exception(f"WebSocket 테스트 실패: {e}")
        
        print("✅ Phase 4 완료\n")


async def main():
    """메인 함수"""
    print("\n")
    print("🚀 LS HTS 플랫폼 통합 테스트")
    print()
    print("서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("서버 시작: python -m uvicorn api.main:app --reload")
    print()
    
    # 서버 연결 확인
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ 서버가 응답하지 않습니다.")
                return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("서버를 먼저 시작해주세요.")
        return
    
    # 통합 테스트 실행
    test = IntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
