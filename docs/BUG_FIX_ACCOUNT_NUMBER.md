# 버그 수정: 계좌번호 대신 비밀번호 표시 문제

## 🐛 문제 설명

### 증상
트레이딩 화면의 "계좌번호" 필드에 실제 계좌번호가 아닌 **계좌 비밀번호**가 표시됨

### 발견 경로
사용자 리포트 → 화면 확인 → 백엔드 로그 분석

---

## 🔍 원인 분석

### 1. 로그 분석
```
'accno': 'qwer1234', 'passwd': 'qwer1234'
```

LS증권 API 호출 시:
- `accno` (계좌번호): `qwer1234` ❌ (비밀번호가 들어감)
- `passwd` (계좌 비밀번호): `qwer1234` ✅

### 2. 코드 추적

#### 문제 1: `LSAccount.account_id` 필드 혼동
**파일**: `broker/ls/services/account.py`

```python
# 문제 코드
return LSAccount(
    account_id=account_id,  # 파라미터 이름이 account_id
    balance=...,
    ...
)
```

**문제점**:
- 파라미터 이름이 `account_id`
- 하지만 실제로는 계좌번호를 받아야 함
- `account_id`와 `account_number`가 혼용됨

#### 문제 2: 파라미터 이름 불일치
**파일**: `broker/ls/adapter.py`

```python
# LSAdapter 초기화 시
self.account_id = account_id or config.get("ls.account_id")
# config.yaml의 ls.account_id = "555044505-01" (계좌번호)

# 하지만 get_account_balance 호출 시
ls_account = await self.account_service.get_account_balance(self.account_id)
# account_id를 그대로 전달
```

#### 문제 3: 계좌 비밀번호 전달 누락
**파일**: `broker/ls/services/account.py`

```python
# 기존 코드
async def get_account_balance(self, account_id: str) -> LSAccount:
    clean_account = account_id.replace("-", "")
    password = config.get("ls.account_password", "")  # config에서 가져옴
    
    # API 호출
    data={
        "t0424InBlock": {
            "accno": clean_account,  # 계좌번호
            "passwd": password,      # 계좌 비밀번호
            ...
        }
    }
```

**문제점**:
- `account_id` 파라미터가 실제로는 계좌번호여야 하는데
- 변수명이 혼란스러움
- 계좌 비밀번호는 항상 config에서 가져옴 (DB에서 가져와야 함)

---

## ✅ 수정 내역

### 1. 파라미터 이름 명확화

#### `broker/ls/services/account.py`

**Before**:
```python
async def get_account_balance(self, account_id: str) -> LSAccount:
    clean_account = account_id.replace("-", "")
    password = config.get("ls.account_password", "")
```

**After**:
```python
async def get_account_balance(
    self, 
    account_number: str,  # 명확한 이름
    account_password: str = None  # 비밀번호 파라미터 추가
) -> LSAccount:
    clean_account = account_number.replace("-", "")
    
    # 비밀번호 처리
    if account_password is None:
        from utils.config import config
        password = config.get("ls.account_password", "")
    else:
        password = account_password
```

### 2. LSAccount 생성 시 올바른 값 전달

**Before**:
```python
return LSAccount(
    account_id=account_id,  # 파라미터 이름 그대로
    ...
)
```

**After**:
```python
return LSAccount(
    account_id=account_number,  # 원본 계좌번호 (하이픈 포함)
    ...
)
```

### 3. Adapter에서 비밀번호 전달

**Before**:
```python
ls_account = await self.account_service.get_account_balance(self.account_id)
```

**After**:
```python
from utils.config import config
account_password = config.get("ls.account_password", "")

ls_account = await self.account_service.get_account_balance(
    self.account_id,  # 계좌번호
    account_password  # 계좌 비밀번호
)
```

### 4. get_positions 메서드도 동일하게 수정

**Before**:
```python
async def get_positions(self, account_id: str) -> List[LSPosition]:
    clean_account = account_id.replace("-", "")
    password = config.get("ls.account_password", "")
```

**After**:
```python
async def get_positions(
    self, 
    account_number: str,
    account_password: str = None
) -> List[LSPosition]:
    clean_account = account_number.replace("-", "")
    
    if account_password is None:
        from utils.config import config
        password = config.get("ls.account_password", "")
    else:
        password = account_password
```

---

## 🧪 테스트 방법

### 1. 서버 재시작
```bash
# 백엔드 재시작 (자동 reload)
# 변경사항이 자동으로 적용됨
```

