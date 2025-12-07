# 트레이딩 화면 계좌번호 데이터 흐름

## 📊 데이터 흐름 다이어그램

```
사용자 → AccountSelector → accountStore → AccountInfo → API → DB → Broker
         (계좌 선택)      (상태 저장)    (표시)      (조회)  (복호화) (실시간)
```

---

## 🔍 상세 흐름

### 1. 계좌 선택 (AccountSelector)
**위치**: `frontend/src/components/AccountSelector.tsx`

```typescript
// 사용자가 드롭다운에서 계좌 선택
<select onChange={(e) => setSelectedAccountId(Number(e.target.value))}>
  <option value={account.id}>{account.alias}</option>
</select>
```

**동작**:
- 사용자가 계좌 선택
- `accountStore.setSelectedAccountId(accountId)` 호출
- 전역 상태에 선택된 계좌 ID 저장

---

### 2. 상태 관리 (accountStore)
**위치**: `frontend/src/app/store/accountStore.ts`

```typescript
interface AccountStore {
  selectedAccountId: number | null;  // 선택된 계좌 ID
  accountBalance: AccountBalance | null;  // 계좌 잔고 정보
  // ...
}
```

**저장되는 데이터**:
- `selectedAccountId`: 선택된 계좌의 DB ID (예: 1, 2, 3...)
- `accountBalance`: API에서 받아온 계좌 정보

---

### 3. 계좌 정보 표시 (AccountInfo)
**위치**: `frontend/src/modules/account/components/AccountInfo.tsx`

```typescript
export const AccountInfo = () => {
  const { selectedAccountId, accountBalance } = useAccountStore();
  
  useEffect(() => {
    if (!selectedAccountId) return;
    
    // API 호출: /api/accounts/{selectedAccountId}/balance
    const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
    setAccountBalance(response.data);
  }, [selectedAccountId]);
  
  return (
    <div className="account-item">
      <label>계좌번호</label>
      <div className="value">{accountBalance.account_number}</div>
    </div>
  );
};
```

**동작**:
1. `selectedAccountId`가 변경되면 API 호출
2. `/api/accounts/{account_id}/balance` 엔드포인트 호출
3. 응답 데이터를 `accountBalance`에 저장
4. `accountBalance.account_number` 표시

---

### 4. API 엔드포인트 (Backend)
**위치**: `api/routes/accounts.py`

```python
@router.get("/{account_id}/balance", response_model=dict)
async def get_account_balance(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """실시간 계좌 잔고 조회"""
    
    # 1. DB에서 계좌 정보 조회
    account = repo.get_account(account_id, current_user["user_id"])
    
    # 2. 암호화된 인증 정보 복호화
    credentials = repo.get_account_credentials(account_id, current_user["user_id"])
    # credentials = {
    #     "account_number": "555044505-01",  # 복호화된 계좌번호
    #     "api_key": "...",
    #     "api_secret": "...",
    #     "account_password": "..."
    # }
    
    # 3. 브로커 Adapter로 실시간 정보 조회
    adapter = await connection_pool.get_adapter(
        broker="ls",
        account_id=credentials["account_number"],
        api_key=credentials["api_key"],
        api_secret=credentials["api_secret"]
    )
    
    balance = await adapter.get_account()
    positions = await adapter.get_positions()
    
    # 4. 응답 반환
    return {
        "account_id": account.id,
        "account_number": credentials["account_number"],  # ← 여기서 계좌번호 반환
        "broker": account.broker,
        "balance": balance.balance,
        "equity": balance.equity,
        "buying_power": balance.buying_power(),
        "positions": [...]
    }
```

**핵심 포인트**:
- `credentials["account_number"]`가 실제 계좌번호
- DB에 암호화되어 저장됨
- `get_account_credentials()`에서 복호화
- API 응답에 포함되어 프론트엔드로 전달

---

## 🔐 계좌번호 저장 및 보안

### 데이터베이스 저장
**테이블**: `trading_accounts`

```sql
CREATE TABLE trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    broker VARCHAR(50) NOT NULL,
    account_number_encrypted TEXT NOT NULL,  -- 암호화된 계좌번호
    account_password_encrypted TEXT,         -- 암호화된 비밀번호
    api_key_encrypted TEXT,                  -- 암호화된 API 키
    api_secret_encrypted TEXT,               -- 암호화된 API 시크릿
    alias VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 암호화/복호화
**위치**: `api/repositories/account_repository.py`

```python
class AccountRepository:
    def create_account(self, user_id: int, account_data: TradingAccountCreate):
        """계좌 생성 (암호화)"""
        account = TradingAccount(
            user_id=user_id,
            broker=account_data.broker,
            account_number_encrypted=self._encrypt(account_data.account_number),
            account_password_encrypted=self._encrypt(account_data.account_password),
            api_key_encrypted=self._encrypt(account_data.api_key),
            api_secret_encrypted=self._encrypt(account_data.api_secret),
            alias=account_data.alias
        )
        db.add(account)
        db.commit()
        return account
    
    def get_account_credentials(self, account_id: int, user_id: int):
        """인증 정보 조회 (복호화)"""
        account = self.get_account(account_id, user_id)
        if not account:
            return None
        
        return {
            "account_number": self._decrypt(account.account_number_encrypted),
            "account_password": self._decrypt(account.account_password_encrypted),
            "api_key": self._decrypt(account.api_key_encrypted),
            "api_secret": self._decrypt(account.api_secret_encrypted)
        }
    
    def _encrypt(self, value: str) -> str:
        """AES 암호화"""
        # Fernet 사용
        return cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        """AES 복호화"""
        return cipher.decrypt(encrypted_value.encode()).decode()
