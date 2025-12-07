# OHLC 데이터 수집 전략 계획

## 🎯 변경 요구사항

### 1. 수정주가 적용
- **현재**: `sujung: "N"` (비수정주가)
- **변경**: `sujung: "Y"` (수정주가)

### 2. 거래소 구분 변경
- **현재**: `exchgubun: "K"` (KRX)
- **변경**: `exchgubun: "U"` (???)

---

## 🤔 고려사항

### A. exchgubun 옵션 확인 필요

| 값 | 의미 | 비고 |
|----|------|------|
| K | KRX | 한국거래소 (코스피+코스닥) |
| U | ??? | **확인 필요** |
| N | NASDAQ | 나스닥 |
| A | AMEX | 아메리칸 증권거래소 |
| S | NYSE | 뉴욕 증권거래소 |

**질문**: `U`가 무엇을 의미하는지 확인 필요
- 가능성 1: US (미국 전체)
- 가능성 2: Unknown/Undefined
- 가능성 3: LS증권 문서 확인 필요

---

## 📊 현재 DB 구조 분석

### OHLCModel 테이블
```python
class OHLCModel(Base):
    __tablename__ = "ohlc_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)  # 1d, 1m, 5m
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

**현재 구조의 특징**:
- ✅ `symbol`, `interval`, `timestamp`로 데이터 구분
- ❌ `exchgubun` (거래소 구분) 필드 없음
- ❌ `sujung` (수정주가 여부) 필드 없음

---

## 🔀 전략 옵션

### 옵션 1: 단순 변경 (기존 데이터 덮어쓰기)

**방법**:
```python
# broker/ls/services/market.py
"sujung": "Y",      # N → Y
"exchgubun": "U"    # K → U
```

**장점**:
- 구현 간단
- DB 스키마 변경 불필요
- 즉시 적용 가능

**단점**:
- 기존 데이터와 혼재 (비수정주가 + 수정주가)
- 거래소 구분 추적 불가
- 데이터 일관성 문제

**권장**: ❌ 비권장 (데이터 혼란)

---

### 옵션 2: DB 스키마 확장 (필드 추가)

**방법**:
```python
class OHLCModel(Base):
    __tablename__ = "ohlc_data"
    
    # 기존 필드
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 신규 필드 추가
    exchgubun = Column(String(10), nullable=True, default="K")  # 거래소 구분
    is_adjusted = Column(Boolean, nullable=True, default=False)  # 수정주가 여부
    
    # OHLC 데이터
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
```

**마이그레이션**:
```sql
-- 1. 필드 추가
ALTER TABLE ohlc_data ADD COLUMN exchgubun VARCHAR(10) DEFAULT 'K';
ALTER TABLE ohlc_data ADD COLUMN is_adjusted BOOLEAN DEFAULT FALSE;

-- 2. 인덱스 추가 (조회 성능)
CREATE INDEX idx_ohlc_exchgubun ON ohlc_data(symbol, interval, exchgubun, timestamp);

-- 3. 기존 데이터 업데이트
UPDATE ohlc_data SET exchgubun = 'K', is_adjusted = FALSE WHERE exchgubun IS NULL;
```

**장점**:
- 데이터 구분 명확
- 여러 거래소 데이터 동시 저장 가능
- 수정주가/비수정주가 선택 가능
- 기존 데이터 보존

**단점**:
- DB 마이그레이션 필요
- 코드 수정 범위 증가
- 스토리지 증가

**권장**: ✅ 권장 (확장성, 명확성)

---

### 옵션 3: 별도 테이블 생성

**방법**:
```python
class OHLCModel(Base):
    """기존 테이블 (비수정주가, KRX)"""
    __tablename__ = "ohlc_data"

class OHLCAdjustedModel(Base):
    """수정주가 테이블"""
    __tablename__ = "ohlc_data_adjusted"
    
    # 동일한 구조
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchgubun = Column(String(10), nullable=False, default="K")
    # ...
