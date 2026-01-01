/**
 * 대시보드 API 서비스
 */
import { httpClient } from '../../../services/http';

export interface ProfitSummary {
  today_return: number;
  week_return: number;
  month_return: number;
  total_return: number;
  current_equity: number;
  initial_capital: number;
}

export interface StrategyPerformanceSummary {
  strategy_id: number;
  strategy_name: string;
  total_return: number;
  daily_return: number | null;
  total_trades: number;
  win_rate: number | null;
  current_equity: number;
  is_active: boolean;
}

export interface TradeSummary {
  trade_id: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  timestamp: string;
}

export interface DashboardSummary {
  profit: ProfitSummary;
  strategies: StrategyPerformanceSummary[];
  recent_trades: TradeSummary[];
}

/**
 * 대시보드 요약 정보 조회
 */
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await httpClient.get<DashboardSummary>('/api/dashboard/summary');
  return response.data;
};

/**
 * 전략별 성과 목록 조회
 */
export const getStrategyPerformances = async (): Promise<StrategyPerformanceSummary[]> => {
  const response = await httpClient.get<StrategyPerformanceSummary[]>('/api/dashboard/strategies');
  return response.data;
};

/**
 * 오늘 거래 내역 조회
 */
export const getTodayTrades = async (limit: number = 50): Promise<TradeSummary[]> => {
  const response = await httpClient.get<TradeSummary[]>(`/api/dashboard/trades?limit=${limit}`);
  return response.data;
};

