# Phase 7: WebSocket 실시간 통신 구현 완료

## 개요
WebSocket을 통한 실시간 양방향 통신 시스템을 구현하여 시세 스트리밍, 주문 체결 알림, 전략 실행 상태 모니터링을 지원합니다.

## 구현 내용

### 1. WebSocket 계층 구조
```
api/websocket/
├── __init__.py
├── manager.py             # 연결 관리자
├── handlers.py            # 메시지 핸들러
└── streams.py             # 실시간 스트리머

api/routes/
└── websocket.py           # WebSocket 라우터
```

### 2. 주요 컴포넌트

#### ConnectionManager
- **연결 관리**: 사용자별 WebSocket 연결 관리
- **구독 관리**: 토픽 기반 pub/sub 패턴
- **메시지 전송**: 개인/그룹/전체 브로드캐스트

#### WebSocketHandler
- **메시지 라우팅**: 타입별 핸들러 매핑
- **요청 처리**: subscribe, unsubscribe, ping, get_price, get_account
- **에러 처리**: 일관된 에러 응답

#### 스트리머
- **PriceStreamer**: 실시간 시세 스트리밍
- **OrderStreamer**: 주문 체결 알림
- **StrategyStreamer**: 전략 실행 상태 및 시그널

### 3. 토픽 구조

#### 시세 토픽
```
price:{symbol}        # 특정 종목 시세
예: price:005930      # 삼성전자 시세
```

#### 주문 토픽
```
order:*               # 모든 주문 체결
order:{order_id}      # 특정 주문
```

#### 전략 토픽
```
strategy:{strategy_id}  # 특정 전략 상태
```

### 4. 메시지 프로토콜

#### 클라이언트 → 서버

**구독 요청**
```json
{
  "type": "subscribe",
  "topic": "price:005930"
}
```

**구독 해제**
```json
{
  "type": "unsubscribe",
  "topic": "price:005930"
}
```

**현재가 조회**
```json
{
  "type": "get_price",
  "symbol": "005930"
}
```

**계좌 정보 조회**
```json
{
  "type": "get_account"
}
```

**Ping**
```json
{
  "type": "ping",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### 서버 → 클라이언트

**연결 성공**
```json
{
  "type": "connected",
  "message": "Welcome testuser!",
  "user_id": "1"
}
```

**구독 확인**
```json
{
  "type": "subscribed",
  "topic": "price:005930",
  "message": "Successfully subscribed to price:005930"
}
```

**시세 업데이트**
```json
{
  "type": "price_update",
  "symbol": "005930",
  "data": {
    "price": 75000,
    "change": 500,
    "change_percent": 0.67,
    "volume": 1234567,
    "timestamp": "2024-01-01T09:00:00"
  }
}
```

**주문 체결**
```json
{
  "type": "order_update",
  "data": {
    "order_id": "ORDER_123",
    "status": "filled",
    "filled_quantity": 10,
    "filled_price": 75000
  }
}
```

**전략 시그널**
```json
{
  "type": "strategy_signal",
  "strategy_id": "STRATEGY_456",
  "data": {
    "signal": "buy",
    "symbol": "005930",
    "quantity": 10,
    "reason": "MA crossover"
  }
}
```

**Pong**
```json
{
  "type": "pong",
  "timestamp": "2024-01-01T00:00:00"
}
```

**에러**
```json
{
  "type": "error",
  "message": "Invalid JSON format"
}
```

### 5. 연결 방법

#### WebSocket URL
```
ws://localhost:8000/api/ws?token={access_token}
```

#### Python 예제
```python
import websockets
import json

uri = f"ws://localhost:8000/api/ws?token={access_token}"

async with websockets.connect(uri) as websocket:
    # 시세 구독
    await websocket.send(json.dumps({
        "type": "subscribe",
        "topic": "price:005930"
    }))
    
    # 메시지 수신
    while True:
        message = await websocket.recv()
        data = json.loads(message)
        print(data)
```

#### JavaScript 예제
```javascript
const ws = new WebSocket(`ws://localhost:8000/api/ws?token=${accessToken}`);

