# Phase 9: LS증권 OAuth 인증 구현 완료

## 개요
LS증권 OpenAPI OAuth 2.0 인증 시스템을 구현하여 실제 증권사 API 연동 기반을 마련했습니다.

## 구현 내용

### 1. OAuth 계층 구조
```
broker/ls/
├── oauth.py               # OAuth 2.0 인증 (LSOAuth, LSTokenManager)
├── client.py              # API 클라이언트 (LSClient)
├── adapter.py             # 브로커 어댑터 (LSAdapter)
└── ...                    # 기타 서비스 (OHLC, Order, Account 등)
```

### 2. 주요 컴포넌트

#### LSOAuth
- **토큰 발급**: `get_access_token()`
- **토큰 갱신**: `refresh_access_token()`
- **토큰 폐기**: `revoke_token()`
- **자동 갱신**: `ensure_valid_token()`
- **유효성 검사**: `is_token_valid()`

#### LSTokenManager
- **파일 기반 영속성**: 토큰을 파일에 저장/로드
- **자동 갱신**: 만료된 토큰 자동 갱신
- **초기화**: `initialize()` - 저장된 토큰 로드 또는 새로 발급

#### LSClient
- **자동 인증**: 모든 API 요청에 자동으로 토큰 포함
- **토큰 관리**: 토큰 만료 시 자동 갱신
- **HTTP 메서드**: `get()`, `post()`, `put()`, `delete()`
- **컨텍스트 매니저**: `async with LSClient()` 지원

### 3. OAuth 2.0 플로우

#### 토큰 발급
```python
from broker.ls.oauth import LSOAuth

oauth = LSOAuth(
    appkey="YOUR_APPKEY",
    appsecretkey="YOUR_APPSECRETKEY"
)

# 토큰 발급
token_info = await oauth.get_access_token()
# {
#   "access_token": "...",
#   "token_type": "Bearer",
#   "expires_in": 86400,
#   "expires_at": "2024-01-02T00:00:00",
#   "scope": "oob"
# }
```

#### 토큰 갱신
```python
# 리프레시 토큰으로 갱신
new_token_info = await oauth.refresh_access_token()
```

#### 토큰 폐기
```python
# 토큰 무효화
await oauth.revoke_token()
```

#### 자동 갱신
```python
# 유효한 토큰 보장 (만료 시 자동 갱신)
valid_token = await oauth.ensure_valid_token()
```

### 4. 토큰 매니저 사용

#### 파일 기반 영속성
```python
from broker.ls.oauth import LSTokenManager

# 토큰 매니저 초기화
manager = LSTokenManager(token_file="data/ls_token.json")
oauth = await manager.initialize(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET"
)

# 유효한 토큰 획득 (자동 갱신 + 파일 저장)
token = await manager.get_valid_token()
```

#### 토큰 파일 구조
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_at": "2024-01-02T00:00:00"
}
```

### 5. LSClient 사용

#### 기본 사용
```python
from broker.ls.client import LSClient

# 클라이언트 생성
client = LSClient(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_id="YOUR_ACCOUNT_ID"
)

# 연결
await client.connect()

# API 요청 (자동 인증)
response = await client.get("/v1/account/balance")

# 종료
await client.close()
```

#### 컨텍스트 매니저 사용 (권장)
```python
async with LSClient() as client:
    # 자동 연결 및 인증
    response = await client.get("/v1/account/balance")
    # 자동 종료
```

#### 토큰 매니저와 함께 사용
```python
# 토큰 파일 기반 영속성 사용
client = LSClient(use_token_manager=True)
await client.connect()

# 토큰이 파일에 저장되어 재시작 시에도 유지됨
```

### 6. 설정 파일

#### config.yaml (LS증권 공식 용어 사용)
```yaml
# LS증권 OAuth 설정
ls:
  appkey: "YOUR_APPKEY"
  appsecretkey: "YOUR_APPSECRETKEY"
  account_id: "YOUR_ACCOUNT_ID"
  base_url: "https://openapi.ls-sec.co.kr:8080"
```

#### 환경변수 사용
```yaml
ls:
  appkey: ${LS_APPKEY}
  appsecretkey: ${LS_APPSECRETKEY}
  account_id: ${LS_ACCOUNT_ID}