```

---

## 📋 전체 데이터 흐름 요약

### 계좌 등록 시
```
사용자 입력 → 프론트엔드 → API → 암호화 → DB 저장
"555044505-01"              encrypt()   "gAAAAABh..."
```

### 계좌 정보 조회 시
```
프론트엔드 → API → DB 조회 → 복호화 → Broker API → 실시간 정보
            /api/accounts/1/balance
                    ↓
            get_account_credentials()
                    ↓
            decrypt("gAAAAABh...") → "555044505-01"
                    ↓
            LS증권 API 호출
                    ↓
            실시간 잔고/포지션
                    ↓
            {
              "account_number": "555044505-01",
              "balance": 10000000,
              "equity": 10500000,
              ...
            }
                    ↓
            프론트엔드 표시
```

---

## 🔑 핵심 포인트

### 1. 계좌번호는 어디서 오는가?
**답**: API 응답의 `account_number` 필드

```typescript
// 프론트엔드
const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
// response.data = {
//   account_number: "555044505-01",  ← 여기!
//   balance: 10000000,
//   ...
// }

accountBalance.account_number  // "555044505-01"
```

### 2. 계좌번호는 어떻게 저장되는가?
**답**: DB에 AES 암호화되어 저장

```python
# 저장 시
account_number_encrypted = encrypt("555044505-01")
# → "gAAAAABh3xK9..."

# 조회 시
account_number = decrypt("gAAAAABh3xK9...")
# → "555044505-01"
```

### 3. 왜 암호화하는가?
**이유**:
- 민감한 금융 정보 보호
- DB 유출 시에도 안전
- 규제 준수 (개인정보보호법)

### 4. 실시간 정보는 어떻게 가져오는가?
**답**: 브로커 Adapter를 통해 실시간 API 호출

```python
# Connection Pool에서 Adapter 가져오기
adapter = await connection_pool.get_adapter(
    broker="ls",
    account_id="555044505-01",
    api_key="...",
    api_secret="..."
)

# 실시간 정보 조회
balance = await adapter.get_account()  # LS증권 API 호출
positions = await adapter.get_positions()  # LS증권 API 호출
```

---

## 🔄 자동 갱신 메커니즘

### 프론트엔드 (30초마다)
```typescript
useEffect(() => {
  const loadBalance = async () => {
    const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
    setAccountBalance(response.data);
  };
  
  loadBalance();  // 즉시 실행
  
  const interval = setInterval(loadBalance, 30000);  // 30초마다
  return () => clearInterval(interval);
}, [selectedAccountId]);
```

### 백엔드 (Connection Pool)
```python
# 연결 재사용으로 성능 최적화
# - 5분 동안 사용 안하면 자동 종료
# - 2분마다 유휴 연결 정리
# - 같은 계좌는 연결 재사용
```

---

## 🛡️ 보안 고려사항

### 1. 전송 보안
- HTTPS 사용 (프로덕션)
- JWT 토큰 인증
- CORS 설정

### 2. 저장 보안
- AES 암호화
- 환경 변수로 암호화 키 관리
- DB 접근 제어

### 3. 표시 보안
- 마스킹 옵션 (선택)
- 로그에 민감 정보 제외
- 에러 메시지에 계좌번호 미포함

---

## 📊 API 응답 예시

### 요청
```http
GET /api/accounts/1/balance
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 응답
```json
{
  "account_id": 1,
  "account_number": "555044505-01",
  "broker": "ls",
  "balance": 10000000.0,
  "equity": 10500000.0,
  "margin_used": 0.0,
  "margin_available": 10000000.0,
  "buying_power": 10000000.0,
  "positions": [
    {
      "symbol": "005930",
      "quantity": 10,
      "avg_price": 70000.0,
      "current_price": 75000.0,
      "unrealized_pnl": 50000.0,
      "realized_pnl": 0.0
    }
  ]
}
```

---

## 🔧 문제 해결

### 계좌번호가 표시되지 않는 경우

#### 1. 계좌가 선택되지 않음
```typescript
if (!selectedAccountId) {
  return <div>계좌를 선택해주세요</div>;
}
```

#### 2. API 호출 실패
```typescript
try {
  const response = await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
} catch (error) {
  console.error('계좌 정보 조회 실패:', error);
  setError('계좌 정보를 불러올 수 없습니다');
}
```

#### 3. 인증 정보 없음
```python
credentials = repo.get_account_credentials(account_id, user_id)
if not credentials:
    raise HTTPException(404, "계좌 인증 정보를 찾을 수 없습니다")
```

#### 4. 브로커 연결 실패
```python
try:
    adapter = await connection_pool.get_adapter(...)
    balance = await adapter.get_account()
except Exception as e:
    raise HTTPException(500, f"계좌 정보 조회 실패: {str(e)}")
```

---

## 💡 개선 아이디어

### 1. 계좌번호 마스킹
```typescript
const maskAccountNumber = (accountNumber: string) => {
  // "555044505-01" → "5550****5-01"
  return accountNumber.replace(/(\d{4})\d{4}(\d{2}-\d{2})/, '$1****$2');
};
```

### 2. 캐싱
```typescript
// 30초 동안 캐시 사용
const cachedBalance = useMemo(() => accountBalance, [accountBalance]);
```

### 3. 에러 재시도
```typescript
const loadBalance = async (retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await httpClient.get(`/api/accounts/${selectedAccountId}/balance`);
    } catch (error) {
      if (i === retries - 1) throw error;
      await sleep(1000 * (i + 1));  // 지수 백오프
    }
  }
};
```

---

**작성일**: 2025-11-30
**버전**: 1.0