ws.onopen = () => {
  // 시세 구독
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'price:005930'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### 6. 실시간 스트리밍

#### 시세 스트리밍
- **주기**: 1초마다 업데이트
- **방식**: 구독된 종목만 전송
- **데이터**: 현재가, 변동률, 거래량

#### 주문 체결 알림
- **방식**: 이벤트 기반 (체결 시 즉시 전송)
- **대상**: 해당 사용자에게만 전송

#### 전략 상태 모니터링
- **주기**: 상태 변경 시 즉시 전송
- **데이터**: 실행 상태, 포지션, 손익, 시그널

### 7. 테스트 실행

```bash
# 서버 시작
python -m uvicorn api.main:app --reload

# 다른 터미널에서 테스트
python examples/test_websocket.py
```

### 8. 예상 출력

```
=== Login ===
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

=== WebSocket Connection ===
Received: {"type":"connected","message":"Welcome testuser!","user_id":"1"}

=== Subscribe to Price ===
Received: {"type":"subscribed","topic":"price:005930","message":"Successfully subscribed to price:005930"}

=== Get Current Price ===
Received: {"type":"price","symbol":"005930","data":{"price":75000,"open":74500,...}}

=== Real-time Price Updates (10 seconds) ===
[1] 005930: 75,123원 (+0.16%)
[2] 005930: 74,987원 (-0.02%)
[3] 005930: 75,234원 (+0.31%)
...

=== WebSocket Status ===
Active Connections: 1
Active Users: ['1']
Price Streamer: Running
Subscriptions: {'price:005930': ['1']}
```

### 9. 성능 최적화

#### 연결 관리
- **다중 연결**: 사용자당 여러 WebSocket 연결 지원
- **자동 재연결**: 클라이언트 측 재연결 로직
- **연결 풀링**: 효율적인 리소스 관리

#### 메시지 전송
- **선택적 전송**: 구독자에게만 전송
- **배치 처리**: 여러 업데이트 묶어서 전송
- **압축**: 대용량 데이터 압축 전송

#### 스트리밍 최적화
- **지연 로딩**: 구독 시작 시 스트리머 활성화
- **자동 중지**: 구독자 없을 때 스트리머 중지
- **캐싱**: 최근 데이터 캐싱으로 중복 조회 방지

### 10. 보안

#### 인증
- **JWT 토큰**: 쿼리 파라미터로 전달
- **토큰 검증**: 연결 시 토큰 유효성 확인
- **자동 종료**: 인증 실패 시 연결 종료

#### 권한 관리
- **사용자별 격리**: 다른 사용자 데이터 접근 불가
- **토픽 권한**: 구독 가능한 토픽 제한
- **Rate Limiting**: 메시지 전송 빈도 제한

### 11. 모니터링

#### 상태 조회 API
```
GET /api/ws/status
```

**응답**
```json
{
  "active_connections": 5,
  "active_users": ["1", "2", "3"],
  "subscriptions": {
    "price:005930": ["1", "2"],
    "price:000660": ["3"]
  },
  "price_streamer_running": true
}
```

#### 로깅
- 연결/해제 이벤트
- 구독/구독 해제
- 메시지 전송 실패
- 에러 발생

### 12. 향후 개선 사항

#### Redis Pub/Sub
- 다중 서버 환경 지원
- 수평 확장 가능
- 메시지 브로커 역할

#### 메시지 큐
- RabbitMQ/Kafka 통합
- 안정적인 메시지 전달
- 재시도 메커니즘

#### 프로토콜 버퍼
- 바이너리 프로토콜
- 대역폭 절약
- 빠른 직렬화/역직렬화

#### 백프레셔 처리
- 클라이언트 처리 속도 고려
- 메시지 큐잉
- 드롭 정책

## 다음 단계

Phase 7 완료 후:

**Phase 8: 전략 레지스트리 구현**
- 전략 동적 로딩
- 전략 메타데이터 관리
- 플러그인 아키텍처

## 결론

Phase 7에서 WebSocket 기반 실시간 양방향 통신 시스템을 성공적으로 구현했습니다. 시세 스트리밍, 주문 체결 알림, 전략 모니터링을 통해 실시간 HTS 플랫폼의 핵심 기능을 완성했습니다.