```

**장점**:
- 기존 시스템 영향 최소화
- 데이터 분리 명확
- 롤백 용이

**단점**:
- 테이블 관리 복잡
- 코드 중복 가능성
- 쿼리 복잡도 증가

**권장**: ⚠️ 조건부 권장 (대규모 데이터 시)

---

## 💡 권장 방안: 옵션 2 (스키마 확장)

### 단계별 구현 계획

#### Phase 1: DB 스키마 확장
```sql
-- 1. 필드 추가
ALTER TABLE ohlc_data ADD COLUMN exchgubun VARCHAR(10) DEFAULT 'K';
ALTER TABLE ohlc_data ADD COLUMN is_adjusted BOOLEAN DEFAULT FALSE;

-- 2. 기존 데이터 마킹
UPDATE ohlc_data SET exchgubun = 'K', is_adjusted = FALSE;

-- 3. 인덱스 추가
CREATE INDEX idx_ohlc_full ON ohlc_data(symbol, interval, exchgubun, is_adjusted, timestamp);
```

#### Phase 2: 모델 업데이트
```python
# data/models.py
class OHLCModel(Base):
    __tablename__ = "ohlc_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 신규 필드
    exchgubun = Column(String(10), nullable=False, default="K", index=True)
    is_adjusted = Column(Boolean, nullable=False, default=False, index=True)
    
    # OHLC
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

#### Phase 3: API 수정
```python
# broker/ls/services/market.py
async def get_daily_ohlc(
    self,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    exchgubun: str = "K",      # 파라미터 추가
    is_adjusted: bool = True   # 파라미터 추가
) -> List[OHLC]:
    """일봉 데이터 조회"""
    
    response = await self.client.request(
        method="POST",
        endpoint="/stock/chart",
        data={
            "t8451InBlock": {
                "shcode": symbol,
                "gubun": "2",
                "qrycnt": 500,
                "sdate": start_date.strftime("%Y%m%d"),
                "edate": end_date.strftime("%Y%m%d"),
                "cts_date": "",
                "comp_yn": "N",
                "sujung": "Y" if is_adjusted else "N",  # 동적 설정
                "exchgubun": exchgubun                   # 동적 설정
            }
        },
        headers={
            "tr_id": "t8451",
            "tr_cont": "N",
            "custtype": "P"
        }
    )
    
    # OHLC 객체에 메타데이터 추가
    ohlc_list = []
    for item in response.get("t8451OutBlock1", []):
        ohlc = OHLC(
            symbol=symbol,
            timestamp=datetime.strptime(item.get("date", ""), "%Y%m%d"),
            open=float(item.get("open", 0)),
            high=float(item.get("high", 0)),
            low=float(item.get("low", 0)),
            close=float(item.get("close", 0)),
            volume=int(item.get("jdiff_vol", 0)),
            exchgubun=exchgubun,        # 추가
            is_adjusted=is_adjusted     # 추가
        )
        ohlc_list.append(ohlc)
    
    return ohlc_list
```

#### Phase 4: Repository 수정
```python
# data/repository.py
async def save_ohlc(
    self,
    symbol: str,
    interval: str,
    ohlc_list: List[OHLC],
    exchgubun: str = "K",
    is_adjusted: bool = True
):
    """OHLC 데이터 저장"""
    
    for ohlc in ohlc_list:
        # 중복 체크 (symbol, interval, timestamp, exchgubun, is_adjusted)
        existing = self.session.query(OHLCModel).filter(
            OHLCModel.symbol == symbol,
            OHLCModel.interval == interval,
            OHLCModel.timestamp == ohlc.timestamp,
            OHLCModel.exchgubun == exchgubun,
            OHLCModel.is_adjusted == is_adjusted
        ).first()
        
        if existing:
            # 업데이트
            existing.open = ohlc.open
            existing.high = ohlc.high
            existing.low = ohlc.low
            existing.close = ohlc.close
            existing.volume = ohlc.volume
        else:
            # 신규 삽입
            new_ohlc = OHLCModel(
                symbol=symbol,
                interval=interval,
                timestamp=ohlc.timestamp,
                exchgubun=exchgubun,
                is_adjusted=is_adjusted,
                open=ohlc.open,
                high=ohlc.high,
                low=ohlc.low,
                close=ohlc.close,
                volume=ohlc.volume
            )
            self.session.add(new_ohlc)
    
    self.session.commit()
```

