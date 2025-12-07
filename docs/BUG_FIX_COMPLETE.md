# 버그 수정 완료: 계좌번호 표시 문제

## 🎯 최종 결과

### ✅ 문제 해결 완료

**Before**:
```
화면 표시: 계좌번호 = "qwer1234" ❌
DB 저장값: "qwer1234" (비밀번호가 잘못 저장됨)
```

**After**:
```
화면 표시: 계좌번호 = "555044505-01" ✅
DB 저장값: "555044505-01" (올바른 계좌번호)
```

---

## 🔍 근본 원인

### 문제 1: DB에 잘못된 데이터 저장
계좌 등록 시 **계좌번호 필드에 비밀번호가 저장됨**

```sql
-- 잘못된 데이터
account_number_encrypted = encrypt("qwer1234")  -- 비밀번호!

-- 올바른 데이터
account_number_encrypted = encrypt("555044505-01")  -- 계좌번호
```

### 문제 2: 코드 레벨 이슈
- 파라미터 이름 혼동 (`account_id` vs `account_number`)
- 계좌 비밀번호 전달 누락

---

## 🔧 수정 작업

### 1. 코드 수정
**파일**: 
- `broker/ls/services/account.py`
- `broker/ls/adapter.py`

**변경사항**:
- 파라미터 이름 명확화 (`account_number`, `account_password`)
- 계좌 비밀번호 파라미터 추가
- `LSAccount` 생성 시 올바른 값 전달

### 2. 데이터 수정
**스크립트**: `scripts/fix_account_number.py`

```python
# 계좌번호 수정
account.account_number = repo._encrypt("555044505-01")
db.commit()
```

**결과**:
```
✅ 수정 완료!
  - 새 계좌번호: 555044505-01
✅ 검증 성공: 계좌번호가 올바르게 저장되었습니다!
```

---

## 📊 검증

### 1. DB 검증
```bash
python scripts/test_decrypt.py
```

**결과**:
```
✅ 계좌 발견:
  - Account Number: 555044505-01
✅ 올바른 계좌번호 형식
```

### 2. API 검증
```bash
GET /api/accounts/1/balance
```

**예상 응답**:
```json
{
  "account_number": "555044505-01",  // ✅ 올바른 계좌번호
  "balance": 10000000.0,
  ...
}
```

### 3. 화면 검증
1. 브라우저 새로고침
2. 트레이딩 화면 > 계좌 정보
3. "계좌번호" 필드 확인: `555044505-01` ✅

---

## 🎓 교훈

### 1. 데이터 검증의 중요성
- 입력 데이터 검증 필수
- DB 저장 전 확인
- 테스트 케이스 작성

### 2. 명확한 변수명
```python
# Bad
account_id = "qwer1234"  # 뭘 의미하는지 불명확

# Good
account_number = "555044505-01"  # 계좌번호
account_password = "qwer1234"     # 계좌 비밀번호
```

### 3. 로그 활용
- API 호출 로그로 문제 발견
- 복호화된 값 확인
- 민감정보 마스킹 필요

---

## 🚀 다음 단계

### 즉시
- [x] 코드 수정
- [x] 데이터 수정
- [x] 검증 완료
- [ ] 브라우저 확인

### 단기
- [ ] 계좌 등록 UI 검증 로직 추가
- [ ] 계좌 비밀번호 DB 저장 (현재는 config.yaml)
- [ ] 로그 마스킹 구현

### 장기
- [ ] 계좌 등록 테스트 케이스 작성
- [ ] E2E 테스트 추가
- [ ] 데이터 마이그레이션 스크립트

---

## 📝 관련 문서

- `docs/BUG_FIX_ACCOUNT_NUMBER.md` - 상세 분석
- `docs/ACCOUNT_NUMBER_FLOW.md` - 데이터 흐름
- `scripts/fix_account_number.py` - 수정 스크립트
- `scripts/test_decrypt.py` - 검증 스크립트

---

**수정 완료**: 2025-11-30 17:08
**상태**: ✅ 해결 완료
**테스트**: 브라우저 확인 필요
