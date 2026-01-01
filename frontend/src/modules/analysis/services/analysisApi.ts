/**
 * 비교 분석 API 서비스
 */
import { httpClient } from '../../../services/http';

export interface ComparisonRequest {
  backtest_id: number;
  strategy_id: number;
  live_start: string;
  live_end: string;
}

export interface ComparisonResponse {
  id: number;
  backtest_id: number;
  strategy_id: number;
  backtest_return: number;
  live_return: number;
  return_difference: number;
  backtest_trades: number;
  live_trades: number;
  trade_difference: number;
  slippage_contribution: number | null;
  commission_contribution: number | null;
  delay_contribution: number | null;
  liquidity_contribution: number | null;
  market_change_contribution: number | null;
  created_at: string;
}

/**
 * 백테스트-실전 비교 실행
 */
export const createComparison = async (
  request: ComparisonRequest
): Promise<ComparisonResponse> => {
  const response = await httpClient.post<ComparisonResponse>('/api/analysis/compare', request);
  return response.data;
};

/**
 * 비교 결과 목록 조회
 */
export const getComparisons = async (
  strategyId?: number,
  limit: number = 50
): Promise<ComparisonResponse[]> => {
  const params = new URLSearchParams();
  if (strategyId) {
    params.append('strategy_id', strategyId.toString());
  }
  params.append('limit', limit.toString());
  
  const response = await httpClient.get<ComparisonResponse[]>(
    `/api/analysis/comparisons?${params.toString()}`
  );
  return response.data;
};

/**
 * 비교 결과 상세 조회
 */
export const getComparison = async (comparisonId: number): Promise<ComparisonResponse> => {
  const response = await httpClient.get<ComparisonResponse>(
    `/api/analysis/comparisons/${comparisonId}`
  );
  return response.data;
};

