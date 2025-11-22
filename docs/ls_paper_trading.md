# LS증권 모의투자 설정 가이드

## 🎯 모의투자 vs 실거래

### URL 차이

| 구분 | 실거래 | 모의투자 |
|------|--------|----------|
| **REST API** | `https://openapi.ls-sec.co.kr:8080` | `https://openapi.ls-sec.co.kr:18080` |
| **WebSocket** | `wss://openapi.ls-sec.co.kr:9443` | `wss://openapi.ls-sec.co.kr:29443` |
| **포트** | 8080, 9443 | 18080, 29443 |

---

## ⚙️ 설정 방법

### 1. config.yaml 설정

```yaml
ls:
  appkey: "YOUR_APPKEY"              # 모의투자 앱 키
  appsecretkey: "YOUR_APPSECRETKEY"  # 모의투자 앱 시크릿 키
  account_id: "YOUR_ACCOUNT_ID"      # 모의투자 계좌번호
  paper_trading: true                # ⭐ 모의투자 활성화
```

**중요:**
- `paper_trading: true` → 모의투자 (포트 18080, 29443)
- `paper_trading: false` → 실거래 (포트 8080, 9443)

### 2. 코드에서 직접 설정

```python
from broker.ls.adapter import LSAdapter

# 모의투자
adapter = LSAdapter(
    api_key="YOUR_APPKEY",
    api_secret="YOUR_APPSECRETKEY",
    account_id="YOUR_ACCOUNT_ID",
    paper_trading=True  # ⭐ 모의투자
)

# 실거래
adapter = LSAdapter(
    api_key="YOUR_APPKEY",
    api_secret="YOUR_APPSECRETKEY",
    account_id="YOUR_ACCOUNT_ID",
    paper_trading=False  # 실거래
)
```

---

## 🔐 인증 정보

### 모의투자 계정 발급

1. LS증권 홈페이지 접속
2. 모의투자 신청
3. 모의투자 앱 키/시크릿 발급
4. 모의투자 계좌번호 확인

### 주의사항

- **모의투자 키 ≠ 실거래 키**: 별도 발급 필요
- **모의투자 계좌 ≠ 실거래 계좌**: 다른 계좌번호
- **모의투자 비밀번호**: 실거래와 다를 수 있음

---

## 🧪 테스트

### 모의투자 테스트

```python
import asyncio
from broker.ls.adapter import LSAdapter

async def test_paper_trading():
    # config.yaml에서 자동으로 paper_trading 설정 로드
    async with LSAdapter() as adapter:
        # 계좌 정보
        account = await adapter.get_account()
        print(f"모의투자 계좌: {account.account_id}")
        print(f"모의 자산: {account.equity:,.0f}원")
        
        # 주문 실행 (모의투자이므로 안전)
        order_id = await adapter.place_order(
            symbol="005930",
            side="buy",
            quantity=10,
            order_type="limit",
            price=70000
        )
        print(f"모의 주문번호: {order_id}")

asyncio.run(test_paper_trading())
```

---

## 🔄 실거래 전환

### 1. config.yaml 수정

```yaml
ls:
  appkey: "REAL_APPKEY"              # 실거래 앱 키로 변경
  appsecretkey: "REAL_APPSECRETKEY"  # 실거래 앱 시크릿 키로 변경
  account_id: "REAL_ACCOUNT_ID"      # 실거래 계좌번호로 변경
  paper_trading: false               # ⭐ 실거래로 변경
```

### 2. 코드 변경 없음

```python
# 동일한 코드로 실거래 가능
async with LSAdapter() as adapter:
    # config.yaml의 paper_trading 설정에 따라 자동 전환
    account = await adapter.get_account()
```

---

## ⚠️ 안전 장치

### 환경 변수로 관리 (권장)

```bash
# .env 파일
LS_APPKEY=YOUR_APPKEY
LS_APPSECRETKEY=YOUR_APPSECRETKEY
LS_ACCOUNT_ID=YOUR_ACCOUNT_ID
LS_PAPER_TRADING=true  # 모의투자
```

```yaml
# config.yaml
ls:
  appkey: ${LS_APPKEY}
  appsecretkey: ${LS_APPSECRETKEY}
  account_id: ${LS_ACCOUNT_ID}
  paper_trading: ${LS_PAPER_TRADING}
```

### 실수 방지

```python
# 실거래 전에 확인
if not adapter.paper_trading:
    confirm = input("⚠️  실거래 모드입니다. 계속하시겠습니까? (yes/no): ")
    if confirm.lower() != "yes":
        print("취소되었습니다.")
        return
```

---

## 📊 모의투자 특징

### 장점
- ✅ 실제 돈 없이 테스트 가능
- ✅ 전략 검증 안전
- ✅ 무제한 테스트
- ✅ 실거래와 동일한 API

### 제한사항
- ❌ 실제 체결 속도와 다를 수 있음
- ❌ 슬리피지 시뮬레이션 부정확
- ❌ 일부 기능 제한 가능

---

## 🎓 권장 워크플로우

### 1단계: 모의투자 개발
```yaml
paper_trading: true
```
- 전략 개발
- 버그 수정
- 성능 테스트

### 2단계: 모의투자 검증
```yaml
paper_trading: true
```
- 장기간 운영 (1개월+)
- 수익률 검증
- 안정성 확인

### 3단계: 실거래 전환
```yaml
paper_trading: false
```
- 소액으로 시작
- 점진적 확대
- 지속적 모니터링

---

## 🔍 디버깅

### URL 확인

```python
from broker.ls.client import LSClient

client = LSClient(paper_trading=True)
print(f"Base URL: {client.base_url}")
# 출력: https://openapi.ls-sec.co.kr:18080 (모의투자)

client = LSClient(paper_trading=False)
print(f"Base URL: {client.base_url}")
# 출력: https://openapi.ls-sec.co.kr:8080 (실거래)
```

### 로그 확인

```python
# 로그에서 모의투자 여부 확인
# LSAdapter initialized for account: 123456 (모의투자)
# LSAdapter initialized for account: 123456 (실거래)
```

---

**작성일**: 2025-11-21
**중요**: 항상 모의투자로 충분히 테스트한 후 실거래로 전환하세요!
