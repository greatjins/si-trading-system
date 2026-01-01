# ICT Pyramiding 전략 리팩토링 완료 보고서

## 개요
LS증권 API 연동 시스템 매매 코드를 명세서에 따라 리팩토링 완료.

## 구현 완료 항목

### 1. Data Layer - Parquet 캐싱 기능 추가 ✅

**파일**: `broker/ls/adapter.py`

**변경 사항**:
- `get_ohlc()` 메서드에 Parquet 캐싱 로직 추가
- 캐시 우선 전략: Parquet 파일 확인 → 없으면 API 호출 → 저장

**동작 방식**:
```python
# 1. Parquet 파일에서 로드 시도
cached_data = await storage.load_ohlc(symbol, interval, start_date, end_date)

# 2. 캐시 미스 시 API 호출
if not cached_data:
    ohlc_list = await self.market_service.get_daily_ohlc(...)
    
# 3. API 데이터를 Parquet에 저장
await storage.save_ohlc(symbol, interval, ohlc_list)
```

**효과**:
- API 호출 횟수 감소
- 데이터 수집 속도 향상
- 로컬 저장소 활용으로 안정성 향상

---

### 2. ICT_Analyzer 클래스 생성 ✅

**파일**: `core/strategy/ict_analyzer.py`

**주요 기능**:
1. **FVG (Fair Value Gap) 탐지**
   - 3개 봉 패턴 분석
   - Bullish/Bearish FVG 식별
   - 최소 크기 임계값 적용

2. **Order Block (OB) 탐지**
   - 높은 거래량 + 큰 몸통 패턴
   - 이후 가격 반응 확인
   - 강도(strength) 계산

3. **지지/저항 레벨 식별**
   - Swing High/Low 찾기
   - 가격 클러스터링

4. **Multi-timeframe 매칭**
   - 일봉 레벨과 60분봉 가격 매칭
   - 진입 신호 신뢰도 계산

**사용 예시**:
```python
analyzer = ICTAnalyzer(fvg_threshold=0.002, ob_volume_ratio=1.5)

# 일봉 분석
fvgs = analyzer.detect_fvg(daily_bars)
obs = analyzer.detect_order_blocks(daily_bars)

# 60분봉 매칭
signals = analyzer.match_price_levels(daily_levels, minute_bars)
```

---

### 3. Multi-Timeframe 진입 시그널 로직 ✅

**파일**: `core/strategy/examples/ict_pyramiding.py`

**전략 흐름**:
1. **일봉 분석 (Setup)**
   - 거래량이 터진 날의 OHLC 기준
   - FVG/OB 탐지
   - 지지/저항 레벨 식별

2. **60분봉 진입 (Entry)**
   - 일봉에서 찾은 가격대 도달 확인
   - 진입 컨펌
   - 포지션 사이징

3. **Pyramiding (추가 매수)**
   - 추세 지속 시 추가 매수
   - 리스크 관리 동반
   - 최대 추가 매수 횟수 제한

4. **청산 (Exit)**
   - ICT 추세 이탈
   - 볼린저 밴드 하향 돌파
   - 대량 거래 음봉 발생 시 분할 매도

**핵심 메서드**:
- `analyze_daily_candles()`: 일봉 분석
- `_check_entry_signal()`: 60분봉 진입 확인
- `_check_pyramid_signal()`: 추가 매수 확인
- `_check_exit_signal()`: 청산 확인

---

### 4. JSON 기반 Strategy Factory 구현 ✅

**파일**: `core/strategy/factory.py`, `api/routes/backtest.py`

**변경 사항**:
- ❌ **제거**: `exec()` 방식 (보안 위험, 유지보수 어려움)
- ✅ **추가**: JSON 설정 기반 전략 생성

**새로운 구조**:
```python
# JSON 설정 예시
{
    "strategy_type": "ict_pyramiding",
    "parameters": {
        "symbol": "005930",
        "fvg_threshold": 0.002,
        "pyramid_levels": 2
    },
    "name": "My ICT Strategy"
}

# Factory 사용
strategy = StrategyFactory.create_from_json(config)
```

**장점**:
- 보안성 향상 (코드 실행 없음)
- 유지보수 용이 (JSON 파싱)
- 타입 안정성
- 확장성 (새 전략 타입 추가 용이)

**DB 호환성**:
- 기존 `StrategyBuilderModel.config` (JSON) 필드 활용
- `python_code` 필드는 참고용으로만 유지

---

## 파일 구조

```
broker/ls/
  └── adapter.py              # Parquet 캐싱 추가

core/strategy/
  ├── ict_analyzer.py          # NEW: ICT 분석기
  ├── factory.py               # NEW: JSON 기반 팩토리
  └── examples/
      └── ict_pyramiding.py    # NEW: Multi-timeframe 전략

api/routes/
  └── backtest.py              # exec() 제거, Factory 사용
```

---

## 사용 방법

### 1. 데이터 수집 (자동 캐싱)
```python
adapter = LSAdapter(...)
ohlc_data = await adapter.get_ohlc(
    symbol="005930",
    interval="1d",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
# 자동으로 Parquet에 캐싱됨
```

### 2. ICT 분석
```python
from core.strategy.ict_analyzer import ICTAnalyzer

analyzer = ICTAnalyzer()
fvgs = analyzer.detect_fvg(daily_bars)
obs = analyzer.detect_order_blocks(daily_bars)
```

### 3. 전략 생성 (JSON)
```python
from core.strategy.factory import StrategyFactory

config = {
    "strategy_type": "ict_pyramiding",
    "parameters": {
        "symbol": "005930",
        "fvg_threshold": 0.002
    }
}

strategy = StrategyFactory.create_from_json(config)
```

### 4. 백테스트 실행
```python
# API 호출 시 자동으로 JSON 설정 사용
POST /api/backtest/run
{
    "strategy_name": "ict_pyramiding",
    "symbol": "005930",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}
```

---

## 향후 개선 사항

1. **Multi-timeframe 데이터 제공**
   - 백테스트 엔진에서 일봉과 60분봉을 동시에 제공
   - `on_bar()`에서 두 타임프레임 모두 접근 가능하도록

2. **벡터화된 백테스팅**
   - 루프 방식 → Pandas Vectorization
   - 대량 데이터 연산 최적화

3. **데이터 표준화**
   - 모든 시장(주식/코인) 공통 스키마 적용
   - `timestamp, o, h, l, c, v` 형식

4. **전략 확장**
   - CCXT (코인) 지원
   - 해외주식 지원

---

## 테스트 체크리스트

- [ ] Parquet 캐싱 동작 확인
- [ ] ICT_Analyzer FVG/OB 탐지 정확도
- [ ] Multi-timeframe 매칭 로직 검증
- [ ] JSON Factory 전략 생성 테스트
- [ ] 백테스트 엔진 통합 테스트

---

## 참고 사항

- 기존 `exec()` 방식은 완전히 제거됨
- `StrategyBuilderModel.python_code` 필드는 참고용으로만 유지
- 모든 전략은 JSON 설정 기반으로 생성됨
- 전략 레지스트리에 `ict_pyramiding` 등록 완료

---

**작성일**: 2024-12-XX
**작성자**: AI Assistant
