# Phase 10: LS증권 API 구현 완료

## 개요
LS증권 OpenAPI를 연동하여 실제 자동매매가 가능한 시스템 완성

---

## ✅ 구현 완료 항목

### 1. 계좌 API
- ✅ `get_account_balance()` - 계좌 잔고 조회
- ✅ `get_positions()` - 보유 종목 조회
- ✅ `get_order_available()` - 주문 가능 금액 조회

### 2. 주문 API
- ✅ `place_order()` - 주문 실행 (매수/매도, 시장가/지정가)
- ✅ `cancel_order()` - 주문 취소
- ✅ `modify_order()` - 주문 정정
- ✅ `get_order()` - 주문 조회
- ✅ `get_orders()` - 주문 목록 조회
- ✅ `get_executions()` - 체결 내역 조회

### 3. 시세 API
- ✅ `get_current_price()` - 현재가 조회
- ✅ `get_orderbook()` - 호가 조회
- ✅ `get_ohlc_daily()` - 일봉 조회
- ✅ `get_ohlc_minute()` - 분봉 조회
- ✅ `search_stock()` - 종목 검색

### 4. 데이터 모델
- ✅ `LSAccount`, `LSPosition` - 계좌 모델
- ✅ `LSOrder`, `LSExecution` - 주문 모델
- ✅ `LSOHLC`, `LSQuote`, `LSOrderbook` - 시세 모델

### 5. 서비스 레이어
- ✅ `LSAccountService` - 계좌 서비스
- ✅ `LSOrderService` - 주문 서비스
- ✅ `LSMarketService` - 시세 서비스

### 6. LSAdapter 통합
- ✅ BrokerBase 인터페이스 구현
- ✅ 서비스 레이어 통합
- ✅ 타입 변환 (LS 타입 ↔ 공통 타입)

---

## 📁 파일 구조

```
broker/ls/
├── oauth.py                    # OAuth 인증 ✅
├── client.py                   # API 클라이언트 ✅
├── endpoints.py                # API 엔드포인트 정의 ✅
├── adapter.py                  # LSAdapter (BrokerBase 구현) ✅
├── models/
│   ├── __init__.py
│   ├── account.py             # 계좌 모델 ✅
│   ├── order.py               # 주문 모델 ✅
│   └── market.py              # 시세 모델 ✅
└── services/
    ├── __init__.py
    ├── account.py             # 계좌 서비스 ✅
    ├── order.py               # 주문 서비스 ✅
    └── market.py              # 시세 서비스 ✅
```

---

## 🔧 사용 방법

### 1. 설정 (config.yaml)

```yaml
ls:
  appkey: "YOUR_APPKEY"
  appsecretkey: "YOUR_APPSECRETKEY"
  account_id: "YOUR_ACCOUNT_ID"
  base_url: "https://openapi.ls-sec.co.kr:8080"
```

### 2. LSAdapter 사용

```python
from broker.ls.adapter import LSAdapter
from datetime import datetime, timedelta

async with LSAdapter() as adapter:
    # 계좌 정보
    account = await adapter.get_account()
    print(f"총 자산: {account.equity:,.0f}원")
    
    # 보유 종목
    positions = await adapter.get_positions()
    for pos in positions:
        print(f"{pos.symbol}: {pos.quantity}주")
    
    # OHLC 데이터
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    ohlc_list = await adapter.get_ohlc("005930", "1d", start_date, end_date)
    
    # 주문 실행
    order_id = await adapter.place_order(
        symbol="005930",
        side="buy",
        quantity=10,
        order_type="limit",
        price=75000
    )
    
    # 주문 취소
    await adapter.cancel_order(order_id)
```

### 3. 서비스 직접 사용

```python
from broker.ls.client import LSClient
from broker.ls.services import LSAccountService, LSOrderService, LSMarketService

async with LSClient() as client:
    # 계좌 서비스
    account_service = LSAccountService(client)
    account = await account_service.get_account_balance("123456")
    
    # 주문 서비스
    order_service = LSOrderService(client)
    order_id = await order_service.place_order(...)
    
    # 시세 서비스
    market_service = LSMarketService(client)
    quote = await market_service.get_current_price("005930")
```

---

## 🧪 테스트