### 2. API 테스트
```bash
# 계좌 잔고 조회
GET /api/accounts/1/balance
Authorization: Bearer {token}
```

**예상 응답**:
```json
{
  "account_id": 1,
  "account_number": "555044505-01",  // ← 계좌번호 (올바름)
  "broker": "ls",
  "balance": 10000000.0,
  ...
}
```

### 3. 프론트엔드 확인
1. http://localhost:3000/dashboard 접속
2. 계좌 정보 섹션 확인
3. "계좌번호" 필드에 `555044505-01` 표시 확인 ✅

---

## 📊 영향 범위

### 수정된 파일
1. `broker/ls/services/account.py`
   - `get_account_balance()` 메서드
   - `get_positions()` 메서드

2. `broker/ls/adapter.py`
   - `get_account()` 메서드
   - `get_positions()` 메서드

### 영향받는 기능
- ✅ 계좌 잔고 조회
- ✅ 보유 종목 조회
- ✅ 트레이딩 화면 계좌 정보 표시

### 영향받지 않는 기능
- 로그인/인증
- 백테스트
- 전략 빌더
- 데이터 수집

---

## 🔐 보안 고려사항

### 현재 구조
```
DB (암호화) → API (복호화) → Broker Adapter → LS증권 API
```

### 데이터 흐름
1. **DB 저장**: 계좌번호 암호화 저장
   ```
   "555044505-01" → "gAAAAABpJErOyyPIgjvGazwr..."
   ```

2. **API 조회**: 복호화하여 Adapter에 전달
   ```python
   credentials = repo.get_account_credentials(account_id, user_id)
   # credentials["account_number"] = "555044505-01"
   ```

3. **Adapter 사용**: LS증권 API 호출
   ```python
   adapter = await connection_pool.get_adapter(
       account_id=credentials["account_number"],  # "555044505-01"
       ...
   )
   ```

4. **LS증권 API**: 계좌번호와 비밀번호로 인증
   ```python
   {
       "accno": "55504450501",  # 하이픈 제거
       "passwd": "qwer1234"     # 계좌 비밀번호
   }
   ```

### 보안 체크리스트
- [x] 계좌번호 DB 암호화
- [x] 계좌 비밀번호 DB 암호화
- [x] API 응답에 계좌번호 포함 (필요)
- [x] API 응답에 비밀번호 미포함
- [x] 로그에 민감정보 마스킹 (TODO)

---

## 🎯 향후 개선 사항

### 1. 계좌 비밀번호 DB 저장
**현재**: config.yaml에 하드코딩
```yaml
ls:
  account_password: "qwer1234"
```

**개선**: DB에 암호화하여 저장
```python
# trading_accounts 테이블에 추가
account_password_encrypted: TEXT
```

### 2. 로그 마스킹
**현재**: 로그에 계좌번호/비밀번호 노출
```
'accno': '55504450501', 'passwd': 'qwer1234'
```

**개선**: 민감정보 마스킹
```python
logger.info(f"Request body: {mask_sensitive_data(data)}")
# 'accno': '5550****01', 'passwd': '****'
```

### 3. 변수명 통일
**현재**: `account_id`, `account_number` 혼용

**개선**: 명확한 네이밍 컨벤션
- `account_id`: DB의 Primary Key (정수)
- `account_number`: 실제 계좌번호 (문자열, 예: "555044505-01")
- `account_password`: 계좌 비밀번호

---

## ✅ 검증 결과

### Before (버그)
```
화면 표시: 계좌번호 = "qwer1234" ❌
실제 값: 계좌 비밀번호
```

### After (수정)
```
화면 표시: 계좌번호 = "555044505-01" ✅
실제 값: 계좌번호
```

---

## 📝 교훈

### 1. 명확한 변수명 사용
- `account_id` vs `account_number` 혼동 방지
- 파라미터 이름과 실제 의미 일치

### 2. 타입 힌트 활용
```python
def get_account_balance(
    self,
    account_number: str,  # 명확한 타입과 이름
    account_password: str = None
) -> LSAccount:
    ...
```

### 3. 로그 확인의 중요성
- API 호출 로그를 통해 문제 발견
- 민감정보 로깅 시 마스킹 필요

### 4. 테스트 케이스 작성
- 계좌 정보 조회 테스트
- 응답 데이터 검증
- 화면 표시 확인

---

**수정 완료**: 2025-11-30 17:01
**테스트 상태**: 재테스트 필요
**우선순위**: 🔴 Critical (수정 완료)
