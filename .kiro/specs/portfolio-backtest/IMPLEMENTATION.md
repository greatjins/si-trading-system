# 포트폴리오 백테스트 구현 완료

## 구현 완료 (2024-12-08)

### Phase 1: 전략 인터페이스 확장 ✅

**파일**: `core/strategy/base.py`

```python
class BaseStrategy:
    def select_universe(self, date, market_data) -> List[str]:
        """매일 거래할 종목 선택"""
        return []  # 기본: 빈 리스트 (하위 호환)
    
    def get_target_weights(self, universe, market_data, account) -> Dict[str, float]:
        """목표 비중 계산"""
        return {symbol: 1.0/len(universe) for symbol in universe}  # 기본: 균등 분배
    
    def is_portfolio_strategy(self) -> bool:
        """포트폴리오 전략 여부"""
        return self.__class__.select_universe != BaseStrategy.select_universe
```

**예제 전략**: `core/strategy/examples/value_portfolio.py`
- PER/PBR/ROE 기반 가치주 선택
- 거래대금 상위 N개
- 균등 분배

### Phase 2: 백테스트 엔진 확장 ✅

**파일**: `core/backtest/engine.py`

```python
class BacktestEngine:
    async def run(self, ohlc_data=None, start_date=None, end_date=None):
        """자동으로 단일/포트폴리오 모드 선택"""
        if self.strategy.is_portfolio_strategy():
            return await self.run_portfolio(start_date, end_date)
        else:
            return await self.run_single(ohlc_data, start_date, end_date)
    
    async def run_single(self, ohlc_data, start_date, end_date):
        """기존 단일 종목 백테스트"""
        # 기존 로직 유지
    
    async def run_portfolio(self, start_date, end_date):
        """새로운 포트폴리오 백테스트"""
        for date in trading_days:
            # 1. 시장 데이터 로드
            market_data = await self._load_market_snapshot(date, repo)
            
            # 2. 종목 선택
            universe = self.strategy.select_universe(date, market_data)
            
            # 3. 목표 비중 계산
            target_weights = self.strategy.get_target_weights(universe, market_data, account)
            
            # 4. 리밸런싱
            await self._rebalance_portfolio(universe, target_weights, market_data, date, repo)
            
            # 5. 자산 기록
            self._update_equity(date)
```

### Phase 3: API 수정 ✅

**파일**: `api/schemas.py`

```python
class BacktestRequest(BaseModel):
    strategy_name: str
    parameters: Dict[str, Any]
    symbol: Optional[str] = None  # 포트폴리오 전략은 None
    interval: str = "1d"
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10_000_000
```

**파일**: `api/routes/backtest.py`
- symbol이 있으면 단일 종목 모드
- symbol이 없으면 포트폴리오 모드

### Phase 4: 포지션 관리자 확장 ✅

**파일**: `core/backtest/position.py`

```python
class PositionManager:
    def get_portfolio_weights(self, total_equity) -> Dict[str, float]:
        """현재 포트폴리오 비중"""
        
    def calculate_rebalance_orders(self, target_weights, current_prices, total_equity) -> Dict[str, int]:
        """리밸런싱 주문 계산"""
        # 양수: 매수, 음수: 매도
```

### Phase 5: 데이터 로더 개선 ✅

**파일**: `data/repository.py`

```python
class DataRepository:
    def get_market_snapshot(self, date, symbols=None) -> pd.DataFrame:
        """시장 스냅샷 (종목 선택용)"""
        # PER, PBR, ROE, 거래대금 등
    
    def get_multi_ohlc(self, symbols, interval, start_date, end_date) -> Dict[str, pd.DataFrame]:
        """여러 종목 배치 로딩"""
```

## 사용 방법

### 1. 포트폴리오 전략 작성

