# 백테스트 시각화 API 엔드포인트

## 개요
백테스트 결과를 시각화하기 위한 API 엔드포인트들입니다. 종목별 성과 분석, 거래 내역 조회, 차트 데이터 제공 등의 기능을 제공합니다.

## 엔드포인트 목록

### 1. 백테스트 결과 상세 조회
**GET** `/api/backtest/results/{backtest_id}`

백테스트 결과의 상세 정보를 조회합니다.

#### 경로 매개변수
- `backtest_id` (integer): 백테스트 ID

#### 응답 예시
```json
{
  "backtest_id": 1,
  "strategy_name": "MovingAverageCrossover",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-12-31T23:59:59",
  "initial_capital": 10000000,
  "final_equity": 11500000,
  "total_return": 0.15,
  "mdd": 0.08,
  "sharpe_ratio": 1.25,
  "win_rate": 0.65,
  "profit_factor": 2.1,
  "total_trades": 45,
  "equity_curve": [10000000, 10150000, 10300000, ...],
  "equity_timestamps": ["2024-01-01T00:00:00", "2024-01-15T00:00:00", ...],
  "symbol_performances": [...]
}
```

#### 오류 응답
- `404 Not Found`: 백테스트 결과를 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

### 2. 종목별 성과 리스트 조회
**GET** `/api/backtest/results/{backtest_id}/symbols`

특정 백테스트의 종목별 성과 리스트를 조회합니다.

#### 경로 매개변수
- `backtest_id` (integer): 백테스트 ID

#### 응답 예시
```json
[
  {
    "symbol": "005930",
    "name": "삼성전자",
    "total_return": 12.5,
    "trade_count": 8,
    "win_rate": 75.0,
    "profit_factor": 2.8,
    "avg_holding_period": 15,
    "total_pnl": 1250000
  },
  {
    "symbol": "000660",
    "name": "SK하이닉스",
    "total_return": -3.2,
    "trade_count": 5,
    "win_rate": 40.0,
    "profit_factor": 0.8,
    "avg_holding_period": 12,
    "total_pnl": -320000
  }
]
```

---

### 3. 종목 상세 정보 조회
**GET** `/api/backtest/results/{backtest_id}/symbols/{symbol}`

특정 종목의 상세 거래 정보를 조회합니다.

#### 경로 매개변수
- `backtest_id` (integer): 백테스트 ID
- `symbol` (string): 종목 코드 (예: "005930")

#### 응답 예시
```json
{
  "symbol": "005930",
  "name": "삼성전자",
  "metrics": {
    "symbol": "005930",
    "name": "삼성전자",
    "total_return": 12.5,
    "trade_count": 8,
    "win_rate": 75.0,
    "profit_factor": 2.8,
    "avg_holding_period": 15,
    "total_pnl": 1250000
  },
  "completed_trades": [
    {
      "symbol": "005930",
      "entry_date": "2024-01-15T09:00:00",
      "entry_price": 75000,
      "entry_quantity": 100,
      "exit_date": "2024-01-30T15:30:00",
      "exit_price": 82000,
      "exit_quantity": 100,
      "pnl": 698000,
      "return_pct": 9.31,
      "holding_period": 15,
      "commission": 2000
    }
  ],
  "all_trades": [
    {
      "trade_id": "T001",
      "order_id": "O001",
      "symbol": "005930",
      "side": "buy",
      "quantity": 100,
      "price": 75000,
      "commission": 1000,
      "timestamp": "2024-01-15T09:00:00"
    }
  ],
  "total_return": 12.5,
  "trade_count": 8,
  "win_rate": 75.0,
  "profit_factor": 2.8,
  "total_pnl": 1250000,
  "avg_buy_price": 76500,
  "avg_sell_price": 84200,
  "avg_holding_days": 15
}
```

---

### 4. 종목 OHLC 데이터 조회
**GET** `/api/backtest/results/{backtest_id}/ohlc/{symbol}`

