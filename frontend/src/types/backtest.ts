/**
 * 백테스트 결과 관련 타입 정의
 */

export interface SymbolPerformance {
  symbol: string;
  name: string;
  total_return: number | null;
  trade_count: number | null;
  win_rate: number | null;
  profit_factor: number | null;
  avg_holding_period: number | null;
  total_pnl: number | null;
}

export interface CompletedTrade {
  symbol: string;
  entry_date: string;
  entry_price: number;
  entry_quantity: number;
  exit_date: string;
  exit_price: number;
  exit_quantity: number;
  pnl: number;
  return_pct: number;
  holding_period: number; // 백엔드와 일치 (일 단위)
  commission: number;
}

export interface TradeRecord {
  trade_id: string;
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission: number;
  timestamp: string;
}

export interface SymbolDetail {
  symbol: string;
  name: string;
  metrics: SymbolPerformance;
  completed_trades: CompletedTrade[];
  all_trades: TradeRecord[];
  // 편의를 위해 metrics의 필드들을 직접 노출
  total_return: number | null;
  trade_count: number | null;
  win_rate: number | null;
  profit_factor: number | null;
  total_pnl: number | null;
  avg_buy_price: number | null;
  avg_sell_price: number | null;
  avg_holding_days: number | null;
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
  backtest_id: number;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  total_return: number;
  mdd: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  equity_curve: number[];
  equity_timestamps: string[];
  symbol_performances: SymbolPerformance[];
}

export interface BacktestComparison {
  comparison: BacktestComparisonItem[];
  best_backtest_id: number;
}

export interface BacktestComparisonItem {
  backtest_id: number;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_return: number;
  mdd: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  equity_curve: number[];
  is_best?: boolean;
}

// 차트 관련 타입
export interface TradeMarker {
  timestamp: string;
  price: number;
  side: 'buy' | 'sell';
  quantity: number;
  pnl?: number;
}

export interface ChartData {
  ohlc: OHLC[];
  trades: TradeMarker[];
}

// UI 상태 관련 타입
export interface SortConfig {
  key: keyof SymbolPerformance;
  direction: 'asc' | 'desc';
}

export interface FilterConfig {
  minReturn?: number;
  maxReturn?: number;
  minTrades?: number;
  maxTrades?: number;
}

// API 응답 타입
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}