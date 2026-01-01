/**
 * 전략 API 서비스
 */
import { httpClient } from '../../../services/http';

export interface StrategyStatus {
  strategy_id: number;
  is_running: boolean;
  last_execution_time: string | null;
  next_execution_time: string | null;
  error_count: number;
  last_error: string | null;
  status: string; // "running", "stopped", "error"
}

/**
 * 전략 실행 상태 조회
 */
export const getStrategyStatus = async (strategyId: number): Promise<StrategyStatus> => {
  const response = await httpClient.get<StrategyStatus>(`/api/strategies/${strategyId}/status`);
  return response.data;
};