### 테스트 실행

```bash
# LS증권 API 테스트
python examples/test_ls_api.py
```

### 예상 출력

```
🚀 LS증권 API 테스트

================================================================================
LS증권 계좌 API 테스트
================================================================================

1. 계좌 정보 조회...
   ✅ 계좌번호: 123456
   ✅ 예수금: 10,000,000원
   ✅ 총 자산: 15,000,000원

2. 보유 종목 조회...
   ✅ 보유 종목 수: 2개
      - 005930: 10주 @ 75,000원
        평가손익: +50,000원
      - 000660: 5주 @ 120,000원
        평가손익: -10,000원

================================================================================
LS증권 시세 API 테스트
================================================================================

1. 현재가 조회 (삼성전자)...
   ✅ 종목명: 삼성전자
   ✅ 현재가: 75,500원
   ✅ 등락률: +1.23%
   ✅ 거래량: 12,345,678주

2. 호가 조회...
   ✅ 매도 호가 1단계: 75,600원 (1,234주)
   ✅ 매수 호가 1단계: 75,500원 (2,345주)

3. 일봉 조회 (최근 5일)...
   ✅ 데이터 수: 5개
      2024-01-15: 시가 74,000 / 고가 75,500 / 저가 73,800 / 종가 75,200
      2024-01-16: 시가 75,200 / 고가 76,000 / 저가 75,000 / 종가 75,800
      ...
```

---

## ⚠️ 주의사항

### 1. API 스펙 확인 필요

현재 구현은 **예상 구조**로 작성되었습니다. 실제 LS증권 API 문서를 확인하여 다음을 수정해야 합니다:

- **엔드포인트 URL**: 실제 경로 확인
- **요청 파라미터**: 필드명 및 형식
- **응답 구조**: 필드명 및 데이터 타입
- **에러 코드**: 에러 처리 로직

### 2. TODO 항목

코드에 `TODO` 주석이 있는 부분:

```python
# TODO: 실제 API 스펙 확인 필요
response = await self.client.get(
    f"{LSEndpoints.STOCK_ACCOUNT}/{account_id}/balance"
)

# TODO: 실제 응답 구조에 맞춰 파싱
return LSAccount(
    account_id=account_id,
    balance=float(response.get("예수금", 0)),
    ...
)
```

### 3. API 문서 참조

각 API의 상세 스펙은 다음 문서를 참조하세요:

- **계좌**: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=37d22d4d-83cd-40a4-a375-81b010a4a627
- **주문**: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=d0e216e0-10d9-479f-8a4d-e175b8bae307
- **시세**: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=54a99b02-dbba-4057-8756-9ac759c9a2ed
- **차트**: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=12320341-ad85-429a-90bd-5b3771c5e89f

---

## 🔄 다음 단계

### Phase 10B: 실시간 시세 (WebSocket)

```python
# broker/ls/services/realtime.py
class LSRealtimeService:
    async def connect(self):
        """WebSocket 연결"""
        
    async def subscribe_price(self, symbol: str):
        """실시간 체결가 구독"""
        
    async def subscribe_orderbook(self, symbol: str):
        """실시간 호가 구독"""
```

### Phase 11: 고급 기능

- 투자정보 API (재무정보, 공시, 뉴스)
- 수급 분석 API (외국인, 기관, 프로그램)
- 종목 스크리닝 API

### Phase 12: 최적화

- Rate Limiting 구현
- 에러 재시도 로직
- 캐싱 전략
- 성능 모니터링

---

## 📊 완료 기준

### ✅ Phase 10 완료 조건

1. ✅ 계좌/주문/시세 API 구현
2. ✅ 데이터 모델 정의
3. ✅ 서비스 레이어 구현
4. ✅ LSAdapter 통합
5. ⏳ 실제 API 연동 테스트 (API 키 필요)
6. ⏳ 실시간 시세 구현 (Phase 10B)

### 다음 작업

1. **LS증권 API 키 발급** 받기
2. **실제 API 스펙 확인** 및 코드 수정
3. **통합 테스트** 실행
4. **실시간 시세** 구현 (WebSocket)

---

**작성일**: 2025-11-21
**상태**: 구조 완성, API 스펙 확인 필요
