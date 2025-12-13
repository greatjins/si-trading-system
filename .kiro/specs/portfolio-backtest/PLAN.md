# 포트폴리오 백테스트 구현 계획

## 목표

전략이 매일 종목을 선택하고, 여러 종목을 동시에 매매할 수 있는 포트폴리오 백테스트 시스템 구축

## 현재 상태

```python
# 현재: 단일 종목만 지원
백테스트(symbol="005930") → 삼성전자만 매매
```

## 목표 상태

```python
# 목표: 전략이 종목 선택
백테스트() → 전략이 매일 종목 선택 → 여러 종목 매매
```

## 구현 단계

### Phase 1: 전략 인터페이스 확장 (1-2일)

**변경 파일**: `core/strategy/base.py`

```python
class BaseStrategy:
    # 기존
    def on_bar(self, bars, positions, account) -> List[OrderSignal]:
        pass
    
    # 추가
    def select_universe(self, date, market_data) -> List[str]:
        """매일 거래할 종목 리스트 반환"""
        return []  # 기본: 빈 리스트 (하위 호환)
    
    def get_target_weights(self, universe, market_data) -> Dict[str, float]:
        """각 종목의 목표 비중 반환"""
        return {}  # 기본: 균등 분배
```

**예시**:
```python
class ValueStrategy(BaseStrategy):
    def select_universe(self, date, market_data):
        # PER < 10, PBR < 1 종목 선택
        return ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    def get_target_weights(self, universe, market_data):
        # 균등 분배
        return {symbol: 1.0/len(universe) for symbol in universe}
```

### Phase 2: 백테스트 엔진 확장 (2-3일)

**변경 파일**: `core/backtest/engine.py`

```python
class BacktestEngine:
    async def run(self, start_date, end_date):
        # 기존: 단일 종목 OHLC 받음
        # 변경: 날짜 범위만 받음
        
        for date in trading_days:
            # 1. 전략이 종목 선택
            universe = strategy.select_universe(date, market_data)
            
            # 2. 각 종목 데이터 로드
            for symbol in universe:
                bars = load_data(symbol, date)
                
                # 3. 매매 신호 생성
                signals = strategy.on_bar(bars, positions, account)
                
                # 4. 신호 처리
                process_signals(signals)
            
            # 5. 리밸런싱 (필요시)
            rebalance_portfolio()
```

### Phase 3: 데이터 로더 개선 (1일)

**변경 파일**: `data/repository.py`

```python
class DataRepository:
    def get_multi_ohlc(self, symbols: List[str], date: datetime) -> Dict[str, pd.DataFrame]:
        """여러 종목 데이터를 한번에 로드 (배치)"""
        pass
    
    def get_market_snapshot(self, date: datetime) -> pd.DataFrame:
        """특정 날짜의 전체 시장 스냅샷 (종목 선택용)"""
        # 모든 종목의 PER, PBR, 거래대금 등
        pass
```

### Phase 4: 포지션 관리자 확장 (1일)

**변경 파일**: `core/backtest/position.py`

```python
class PositionManager:
    def rebalance(self, target_weights: Dict[str, float], current_prices: Dict[str, float]):
        """목표 비중에 맞춰 포트폴리오 재조정"""
        # 현재 비중 계산
        # 목표 비중과 비교
        # 매수/매도 신호 생성
        pass
```

### Phase 5: API 수정 (1일)

**변경 파일**: `api/routes/backtest.py`, `api/schemas.py`

```python
# 기존
class BacktestRequest:
    symbol: str  # 삭제
    strategy_name: str
    start_date: datetime
    end_date: datetime

# 변경
class BacktestRequest:
    strategy_name: str
    start_date: datetime
    end_date: datetime
    # symbol 제거 - 전략이 알아서 선택
```

## 구현 순서

1. **Day 1-2**: Phase 1 (전략 인터페이스)
   - `BaseStrategy`에 메서드 추가
   - 예제 전략 작성 (ValueStrategy)
   - 단위 테스트

2. **Day 3-5**: Phase 2 (백테스트 엔진)
   - 멀티 심볼 지원
   - 리밸런싱 로직
   - 통합 테스트

3. **Day 6**: Phase 3 (데이터 로더)
   - 배치 로딩
   - 시장 스냅샷
   - 캐싱

4. **Day 7**: Phase 4 (포지션 관리)
   - 리밸런싱 함수
   - 비중 계산

5. **Day 8**: Phase 5 (API)
   - 스키마 수정
   - 엔드포인트 수정
   - 프론트엔드 연동

## 하위 호환성

기존 단일 종목 전략도 계속 동작하도록:

```python
# 기존 전략 (단일 종목)
class MACrossStrategy(BaseStrategy):
    def on_bar(self, bars, positions, account):
        # select_universe 구현 안함
        pass

# 백테스트 엔진이 자동 감지
if strategy.select_universe() == []:
    # 단일 종목 모드 (기존 방식)
    run_single_symbol_backtest(symbol)
else:
    # 포트폴리오 모드 (신규 방식)
    run_portfolio_backtest()
```

## 예상 결과

```python
# 사용 예시
strategy = ValueStrategy(params={
    "per_max": 10,
    "pbr_max": 1.0,
    "max_stocks": 20
})

result = await backtest_engine.run(
    strategy=strategy,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(f"총 수익률: {result.total_return:.2%}")
print(f"보유 종목 수: {len(result.positions)}")
print(f"리밸런싱 횟수: {result.rebalance_count}")
```

## 다음 단계

1. 요구사항 검토 및 승인
2. 설계 문서 작성 (design.md)
3. 태스크 리스트 작성 (tasks.md)
4. 구현 시작
