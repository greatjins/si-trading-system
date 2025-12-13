# Design Document

## Overview

백테스트 결과를 시각적으로 분석할 수 있는 기능을 제공합니다. 포트폴리오 백테스트에서 거래된 각 종목의 성과를 리스트로 표시하고, 종목을 클릭하면 가격 차트와 매매 시점을 함께 볼 수 있습니다.

**핵심 기능:**
- 종목별 성과 리스트 (수익률, 거래 횟수, 승률)
- 가격 차트 + 매매 시점 마커
- 거래 내역 테이블
- 전체 자산 곡선
- 백테스트 비교 기능

## Architecture

### 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│  BacktestResultPage                                          │
│  ├─ EquityCurveChart (전체 자산 곡선)                        │
│  ├─ SymbolPerformanceList (종목별 성과 리스트)               │
│  └─ SymbolDetailModal                                        │
│      ├─ PriceChart (가격 차트 + 매매 마커)                   │
│      └─ TradeHistoryTable (거래 내역)                        │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  /api/backtest/results/{backtest_id}                         │
│  /api/backtest/results/{backtest_id}/symbols                 │
│  /api/backtest/results/{backtest_id}/symbols/{symbol}        │
│  /api/backtest/results/{backtest_id}/ohlc/{symbol}           │
│  /api/backtest/results/compare                               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
├─────────────────────────────────────────────────────────────┤
│  BacktestRepository (백테스트 결과 저장/조회)                │
│  DataRepository (OHLC 데이터 조회)                           │
│  TradeAnalyzer (거래 분석 및 메트릭 계산)                    │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **백테스트 실행 → 결과 저장**
   - BacktestEngine이 거래 실행
   - 종목별로 Trade 객체 생성
   - BacktestRepository가 DB에 저장

2. **결과 조회 → 분석**
   - Frontend가 backtest_id로 결과 요청
   - TradeAnalyzer가 종목별 메트릭 계산
   - 종목 리스트 반환

3. **종목 상세 → 차트 렌더링**
   - Frontend가 특정 종목 상세 요청
   - DataRepository에서 OHLC 데이터 조회
   - 거래 시점과 함께 반환

## Components and Interfaces

### Backend Components

#### 1. TradeAnalyzer (신규)

```python
class TradeAnalyzer:
    """거래 분석 및 메트릭 계산"""
    
    @staticmethod
    def group_trades_by_symbol(trades: List[Trade]) -> Dict[str, List[Trade]]:
        """종목별로 거래 그룹화"""
        pass
    
    @staticmethod
    def calculate_symbol_metrics(trades: List[Trade]) -> SymbolMetrics:
        """종목별 성과 메트릭 계산"""
        # - total_return: 총 수익률
        # - win_rate: 승률
        # - trade_count: 거래 횟수
        # - avg_holding_period: 평균 보유 기간
        # - profit_factor: 손익비
        pass
    
    @staticmethod
    def match_entry_exit(trades: List[Trade]) -> List[CompletedTrade]:
        """매수/매도 거래를 매칭하여 완결된 거래 생성"""
        pass
```

#### 2. API Endpoints (신규)

```python
# api/routes/backtest_results.py

@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: int) -> BacktestResultDetail:
    """백테스트 전체 결과 조회"""
    pass

@router.get("/results/{backtest_id}/symbols")
async def get_symbol_performance(backtest_id: int) -> List[SymbolPerformance]:
    """종목별 성과 리스트"""
    pass

@router.get("/results/{backtest_id}/symbols/{symbol}")
async def get_symbol_detail(backtest_id: int, symbol: str) -> SymbolDetail:
    """특정 종목 상세 정보 (거래 내역 포함)"""
    pass

@router.get("/results/{backtest_id}/ohlc/{symbol}")
async def get_symbol_ohlc(
    backtest_id: int, 
    symbol: str
) -> List[OHLC]:
    """특정 종목의 OHLC 데이터 (백테스트 기간)"""
    pass

@router.post("/results/compare")
async def compare_backtests(
    backtest_ids: List[int]
) -> BacktestComparison:
    """여러 백테스트 결과 비교"""
    pass
```

### Frontend Components

#### 1. BacktestResultPage (신규)

```typescript
interface BacktestResultPageProps {
  backtestId: number;
}

const BacktestResultPage: React.FC<BacktestResultPageProps> = ({ backtestId }) => {
  // 백테스트 결과 로드
  // 자산 곡선 표시
  // 종목 리스트 표시
  // 종목 클릭 시 상세 모달 열기
}
```

#### 2. EquityCurveChart (신규)

```typescript
interface EquityCurveChartProps {
  equityCurve: number[];
  timestamps: string[];
  mdd: number;
  mddPeriod: { start: string; end: string };
}

const EquityCurveChart: React.FC<EquityCurveChartProps> = (props) => {
  // Recharts 또는 Chart.js로 라인 차트 렌더링
  // MDD 구간 하이라이트
  // 호버 시 날짜/금액 표시
}
```

#### 3. SymbolPerformanceList (신규)