특정 종목의 백테스트 기간 OHLC 데이터를 조회합니다.

#### 경로 매개변수
- `backtest_id` (integer): 백테스트 ID
- `symbol` (string): 종목 코드

#### 응답 예시
```json
[
  {
    "timestamp": "2024-01-15T00:00:00",
    "open": 75000,
    "high": 76500,
    "low": 74200,
    "close": 75800,
    "volume": 1250000
  },
  {
    "timestamp": "2024-01-16T00:00:00",
    "open": 75800,
    "high": 77200,
    "low": 75500,
    "close": 76900,
    "volume": 980000
  }
]
```

---

### 5. 백테스트 비교
**POST** `/api/backtest/results/compare`

여러 백테스트 결과를 비교합니다.

#### 요청 본문
```json
[1, 2, 3]
```
백테스트 ID 배열

#### 응답 예시
```json
[
  {
    "backtest_id": 1,
    "strategy_name": "Strategy A",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "total_return": 0.15,
    "mdd": 0.08,
    "sharpe_ratio": 1.25,
    "win_rate": 0.65,
    "profit_factor": 2.1,
    "total_trades": 45,
    "equity_curve": [10000000, 10150000, ...],
    "is_best": true
  },
  {
    "backtest_id": 2,
    "strategy_name": "Strategy B",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "total_return": 0.12,
    "mdd": 0.06,
    "sharpe_ratio": 1.18,
    "win_rate": 0.58,
    "profit_factor": 1.8,
    "total_trades": 38,
    "equity_curve": [10000000, 10120000, ...],
    "is_best": false
  }
]
```

## 데이터 모델

### SymbolPerformance
종목별 성과 정보
```typescript
interface SymbolPerformance {
  symbol: string;           // 종목 코드
  name: string;            // 종목명
  total_return: number;    // 총 수익률 (%)
  trade_count: number;     // 거래 횟수
  win_rate: number;        // 승률 (%)
  profit_factor: number;   // 손익비
  avg_holding_period: number; // 평균 보유 기간 (일)
  total_pnl: number;       // 총 손익 (원)
}
```

### CompletedTrade
완결된 거래 정보
```typescript
interface CompletedTrade {
  symbol: string;
  entry_date: string;      // 진입 날짜
  entry_price: number;     // 진입 가격
  entry_quantity: number;  // 진입 수량
  exit_date: string;       // 청산 날짜
  exit_price: number;      // 청산 가격
  exit_quantity: number;   // 청산 수량
  pnl: number;            // 손익 (원)
  return_pct: number;     // 수익률 (%)
  holding_period: number; // 보유 기간 (일)
  commission: number;     // 수수료
}
```

### OHLC
OHLC 데이터
```typescript
interface OHLC {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

## 오류 처리

### 공통 오류 응답 형식
```json
{
  "detail": "Error message",
  "status_code": 404
}
```

### 주요 오류 코드
- `400 Bad Request`: 잘못된 요청 매개변수
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 요청 데이터 검증 실패
- `500 Internal Server Error`: 서버 내부 오류

## 사용 예시

### 1. 백테스트 결과 조회 및 시각화
```javascript
// 1. 백테스트 결과 상세 조회
const result = await fetch('/api/backtest/results/1');
const backtestData = await result.json();

// 2. 종목별 성과 조회
const symbolsResult = await fetch('/api/backtest/results/1/symbols');
const symbolPerformances = await symbolsResult.json();

// 3. 특정 종목 상세 조회
const symbolDetail = await fetch('/api/backtest/results/1/symbols/005930');
const detailData = await symbolDetail.json();
```

### 2. 백테스트 비교
```javascript
// 여러 백테스트 비교
const compareResult = await fetch('/api/backtest/results/compare', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify([1, 2, 3])
});
const comparisonData = await compareResult.json();
```

## 성능 고려사항
- 대용량 데이터 조회 시 페이지네이션 고려
- 캐싱을 통한 응답 속도 개선
- 데이터베이스 인덱스 최적화 필요