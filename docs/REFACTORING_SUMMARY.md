# si-trading-system 리팩토링 요약

## 개요
2025-11-24 수행된 전체 시스템 리팩토링 내역

---

## 📋 개선 사항

### 1. 캔들(바) 생성 로직 구현 ✅

**변경 파일:**
- `core/execution/engine.py`
- `utils/bar_utils.py` (신규)

**주요 개선:**
- `_create_bars_from_history()` 완전 구현
- price_update (dict 형태) → OHLCV DataFrame 변환
- pandas resample을 활용한 타임프레임별 집계
- NaN/음수/invalid 데이터 자동 처리
- value 컬럼 자동 계산 (volume * price)

**타임프레임 설정:**
- `config.yaml`에 `execution.timeframe` 추가 (기본값: "1m")
- 지원 타임프레임: 1m, 5m, 15m, 30m, 1h, 4h, 1d

---

### 2. 전략 인터페이스 명확화 ✅

**변경 파일:**
- `core/strategy/base.py`
- `core/strategy/examples/ma_cross.py`
- `core/backtest/engine.py`
- `utils/types.py`

**주요 개선:**
- `on_bar()` 시그니처 변경: `List[OHLC]` → `pd.DataFrame`
- DataFrame 형식: timestamp 인덱스, ['open', 'high', 'low', 'close', 'volume', 'value'] 컬럼
- 상세한 docstring 및 사용 예제 추가
- OHLC 클래스에 `value` 필드 추가

**전략 작성 패턴:**
```python
def on_bar(self, bars: pd.DataFrame, positions: List[Position], account: Account) -> List[OrderSignal]:
    # pandas를 활용한 지표 계산
    ma20 = bars['close'].rolling(20).mean()
    
    # 신호 생성
    if 조건:
        return [OrderSignal(...)]
    return []
```

---

### 3. 데이터 유효성 및 안전성 검증 ✅

**변경 파일:**
- `utils/bar_utils.py` (신규)
- `core/execution/engine.py`
- `core/strategy/examples/ma_cross.py`

**주요 개선:**
- `validate_bars()` 함수: 필수 컬럼 확인, high/low 검증, 음수 제거
- NaN 처리: forward fill 적용
- value 컬럼 fallback: `volume * close`로 자동 계산
- Zero volume 처리
- 전략별 `_validate_bars()` 메서드 추가

---

### 4. 주문·리스크 처리 안정화 ✅

**변경 파일:**
- `core/execution/engine.py`
- `core/strategy/examples/ma_cross.py`

**주요 개선:**
- 재시도 로직 구현 (최대 3회, 지수 백오프)
- 타임아웃/네트워크 오류 처리
- 중복 진입 방지 로직 강화
- 포지션 보유 중 같은 방향 진입 차단

**재시도 로직:**
```python
max_retries = 3
retry_delay = 1.0  # 초, 지수 백오프
- TimeoutError: 재시도
- ConnectionError: 재시도
- 기타 예외: 즉시 중단
```

---

### 5. 디버깅 및 운영 가시성 강화 ✅

**변경 파일:**
- `utils/signal_logger.py` (신규)
- `core/strategy/examples/ma_cross.py`

**주요 개선:**
- `SignalLogger` 클래스 구현
- 진입/청산 시점마다 상세 로그 (신호 이유, 지표 값, 손익률)
- 외부 알림 hook 인터페이스 제공 (Telegram/Slack 연동 가능)
- 상태 기록 (매수/매도/관망) - 분석/시각화용

**로그 예시:**
```
[MACrossStrategy] 골든크로스 매수 신호
종목: 005930
수량: 100주
현재가: 70,000원
예상 금액: 7,000,000원
계좌 자산: 10,000,000원
신호 이유: 골든크로스: 단기MA(5)가 장기MA(20)를 상향 돌파
지표 값:
  - 단기MA: 69500.00
  - 장기MA: 68000.00
```