```typescript
interface SymbolPerformance {
  symbol: string;
  name: string;
  totalReturn: number;
  tradeCount: number;
  winRate: number;
  profitFactor: number;
}

interface SymbolPerformanceListProps {
  symbols: SymbolPerformance[];
  onSymbolClick: (symbol: string) => void;
}

const SymbolPerformanceList: React.FC<SymbolPerformanceListProps> = (props) => {
  // 종목 리스트 테이블
  // 정렬 기능 (수익률, 거래 횟수, 승률)
  // 클릭 시 onSymbolClick 호출
}
```

#### 4. SymbolDetailModal (신규)

```typescript
interface SymbolDetailModalProps {
  symbol: string;
  backtestId: number;
  onClose: () => void;
}

const SymbolDetailModal: React.FC<SymbolDetailModalProps> = (props) => {
  // 모달 레이아웃
  // PriceChart 렌더링
  // TradeHistoryTable 렌더링
}
```

#### 5. PriceChart (신규)

```typescript
interface TradeMarker {
  timestamp: string;
  price: number;
  side: 'buy' | 'sell';
  quantity: number;
  pnl?: number;
}

interface PriceChartProps {
  ohlcData: OHLC[];
  trades: TradeMarker[];
}

const PriceChart: React.FC<PriceChartProps> = (props) => {
  // Lightweight Charts 또는 TradingView 라이브러리 사용
  // 캔들스틱 차트
  // 매수 마커 (↑ 녹색)
  // 매도 마커 (↓ 빨간색)
  // 호버 시 거래 상세 툴팁
}
```

#### 6. TradeHistoryTable (신규)

```typescript
interface CompletedTrade {
  entryDate: string;
  entryPrice: number;
  exitDate: string;
  exitPrice: number;
  quantity: number;
  return: number;
  holdingPeriod: number; // days
}

interface TradeHistoryTableProps {
  trades: CompletedTrade[];
  onTradeClick: (trade: CompletedTrade) => void;
}

const TradeHistoryTable: React.FC<TradeHistoryTableProps> = (props) => {
  // 거래 내역 테이블
  // 수익/손실 색상 구분
  // 클릭 시 차트에 하이라이트
}
```

## Data Models

### Backend Models

#### SymbolPerformance

```python
@dataclass
class SymbolPerformance:
    """종목별 성과"""
    symbol: str
    name: str
    total_return: float  # 총 수익률 (%)
    trade_count: int  # 거래 횟수
    win_rate: float  # 승률 (%)
    profit_factor: float  # 손익비
    avg_holding_period: int  # 평균 보유 기간 (일)
    total_pnl: float  # 총 손익 (원)
```

#### CompletedTrade

```python
@dataclass
class CompletedTrade:
    """완결된 거래 (매수 → 매도)"""
    symbol: str
    entry_date: datetime
    entry_price: float
    entry_quantity: int
    exit_date: datetime
    exit_price: float
    exit_quantity: int
    pnl: float  # 손익 (원)
    return_pct: float  # 수익률 (%)
    holding_period: int  # 보유 기간 (일)
    commission: float  # 수수료
```

#### SymbolDetail

```python
@dataclass
class SymbolDetail:
    """종목 상세 정보"""
    symbol: str
    name: str
    metrics: SymbolPerformance
    completed_trades: List[CompletedTrade]
    all_trades: List[Trade]  # 원본 거래 기록
```

#### BacktestResultDetail

```python
@dataclass
class BacktestResultDetail:
    """백테스트 결과 상세"""
    backtest_id: int
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_equity: float
    total_return: float
    mdd: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    equity_curve: List[float]
    equity_timestamps: List[datetime]
    symbol_performances: List[SymbolPerformance]
```

### Frontend Models

```typescript
// types/backtest.ts

export interface SymbolPerformance {
  symbol: string;
  name: string;
  totalReturn: number;
  tradeCount: number;
  winRate: number;
  profitFactor: number;
  avgHoldingPeriod: number;
  totalPnl: number;
}

export interface CompletedTrade {
  symbol: string;
  entryDate: string;
  entryPrice: number;
  entryQuantity: number;
  exitDate: string;
  exitPrice: number;
  exitQuantity: number;
  pnl: number;
  returnPct: number;
  holdingPeriod: number;
  commission: number;
}

export interface SymbolDetail {
  symbol: string;
  name: string;
  metrics: SymbolPerformance;
  completedTrades: CompletedTrade[];
}

export interface OHLC {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestResultDetail {
  backtestId: number;
  strategyName: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalEquity: number;
  totalReturn: number;
  mdd: number;
  sharpeRatio: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  equityCurve: number[];
  equityTimestamps: string[];
  symbolPerformances: SymbolPerformance[];
}
```

## Error Handling

### Backend

```python
# 백테스트 결과 없음
if not backtest_result:
    raise HTTPException(
        status_code=404,
        detail=f"Backtest result {backtest_id} not found"
    )

# 종목 데이터 없음
if symbol not in traded_symbols:
    raise HTTPException(
        status_code=404,
        detail=f"Symbol {symbol} not found in backtest {backtest_id}"
    )

# OHLC 데이터 없음
if ohlc_data.empty:
    raise HTTPException(
        status_code=404,
        detail=f"No OHLC data for {symbol} in the backtest period"
    )
```