```

**참고**: LS증권 OpenAPI는 `appkey`와 `appsecretkey` 용어를 사용합니다 (ProgramGarden 호환)

### 7. 테스트 실행

```bash
# OAuth 테스트
python examples/test_ls_oauth.py
```

### 8. 예상 출력

```
🔐 LS증권 OAuth 인증 테스트

⚠️  주의: config.yaml에 LS증권 API 키 설정이 필요합니다

================================================================================
LS증권 OAuth 기본 테스트
================================================================================

1. OAuth 인스턴스 생성...
   ✅ OAuth 인스턴스 생성 완료

2. 접근 토큰 발급...
   ✅ 접근 토큰: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
   ✅ 토큰 타입: Bearer
   ✅ 만료 시간: 86400초
   ✅ 만료 일시: 2024-01-02T00:00:00

3. 토큰 유효성 확인...
   ✅ 토큰 유효: True

4. 인증 헤더 생성...
   ✅ Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...

5. 토큰 갱신 테스트...
   ✅ 새 접근 토큰: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...

6. 토큰 폐기...
   ✅ 토큰 폐기: True

✅ OAuth 테스트 완료
```

### 9. 보안 고려사항

#### 토큰 저장
- **파일 권한**: 토큰 파일은 읽기 전용으로 설정
- **암호화**: 민감한 정보는 암호화하여 저장
- **환경변수**: API 키는 환경변수로 관리

#### 토큰 갱신
- **자동 갱신**: 만료 5분 전 자동 갱신
- **재시도**: 갱신 실패 시 새 토큰 발급
- **에러 처리**: 인증 실패 시 적절한 에러 처리

#### API 요청
- **HTTPS**: 모든 API 요청은 HTTPS 사용
- **타임아웃**: 적절한 타임아웃 설정 (30초)
- **재시도**: 네트워크 오류 시 재시도 로직

### 10. LSAdapter 통합

#### 기존 LSAdapter 업데이트
```python
from broker.ls.client import LSClient

class LSAdapter(BrokerBase):
    def __init__(self, app_key=None, app_secret=None, account_id=None):
        # LSClient 사용
        self.client = LSClient(
            app_key=app_key,
            app_secret=app_secret,
            account_id=account_id
        )
    
    async def get_account(self) -> Account:
        # 자동 인증된 API 요청
        response = await self.client.get("/v1/account/balance")
        return Account(...)
```

### 11. 다음 단계

#### API 엔드포인트 구현
- **계좌 조회**: `/v1/account/balance`, `/v1/account/positions`
- **주문 실행**: `/v1/order/place`, `/v1/order/cancel`
- **시세 조회**: `/v1/market/ohlc`, `/v1/market/current`
- **실시간 시세**: WebSocket 연결

#### 서비스 구현
- `LSOHLCService` - 시세 데이터 조회
- `LSOrderService` - 주문 실행/취소/조회
- `LSAccountService` - 계좌 정보 조회
- `LSRealtimeService` - 실시간 시세 스트리밍

#### 에러 처리
- API 에러 코드별 처리
- 재시도 로직
- 로깅 및 모니터링

### 12. 향후 개선 사항

#### 다중 계좌 지원
```python
# 여러 계좌 동시 관리
clients = {
    "account1": LSClient(account_id="123456"),
    "account2": LSClient(account_id="789012")
}
```

#### 토큰 암호화
```python
# 토큰 파일 암호화
from cryptography.fernet import Fernet

class EncryptedTokenManager(LSTokenManager):
    def __init__(self, encryption_key):
        self.cipher = Fernet(encryption_key)
        super().__init__()
```

#### Rate Limiting
```python
# API 호출 빈도 제한
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=1)  # 초당 10회
async def api_call():
    pass
```

## 결론

Phase 9에서 LS증권 OAuth 2.0 인증 시스템을 성공적으로 구현했습니다. 토큰 발급/갱신/폐기, 파일 기반 영속성, 자동 인증 등의 기능을 통해 실제 LS증권 API 연동을 위한 견고한 기반을 마련했습니다.

**다음 단계**: 실제 LS증권 API 엔드포인트 구현 및 서비스 레이어 완성
