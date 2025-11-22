# Phase 10: LS증권 API 구현 계획

## 목표
LS증권 OpenAPI를 연동하여 실제 자동매매가 가능한 시스템 완성

---

## 📋 구현 범위

### 1단계: 계좌 API (Account)
**목표**: 계좌 정보 조회 및 관리

#### 구현 항목
- [ ] `get_account_balance()` - 계좌 잔고 조회
  - 예수금, 총 자산, 평가 금액
- [ ] `get_positions()` - 보유 종목 조회
  - 종목별 수량, 평균 단가, 평가 손익
- [ ] `get_order_available()` - 주문 가능 금액 조회
  - 매수 가능 금액 계산

#### 파일 구조
```
broker/ls/
├── services/
│   └── account.py          # LSAccountService
└── models/
    └── account.py          # Account 모델
```

#### 예상 소요 시간: 2-3시간

---

### 2단계: 주문 API (Order)
**목표**: 주식 매매 주문 실행

#### 구현 항목
- [ ] `place_order()` - 주문 실행
  - 매수/매도, 시장가/지정가
  - 주문 번호 반환
- [ ] `cancel_order()` - 주문 취소
  - 미체결 주문 취소
- [ ] `modify_order()` - 주문 정정
  - 가격/수량 변경
- [ ] `get_orders()` - 주문 조회
  - 당일 주문 내역
- [ ] `get_executions()` - 체결 조회
  - 체결 내역 확인

#### 파일 구조
```
broker/ls/
├── services/
│   └── order.py            # LSOrderService
└── models/
    └── order.py            # Order 모델
```

#### 예상 소요 시간: 3-4시간

---

### 3단계: 시세 API (Market Data)
**목표**: 과거 및 현재 시세 데이터 조회

#### 구현 항목
- [ ] `get_current_price()` - 현재가 조회
  - 실시간 가격, 등락률
- [ ] `get_orderbook()` - 호가 조회
  - 매수/매도 호가 10단계
- [ ] `get_ohlc_daily()` - 일봉 조회
  - 백테스트용 과거 데이터
- [ ] `get_ohlc_minute()` - 분봉 조회
  - 1분/5분/10분/30분/60분
- [ ] `search_stock()` - 종목 검색
  - 종목명/코드로 검색

#### 파일 구조
```
broker/ls/
├── services/
│   └── market.py           # LSMarketService
└── models/
    └── market.py           # OHLC, Quote 모델
```

#### 예상 소요 시간: 3-4시간

---

### 4단계: 실시간 시세 (WebSocket)
**목표**: 실시간 데이터 스트리밍

#### 구현 항목
- [ ] WebSocket 연결 관리
  - 연결/재연결/종료
- [ ] `subscribe_price()` - 실시간 체결가
  - 가격 변동 스트리밍
- [ ] `subscribe_orderbook()` - 실시간 호가
  - 호가 변동 스트리밍
- [ ] `subscribe_execution()` - 실시간 체결
  - 주문 체결 알림
- [ ] 메시지 파싱 및 이벤트 처리

#### 파일 구조
```
broker/ls/
├── services/
│   └── realtime.py         # LSRealtimeService
└── websocket/
    ├── connection.py       # WebSocket 연결
    ├── parser.py           # 메시지 파싱
    └── handler.py          # 이벤트 핸들러
```

#### 예상 소요 시간: 4-5시간

---

## 🏗️ 구현 아키텍처

### 계층 구조
```
LSAdapter (BrokerBase 구현)
    ↓
LSClient (OAuth 인증)
    ↓
Services (비즈니스 로직)
    ├── LSAccountService
    ├── LSOrderService
    ├── LSMarketService
    └── LSRealtimeService
    ↓
Models (데이터 모델)
    ├── Account, Position
    ├── Order, Execution
    └── OHLC, Quote
```