### Frontend

```typescript
// 데이터 로딩 실패
try {
  const result = await httpClient.get(`/api/backtest/results/${backtestId}`);
  setBacktestResult(result.data);
} catch (error) {
  setError('백테스트 결과를 불러올 수 없습니다.');
  console.error(error);
}

// 차트 렌더링 실패
if (!ohlcData || ohlcData.length === 0) {
  return <div>차트 데이터가 없습니다.</div>;
}
```

## Testing Strategy

### Unit Tests

1. **TradeAnalyzer 테스트**
   - `test_group_trades_by_symbol()`: 종목별 그룹화 검증
   - `test_calculate_symbol_metrics()`: 메트릭 계산 정확성
   - `test_match_entry_exit()`: 매수/매도 매칭 로직

2. **API Endpoint 테스트**
   - `test_get_backtest_result()`: 결과 조회
   - `test_get_symbol_performance()`: 종목 리스트 조회
   - `test_get_symbol_detail()`: 종목 상세 조회

### Integration Tests

1. **백테스트 실행 → 결과 조회 플로우**
   - 포트폴리오 백테스트 실행
   - 결과 저장 확인
   - API로 결과 조회
   - 종목별 데이터 검증

2. **Frontend 통합 테스트**
   - 백테스트 결과 페이지 렌더링
   - 종목 클릭 → 모달 열기
   - 차트 렌더링 확인

### Manual Tests

1. **UI/UX 테스트**
   - 차트 인터랙션 (줌, 팬, 호버)
   - 정렬/필터링 동작
   - 모달 열기/닫기

2. **성능 테스트**
   - 100개 종목 백테스트 결과 로딩 시간
   - 차트 렌더링 속도
   - 대량 거래 데이터 처리

## Implementation Notes

### 차트 라이브러리 선택

**옵션 1: Lightweight Charts (TradingView)**
- 장점: 금융 차트 전문, 성능 우수, 캔들스틱 기본 지원
- 단점: 커스터마이징 제한적

**옵션 2: Recharts**
- 장점: React 친화적, 커스터마이징 쉬움
- 단점: 캔들스틱 차트 직접 구현 필요

**옵션 3: Chart.js + react-chartjs-2**
- 장점: 범용적, 문서 풍부
- 단점: 금융 차트 플러그인 필요

**권장: Lightweight Charts** (금융 차트에 최적화)

### 데이터 저장 전략

**현재 구조:**
- `BacktestResult`에 `trades: List[Trade]` 저장
- 모든 거래가 하나의 리스트에 저장됨

**개선 방안:**
1. **종목별 인덱싱 추가**
   - DB에 `symbol` 컬럼 인덱스 생성
   - 종목별 조회 성능 향상

2. **완결된 거래 사전 계산**
   - 백테스트 완료 시 `CompletedTrade` 계산
   - 별도 테이블에 저장 (선택적)

3. **메트릭 캐싱**
   - 종목별 메트릭을 JSON으로 저장
   - API 응답 속도 향상

### 성능 최적화

1. **Lazy Loading**
   - 종목 리스트만 먼저 로드
   - 종목 클릭 시 상세 데이터 로드

2. **차트 데이터 샘플링**
   - 1000개 이상 캔들 → 다운샘플링
   - 줌 레벨에 따라 해상도 조정

3. **Frontend 캐싱**
   - React Query로 API 응답 캐싱
   - 동일한 종목 재클릭 시 즉시 표시

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Trade matching consistency
*For any* list of trades for a symbol, the number of completed trades should equal the minimum of buy trades and sell trades
**Validates: Requirements 3.1, 3.2**

### Property 2: Symbol metrics accuracy
*For any* symbol with completed trades, the total return should equal the sum of individual trade returns
**Validates: Requirements 1.2, 7.4**

### Property 3: Trade marker correspondence
*For any* displayed chart, every trade marker should correspond to an actual trade in the trade history
**Validates: Requirements 2.3, 2.4**

### Property 4: Equity curve monotonicity
*For any* backtest result, the equity curve timestamps should be in strictly increasing order
**Validates: Requirements 4.2, 4.4**

### Property 5: Symbol list completeness
*For any* backtest result, the symbol performance list should include all symbols that have at least one trade
**Validates: Requirements 1.1, 7.2**

### Property 6: Sort order correctness
*For any* sorted symbol list, consecutive elements should maintain the sort order based on the selected column
**Validates: Requirements 5.2, 5.3**

### Property 7: OHLC data period alignment
*For any* symbol OHLC request, all returned data points should fall within the backtest start and end dates
**Validates: Requirements 2.2, 7.5**

### Property 8: Win rate calculation
*For any* symbol with completed trades, the win rate should equal (profitable trades / total trades) * 100
**Validates: Requirements 1.2, 3.2**