```python
from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy

@strategy(name="MyPortfolioStrategy", version="1.0.0")
class MyPortfolioStrategy(BaseStrategy):
    def select_universe(self, date, market_data):
        # 종목 선택 로직
        filtered = market_data[
            (market_data['per'] < 10) &
            (market_data['pbr'] < 1.0)
        ]
        return filtered.nlargest(20, 'volume_amount').index.tolist()
    
    def get_target_weights(self, universe, market_data, account):
        # 비중 계산 (기본: 균등 분배)
        return super().get_target_weights(universe, market_data, account)
    
    def on_bar(self, bars, positions, account):
        # 포트폴리오 전략은 비워둠 (엔진이 리밸런싱 처리)
        return []
    
    def on_fill(self, order, position):
        pass
```

### 2. 백테스트 실행

```python
from core.backtest.engine import BacktestEngine
from datetime import datetime

# 전략 생성
strategy = MyPortfolioStrategy(params={
    "per_max": 10.0,
    "pbr_max": 1.0,
    "max_stocks": 20
})

# 엔진 생성
engine = BacktestEngine(
    strategy=strategy,
    initial_capital=10_000_000,
    commission=0.00015
)

# 실행 (symbol 없음 → 자동으로 포트폴리오 모드)
result = await engine.run(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

print(f"수익률: {result.total_return:.2%}")
print(f"MDD: {result.mdd:.2%}")
print(f"거래 수: {result.total_trades}")
```

### 3. API 호출

```bash
# 포트폴리오 백테스트
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ValuePortfolioStrategy",
    "parameters": {
      "per_max": 10.0,
      "pbr_max": 1.0,
      "max_stocks": 20
    },
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T00:00:00",
    "initial_capital": 10000000
  }'
```

## 하위 호환성

기존 단일 종목 전략도 그대로 동작:

```python
# 기존 전략 (select_universe 구현 안함)
class MACrossStrategy(BaseStrategy):
    def on_bar(self, bars, positions, account):
        # 기존 로직
        pass

# symbol 있으면 → 단일 종목 모드
result = await engine.run(
    ohlc_data=ohlc_list,
    start_date=start,
    end_date=end
)
```

## 테스트

```bash
# 포트폴리오 백테스트 테스트
python scripts/test_portfolio_backtest.py
```

## 다음 단계 (선택사항)

1. **성능 최적화**
   - 데이터 캐싱
   - 병렬 처리
   - 메모리 최적화

2. **고급 기능**
   - 동적 리밸런싱 주기
   - 거래 비용 최적화
   - 슬리피지 모델 개선

3. **프론트엔드**
   - 포트폴리오 백테스트 UI
   - 종목 선택 시각화
   - 리밸런싱 이력 차트

4. **실시간 트레이딩**
   - 포트폴리오 전략 실전 적용
   - 자동 리밸런싱
   - 리스크 관리

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                    Portfolio Strategy                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐│
│  │select_universe │  │get_target_     │  │  on_bar    ││
│  │                │  │   weights      │  │  (empty)   ││
│  └────────────────┘  └────────────────┘  └────────────┘│
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Backtest Engine                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │  run_portfolio()                                   │ │
│  │    ├─ load_market_snapshot()                       │ │
│  │    ├─ strategy.select_universe()                   │ │
│  │    ├─ strategy.get_target_weights()                │ │
│  │    └─ rebalance_portfolio()                        │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────┐   ┌──────────────────────┐
│  Position Manager    │   │  Data Repository     │
│  ├─ get_portfolio_   │   │  ├─ get_market_      │
│  │    weights()      │   │  │    snapshot()     │
│  └─ calculate_       │   │  └─ get_multi_ohlc() │
│      rebalance_      │   │                      │
│      orders()        │   │                      │
└──────────────────────┘   └──────────────────────┘
```

## 설계 원칙 준수

✅ **느슨한 결합**: 전략 ↔ 엔진 ↔ 데이터 계층 분리
✅ **DIP**: 전략은 추상 인터페이스에 의존
✅ **ISP**: 단일 종목/포트폴리오 전략 분리
✅ **하위 호환**: 기존 전략 그대로 동작
✅ **확장 가능**: 새로운 전략 타입 추가 용이
