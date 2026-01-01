/**
 * 전략 실행 상태 컴포넌트
 */
import { useEffect, useState } from 'react';
import { getStrategyStatus, StrategyStatus } from '../services/strategyApi';
import { LoadingSpinner } from '../../../components/UI/LoadingSpinner';
import { ErrorMessage } from '../../../components/UI/ErrorMessage';
import './StrategyStatus.css';

interface StrategyStatusProps {
  strategyId: number;
  onStart?: () => void;
  onStop?: () => void;
}

export const StrategyStatusComponent = ({ strategyId, onStart, onStop }: StrategyStatusProps) => {
  const [status, setStatus] = useState<StrategyStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();
    // 10초마다 자동 갱신
    const interval = setInterval(loadStatus, 10000);
    return () => clearInterval(interval);
  }, [strategyId]);

  const loadStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getStrategyStatus(strategyId);
      setStatus(data);
    } catch (err: any) {
      setError(err.message || '상태를 불러오는데 실패했습니다.');
      console.error('Strategy status load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !status) {
    return (
      <div className="strategy-status">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="strategy-status">
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!status) {
    return null;
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'running':
        return '#28a745';
      case 'error':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'running':
        return '실행 중';
      case 'error':
        return '에러';
      default:
        return '중지됨';
    }
  };

  return (
    <div className="strategy-status">
      <div className="strategy-status-header">
        <h3>실행 상태</h3>
        <button onClick={loadStatus} className="refresh-button" disabled={isLoading}>
          {isLoading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      <div className="status-card">
        <div className="status-indicator">
          <span
            className="status-dot"
            style={{ backgroundColor: getStatusColor() }}
          />
          <span className="status-text">{getStatusText()}</span>
        </div>

        <div className="status-details">
          {status.last_execution_time && (
            <div className="status-detail">
              <span className="detail-label">마지막 실행:</span>
              <span className="detail-value">
                {new Date(status.last_execution_time).toLocaleString()}
              </span>
            </div>
          )}

          {status.next_execution_time && (
            <div className="status-detail">
              <span className="detail-label">다음 실행 예정:</span>
              <span className="detail-value">
                {new Date(status.next_execution_time).toLocaleString()}
              </span>
            </div>
          )}

          {status.error_count > 0 && (
            <div className="status-detail error">
              <span className="detail-label">에러 횟수:</span>
              <span className="detail-value">{status.error_count}회</span>
            </div>
          )}

          {status.last_error && (
            <div className="status-detail error">
              <span className="detail-label">마지막 에러:</span>
              <span className="detail-value">{status.last_error}</span>
            </div>
          )}
        </div>

        <div className="status-actions">
          {status.is_running ? (
            <button onClick={onStop} className="stop-button">
              중지
            </button>
          ) : (
            <button onClick={onStart} className="start-button">
              시작
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