### 데이터 흐름
```
1. 전략 → OrderSignal 생성
2. ExecutionEngine → LSAdapter.place_order()
3. LSAdapter → LSOrderService.place_order()
4. LSOrderService → LSClient.post("/order")
5. LSClient → OAuth 인증 → LS API 호출
6. 응답 → Order 모델 → ExecutionEngine
```

---

## 📝 구현 상세

### 1. LSAccountService

```python
class LSAccountService:
    """계좌 관련 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def get_account_balance(self, account_id: str) -> Account:
        """
        계좌 잔고 조회
        
        Args:
            account_id: 계좌번호
            
        Returns:
            Account 객체
        """
        response = await self.client.get(
            f"/stock/accno/{account_id}/balance"
        )
        
        return Account(
            account_id=account_id,
            balance=response["예수금"],
            equity=response["총평가금액"],
            # ...
        )
    
    async def get_positions(self, account_id: str) -> List[Position]:
        """보유 종목 조회"""
        response = await self.client.get(
            f"/stock/accno/{account_id}/positions"
        )
        
        return [
            Position(
                symbol=item["종목코드"],
                quantity=item["보유수량"],
                avg_price=item["평균단가"],
                # ...
            )
            for item in response["보유종목"]
        ]
```

### 2. LSOrderService

```python
class LSOrderService:
    """주문 관련 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def place_order(
        self,
        account_id: str,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        price: float = None
    ) -> str:
        """
        주문 실행
        
        Returns:
            주문번호
        """
        response = await self.client.post(
            "/stock/order",
            data={
                "계좌번호": account_id,
                "종목코드": symbol,
                "주문구분": "매수" if side == OrderSide.BUY else "매도",
                "주문수량": quantity,
                "주문가격": price,
                "주문유형": "시장가" if order_type == OrderType.MARKET else "지정가"
            }
        )
        
        return response["주문번호"]
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        response = await self.client.delete(f"/stock/order/{order_id}")
        return response["결과"] == "성공"
```

### 3. LSMarketService

```python
class LSMarketService:
    """시세 관련 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def get_current_price(self, symbol: str) -> Quote:
        """현재가 조회"""
        response = await self.client.get(
            f"/stock/market/{symbol}/current"
        )
        
        return Quote(
            symbol=symbol,
            price=response["현재가"],
            change=response["전일대비"],
            change_percent=response["등락률"],
            volume=response["거래량"],
            # ...
        )
    
    async def get_ohlc_daily(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """일봉 조회"""
        response = await self.client.get(
            f"/stock/chart/{symbol}/daily",
            params={
                "시작일": start_date.strftime("%Y%m%d"),
                "종료일": end_date.strftime("%Y%m%d")
            }
        )
        
        return [
            OHLC(
                timestamp=datetime.strptime(item["일자"], "%Y%m%d"),
                open=item["시가"],
                high=item["고가"],
                low=item["저가"],
                close=item["종가"],
                volume=item["거래량"]
            )
            for item in response["차트데이터"]
        ]
```

### 4. LSRealtimeService

```python
class LSRealtimeService:
    """실시간 시세 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self):
        """WebSocket 연결"""
        token = await self.client._get_valid_token()
        
        self.ws = await websockets.connect(
            "wss://openapi.ls-sec.co.kr:9443/websocket",
            extra_headers={"Authorization": f"Bearer {token}"}
        )
    
    async def subscribe_price(self, symbol: str, callback):
        """실시간 체결가 구독"""
        await self.ws.send(json.dumps({
            "header": {
                "tr_type": "1",  # 실시간 등록
                "tr_cd": "S3_"   # 체결가
            },
            "body": {
                "종목코드": symbol
            }
        }))
        
        # 콜백 등록
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(callback)
    
    async def _message_loop(self):
        """메시지 수신 루프"""
        async for message in self.ws:
            data = json.loads(message)
            
            # 메시지 파싱 및 콜백 호출
            symbol = data["body"]["종목코드"]
            if symbol in self.subscriptions:
                for callback in self.subscriptions[symbol]:
                    await callback(data)
```