---

## 📁 신규 파일

### 1. `utils/bar_utils.py`
OHLCV 바 생성 및 검증 공통 유틸리티
- `validate_bars()`: 데이터 검증 및 정리
- `create_bars_from_ticks()`: 틱 데이터 → OHLCV 바 변환
- `ohlc_list_to_dataframe()`: OHLC 리스트 → DataFrame
- `dataframe_to_ohlc_list()`: DataFrame → OHLC 리스트

### 2. `utils/signal_logger.py`
신호 로깅 및 알림 유틸리티
- `SignalLogger` 클래스
- `log_entry_signal()`: 진입 신호 로깅
- `log_exit_signal()`: 청산 신호 로깅
- `log_state()`: 전략 상태 로깅
- 외부 알림 hook 지원

---

## 🔧 설정 변경

### `config.yaml`
```yaml
# 실행 엔진 설정 (신규)
execution:
  timeframe: "1m"  # 기본 타임프레임 (1m, 5m, 15m, 30m, 1h, 4h, 1d)
```

---

## 📊 사용 예제

### 전략 작성 (새 인터페이스)
```python
from core.strategy.base import BaseStrategy
from utils.signal_logger import get_signal_logger, SignalType
import pandas as pd

signal_logger = get_signal_logger()

class MyStrategy(BaseStrategy):
    def on_bar(self, bars: pd.DataFrame, positions, account):
        # 데이터 검증
        if len(bars) < 20:
            return []
        
        # pandas 활용
        ma20 = bars['close'].rolling(20).mean()
        current_price = bars['close'].iloc[-1]
        
        # 신호 생성
        if current_price > ma20.iloc[-1]:
            signal = OrderSignal(...)
            
            # 상세 로깅
            signal_logger.log_entry_signal(
                strategy_name=self.name,
                signal=signal,
                reason="가격이 MA20 돌파",
                current_price=current_price,
                account_equity=account.equity,
                indicators={'MA20': ma20.iloc[-1]}
            )
            
            return [signal]
        
        return []
```

### 외부 알림 설정
```python
from utils.signal_logger import set_notification_hook

async def telegram_hook(message: str, level: str):
    # Telegram 전송 로직
    await send_telegram(message)

set_notification_hook(telegram_hook)
```

---

## ✅ 테스트 체크리스트

- [ ] 백테스트 엔진 정상 작동 확인
- [ ] 실시간 실행 엔진 정상 작동 확인
- [ ] MA Cross 전략 테스트
- [ ] 데이터 검증 로직 테스트
- [ ] 재시도 로직 테스트
- [ ] SignalLogger 테스트
- [ ] 외부 알림 hook 테스트

---

## 🚀 다음 단계

1. **추가 전략 마이그레이션**
   - 기존 전략들을 새 인터페이스로 변환
   
2. **리스크 관리 강화**
   - 손절/익절 자동 실행
   - 포지션별 리스크 추적

3. **모니터링 대시보드**
   - SignalLogger 데이터 시각화
   - 실시간 전략 상태 모니터링

4. **알림 시스템 구현**
   - Telegram Bot 연동
   - Slack Webhook 연동

---

## 📝 주의사항

1. **기존 전략 호환성**
   - 기존 `List[OHLC]` 기반 전략은 수정 필요
   - `on_bar()` 시그니처 변경 필수

2. **타임프레임 설정**
   - 전역 타임프레임 사용 (config.yaml)
   - 전략별 타임프레임은 향후 지원 예정

3. **데이터 형식**
   - price_update는 반드시 timestamp 포함
   - value가 None이면 자동 계산됨

---

## 📚 참고 문서

- [전략 작성 가이드](./STRATEGY_GUIDE.md) (작성 예정)
- [리스크 관리 가이드](./RISK_MANAGEMENT.md) (작성 예정)
- [알림 설정 가이드](./NOTIFICATION_GUIDE.md) (작성 예정)
