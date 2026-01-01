/**
 * 수익 대시보드 컴포넌트
 */
import { useEffect, useState } from 'react';
import { getDashboardSummary, DashboardSummary } from '../services/dashboardApi';
import { formatCurrency, formatPercent } from '../../../utils/formatters';
import { LoadingSpinner } from '../../../components/UI/LoadingSpinner';
import { ErrorMessage } from '../../../components/UI/ErrorMessage';
import './ProfitDashboard.css';

export const ProfitDashboard = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    // 30초마다 자동 갱신
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const summary = await getDashboardSummary();
      setData(summary);
    } catch (err: any) {
      setError(err.message || '대시보드 데이터를 불러오는데 실패했습니다.');
      console.error('Dashboard load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !data) {
    return (
      <div className="profit-dashboard">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="profit-dashboard">
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { profit, strategies, recent_trades } = data;

  return (
    <div className="profit-dashboard">
      <div className="profit-dashboard-header">
        <h2>수익 대시보드</h2>
        <button onClick={loadData} className="refresh-button" disabled={isLoading}>
          {isLoading ? '갱신 중...' : '새로고침'}
        </button>
      </div>

      {/* 수익 요약 카드 */}
      <div className="profit-summary-cards">
        <div className="profit-card">
          <div className="profit-card-label">오늘 수익률</div>
          <div className={`profit-card-value ${profit.today_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(profit.today_return)}
          </div>
        </div>
        <div className="profit-card">
          <div className="profit-card-label">이번 주 수익률</div>
          <div className={`profit-card-value ${profit.week_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(profit.week_return)}
          </div>
        </div>
        <div className="profit-card">
          <div className="profit-card-label">이번 달 수익률</div>
          <div className={`profit-card-value ${profit.month_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(profit.month_return)}
          </div>
        </div>
        <div className="profit-card">
          <div className="profit-card-label">총 수익률</div>
          <div className={`profit-card-value ${profit.total_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(profit.total_return)}
          </div>
        </div>
        <div className="profit-card">
          <div className="profit-card-label">현재 자산</div>
          <div className="profit-card-value">
            {formatCurrency(profit.current_equity)}
          </div>
        </div>
        <div className="profit-card">
          <div className="profit-card-label">초기 자본</div>
          <div className="profit-card-value">
            {formatCurrency(profit.initial_capital)}
          </div>
        </div>
      </div>

      {/* 전략별 성과 */}
      {strategies.length > 0 && (
        <div className="strategy-performance-section">
          <h3>전략별 성과</h3>
          <div className="strategy-list">
            {strategies.map((strategy) => (
              <div key={strategy.strategy_id} className="strategy-card">
                <div className="strategy-header">
                  <span className="strategy-name">{strategy.strategy_name}</span>
                  <span className={`strategy-status ${strategy.is_active ? 'active' : 'inactive'}`}>
                    {strategy.is_active ? '실행 중' : '중지됨'}
                  </span>
                </div>
                <div className="strategy-metrics">
                  <div className="metric">
                    <span className="metric-label">수익률:</span>
                    <span className={`metric-value ${strategy.total_return >= 0 ? 'positive' : 'negative'}`}>
                      {formatPercent(strategy.total_return)}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">거래 횟수:</span>
                    <span className="metric-value">{strategy.total_trades}회</span>
                  </div>
                  {strategy.win_rate !== null && (
                    <div className="metric">
                      <span className="metric-label">승률:</span>
                      <span className="metric-value">{formatPercent(strategy.win_rate)}</span>
                    </div>
                  )}
                  <div className="metric">
                    <span className="metric-label">현재 자산:</span>
                    <span className="metric-value">{formatCurrency(strategy.current_equity)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 최근 거래 내역 */}
      {recent_trades.length > 0 && (
        <div className="recent-trades-section">
          <h3>오늘 거래 내역</h3>
          <table className="trades-table">
            <thead>
              <tr>
                <th>시간</th>
                <th>종목</th>
                <th>매수/매도</th>
                <th>수량</th>
                <th>가격</th>
              </tr>
            </thead>
            <tbody>
              {recent_trades.map((trade) => (
                <tr key={trade.trade_id}>
                  <td>{new Date(trade.timestamp).toLocaleTimeString()}</td>
                  <td>{trade.symbol}</td>
                  <td className={trade.side === 'buy' ? 'buy' : 'sell'}>
                    {trade.side === 'buy' ? '매수' : '매도'}
                  </td>
                  <td>{trade.quantity}주</td>
                  <td>{formatCurrency(trade.price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {strategies.length === 0 && recent_trades.length === 0 && (
        <div className="empty-state">
          <p>실행 중인 전략이 없습니다.</p>
        </div>
      )}
    </div>
  );
};