---

## 🧪 테스트 계획

### 단위 테스트
```python
# tests/test_ls_account.py
async def test_get_account_balance():
    service = LSAccountService(mock_client)
    account = await service.get_account_balance("123456")
    assert account.balance > 0

# tests/test_ls_order.py
async def test_place_order():
    service = LSOrderService(mock_client)
    order_id = await service.place_order(...)
    assert order_id is not None

# tests/test_ls_market.py
async def test_get_current_price():
    service = LSMarketService(mock_client)
    quote = await service.get_current_price("005930")
    assert quote.price > 0
```

### 통합 테스트
```python
# examples/test_ls_integration.py
async def test_full_trading_flow():
    # 1. 계좌 조회
    account = await adapter.get_account()
    
    # 2. 현재가 조회
    price = await adapter.get_current_price("005930")
    
    # 3. 주문 실행
    order_id = await adapter.place_order(...)
    
    # 4. 주문 확인
    order = await adapter.get_order(order_id)
    
    # 5. 체결 확인
    assert order.status == "체결"
```

---

## 📊 진행 상황 추적

### 체크리스트

#### 1단계: 계좌 API
- [ ] LSAccountService 구현
- [ ] Account/Position 모델 정의
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 문서 작성

#### 2단계: 주문 API
- [ ] LSOrderService 구현
- [ ] Order/Execution 모델 정의
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 문서 작성

#### 3단계: 시세 API
- [ ] LSMarketService 구현
- [ ] OHLC/Quote 모델 정의
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 문서 작성

#### 4단계: 실시간 시세
- [ ] LSRealtimeService 구현
- [ ] WebSocket 연결 관리
- [ ] 메시지 파싱
- [ ] 이벤트 핸들러
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 문서 작성

---

## ⚠️ 주의사항

### 1. API 호출 제한
- Rate Limiting 준수
- 초당 요청 횟수 제한
- 재시도 로직 구현

### 2. 에러 처리
- API 에러 코드별 처리
- 네트워크 오류 재시도
- 타임아웃 설정

### 3. 데이터 검증
- 응답 데이터 유효성 검사
- 필수 필드 확인
- 타입 변환 안전성

### 4. 로깅
- 모든 API 호출 로깅
- 에러 상세 로깅
- 성능 모니터링

---

## 📅 일정

### Week 1: 계좌 + 주문 API
- Day 1-2: LSAccountService 구현
- Day 3-4: LSOrderService 구현
- Day 5: 테스트 및 디버깅

### Week 2: 시세 + 실시간
- Day 1-2: LSMarketService 구현
- Day 3-4: LSRealtimeService 구현
- Day 5: 통합 테스트

### Week 3: 통합 및 최적화
- Day 1-2: LSAdapter 통합
- Day 3-4: 전체 시스템 테스트
- Day 5: 문서화 및 배포 준비

---

## 🎯 완료 기준

### Phase 10 완료 조건
1. ✅ 4개 서비스 모두 구현 완료
2. ✅ 모든 단위 테스트 통과
3. ✅ 통합 테스트 통과
4. ✅ 실제 LS증권 API 연동 성공
5. ✅ 문서 작성 완료

### 성공 지표
- API 호출 성공률 > 99%
- 평균 응답 시간 < 1초
- 주문 체결 성공률 > 95%
- 실시간 시세 지연 < 100ms

---

## 다음 단계

Phase 10 완료 후:
- **Phase 11**: 고급 기능 (투자정보, 수급 분석)
- **Phase 12**: 확장 기능 (ETF, 섹터, 스크리닝)
- **Phase 13**: 프론트엔드 대시보드
- **Phase 14**: 배포 및 운영

---

**작성일**: 2025-11-21
**예상 완료**: 2025-12-12 (3주)