#### Phase 5: 조회 API 수정
```python
# data/repository.py
async def get_ohlc(
    self,
    symbol: str,
    interval: str,
    start_date: datetime,
    end_date: datetime,
    exchgubun: str = "K",
    is_adjusted: bool = True
) -> List[OHLC]:
    """OHLC 데이터 조회"""
    
    results = self.session.query(OHLCModel).filter(
        OHLCModel.symbol == symbol,
        OHLCModel.interval == interval,
        OHLCModel.timestamp >= start_date,
        OHLCModel.timestamp <= end_date,
        OHLCModel.exchgubun == exchgubun,
        OHLCModel.is_adjusted == is_adjusted
    ).order_by(OHLCModel.timestamp).all()
    
    return [self._to_ohlc(r) for r in results]
```

---

## 📈 데이터 저장 예시

### 기존 (현재)
```
symbol | interval | timestamp  | open | high | low | close | volume
-------|----------|------------|------|------|-----|-------|-------
005930 | 1d       | 2025-11-28 | 103k | 103k | 100k| 100k  | 14M
```

### 변경 후
```
symbol | interval | timestamp  | exchgubun | is_adjusted | open | high | low | close | volume
-------|----------|------------|-----------|-------------|------|------|-----|-------|-------
005930 | 1d       | 2025-11-28 | K         | FALSE       | 103k | 103k | 100k| 100k  | 14M  (기존)
005930 | 1d       | 2025-11-28 | K         | TRUE        | 102k | 102k | 99k | 99k   | 14M  (수정주가)
005930 | 1d       | 2025-11-28 | U         | TRUE        | 103k | 103k | 100k| 100k  | 14M  (U 거래소)
```

---

## ⚠️ 주의사항

### 1. exchgubun = "U" 확인 필요
- LS증권 API 문서 확인
- 테스트 호출로 응답 확인
- 에러 발생 시 대체 방안

### 2. 수정주가 vs 비수정주가
**수정주가 (is_adjusted=TRUE)**:
- 장점: 액면분할, 배당 등 반영 → 차트 연속성
- 단점: 실제 거래가격과 다름
- 용도: 기술적 분석, 백테스트

**비수정주가 (is_adjusted=FALSE)**:
- 장점: 실제 거래가격
- 단점: 액면분할 시 차트 단절
- 용도: 실거래, 주문

### 3. 스토리지 증가
- 기존: 1개 데이터 세트
- 변경 후: 최대 4개 데이터 세트 (K/U × 수정/비수정)
- 예상 증가율: 2~4배

### 4. 기존 데이터 처리
**옵션 A**: 기존 데이터 유지
```sql
-- 기존 데이터는 K, 비수정주가로 마킹
UPDATE ohlc_data SET exchgubun = 'K', is_adjusted = FALSE;
```

**옵션 B**: 기존 데이터 삭제 후 재수집
```sql
-- 깨끗하게 시작
TRUNCATE TABLE ohlc_data;
-- 새로운 기준으로 재수집
```

---

## 🎯 최종 권장사항

### 즉시 실행
1. **exchgubun = "U" 의미 확인**
   - LS증권 API 문서 확인
   - 테스트 호출

2. **요구사항 명확화**
   - U 거래소가 필요한 이유?
   - 수정주가만 필요? 비수정주가도 필요?
   - 기존 데이터 보존 필요?

### 구현 순서
1. exchgubun 확인 및 테스트
2. DB 스키마 설계 확정
3. 마이그레이션 스크립트 작성
4. 모델 및 API 수정
5. 테스트 및 검증
6. 기존 데이터 처리 결정
7. 프로덕션 적용

---

## 🤔 결정이 필요한 질문

1. **exchgubun = "U"가 무엇인가요?**
   - LS증권 문서 확인 필요
   - 테스트 필요

2. **수정주가만 필요한가요, 아니면 둘 다 필요한가요?**
   - 수정주가만: `is_adjusted` 필드 불필요
   - 둘 다: `is_adjusted` 필드 필요

3. **기존 데이터는 어떻게 할까요?**
   - 보존: 마이그레이션 + 마킹
   - 삭제: 재수집

4. **여러 거래소 데이터를 동시에 저장할까요?**
   - 예: `exchgubun` 필드 필요
   - 아니오: 단순 변경만

이 질문들에 답하면 정확한 구현 계획을 세울 수 있습니다!
