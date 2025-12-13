# 내일 작업 사항 (2025-12-09)

## 🔥 긴급: 포트폴리오 백테스트 Syntax Error 해결

### 현재 상황
- **전략 ID**: 3 ("200일선초과일목상향돌파")
- **문제**: DB에 저장된 Python 코드에 syntax error (187번째 줄)
- **원인**: `_generate_select_universe_method()`에서 `.filter()` 메서드 체이닝 줄바꿈 오류

### 문제 코드 (DB에 저장된 상태)
```python
# 186번째 줄
query = db.query(StockMasterModel.symbol).filter(StockMasterModel.market_cap >= 100000000000.0)      
# 187번째 줄 - syntax error 발생
.filter(StockMasterModel.volume_amount >= 10000000000.0)
```

### 수정 완료 사항 ✅
**파일**: `api/routes/strategy_builder.py`
**함수**: `_generate_select_universe_method()`

**수정 내용**:
```python
# 기존 (문제)
filter_conditions = "\n            ".join([f".filter({cond})" for cond in conditions])
query = db.query(StockMasterModel.symbol){filter_conditions}

# 수정 후 (해결)
filter_lines = []
for cond in conditions:
    filter_lines.append(f"            query = query.filter({cond})")
filter_conditions = "\n".join(filter_lines)

# 생성되는 코드:
query = db.query(StockMasterModel.symbol)
query = query.filter(StockMasterModel.market_cap >= 100000000000.0)
query = query.filter(StockMasterModel.volume_amount >= 10000000000.0)
```

### 내일 작업 순서

#### 1단계: 백엔드 확인
```bash
# 백엔드가 실행 중인지 확인
# 프로세스 ID 5로 실행 중
python -m uvicorn api.main:app --reload --port 8000
```

#### 2단계: 프론트엔드에서 전략 재저장
1. 브라우저에서 `http://localhost:3000/my-strategies` 접속
2. "200일선초과일목상향돌파" 전략의 **수정** 버튼 클릭
3. 전략 빌더 페이지에서 아무것도 변경하지 말고
4. **저장** 버튼 클릭
5. 저장 성공 팝업 확인

#### 3단계: DB 확인
```bash
python scripts/check_strategy_db.py
```

**확인 사항**:
- `updated_at` 시간이 최신으로 변경되었는지
- 187번째 줄이 `query = query.filter(...)` 형태로 변경되었는지
- `select_universe()` 메서드가 정상적으로 생성되었는지

#### 4단계: 백테스트 실행 테스트
1. 백테스트 페이지 접속
2. 전략: "200일선초과일목상향돌파" 선택
3. 기간: 2025-08-14 ~ 2025-11-21 (데이터 있는 기간)
4. **종목 입력란이 자동으로 숨겨져야 함** (포트폴리오 전략)
5. 백테스트 실행
6. 결과 확인

#### 5단계: 에러 발생 시 디버깅
```bash
# 백엔드 로그 확인
# 프로세스 출력 보기

# 생성된 코드 직접 확인
python scripts/check_strategy_db.py

# 코드 문법 검사
python -m py_compile data/debug_strategy_3.py
```

---

## 📋 구현 완료된 기능 (복습)

### 백엔드 (api/routes/strategy_builder.py)
✅ `_has_stock_selection_criteria()` - 종목 선정 조건 확인
✅ `_generate_select_universe_method()` - select_universe 메서드 생성 (수정 완료)
✅ `generate_strategy_code()` - 포트폴리오 전략 코드 생성
✅ `save_strategy()` - UPDATE/INSERT 로직
✅ `list_strategies()` - is_portfolio 필드 추가

### 프론트엔드
✅ `StrategyBuilderPage.tsx` - 수정 모드 지원 (editingStrategyId)
✅ `BacktestPage.tsx` - 포트폴리오 전략 자동 감지 및 symbol 입력란 숨김

### 백테스트 API
✅ `/api/backtest/portfolio` - 포트폴리오 전용 엔드포인트
✅ 전략 빌더 전략 동적 로딩

---

## 🎯 목표
- 전략 빌더에서 종목 선정 조건을 설정하면
- 자동으로 `select_universe()` 메서드가 생성되고
- 백테스트 시 종목을 자동으로 선정하여
- 포트폴리오 백테스트가 실행되도록

---

## 🔍 확인용 스크립트

### DB 상태 확인
```bash
python scripts/check_strategy_db.py
```

### 백엔드 로그 확인
```bash
# 프로세스 출력 확인 (Kiro IDE에서)
# 또는 터미널에서 직접 실행
```

### 생성된 코드 문법 검사
```bash
python -m py_compile data/debug_strategy_3.py
```

---

## 📝 참고 사항

### 현재 데이터 기간
- OHLC 데이터: 2025-08-14 ~ 2025-11-21 (100 bars)
- 백테스트 시 이 기간 내에서 테스트해야 함

### 전략 ID 3 설정
- 이름: "200일선초과일목상향돌파"
- 종목 선정 조건:
  - 시가총액: 1000억 이상
  - 거래대금: 100억 이상
  - 가격: 1000원 이상
  - 시장: KOSPI, KOSDAQ
  - 관리종목 제외
- 매수 조건: 2개 (MA 관련)
- 매도 조건: 0개
- 진입 방식: 피라미딩 (4단계)
- 포지션 사이징: ATR 기반 리스크 관리

### 예상 결과
- 종목 자동 선정 (PER 낮은 순으로 최대 50개)
- 각 종목별로 매수/매도 신호 생성
- 포트폴리오 전체 수익률 계산
- MDD, Sharpe Ratio 등 메트릭 계산

---

**작성일**: 2025-12-08 23:30
**백엔드 상태**: 실행 중 (프로세스 ID 5)
**프론트엔드 상태**: 실행 필요
**다음 작업**: 전략 재저장 → DB 확인 → 백테스트 실행
