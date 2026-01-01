/**
 * 비교 결과 UI 컴포넌트
 */
import { useEffect, useState } from 'react';
import {
  getComparisons,
  getComparison,
  ComparisonResponse
} from '../services/analysisApi';
import { formatPercent } from '../../../utils/formatters';
import { LoadingSpinner } from '../../../components/UI/LoadingSpinner';
import { ErrorMessage } from '../../../components/UI/ErrorMessage';
import { EquityCurveChart } from '../../../components/Charts/EquityCurveChart';
import './ComparisonView.css';

interface ComparisonViewProps {
  comparisonId?: number;
  strategyId?: number;
}

export const ComparisonView = ({ comparisonId, strategyId }: ComparisonViewProps) => {
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [comparisons, setComparisons] = useState<ComparisonResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (comparisonId) {
      loadComparison(comparisonId);
    } else {
      loadComparisons();
    }
  }, [comparisonId, strategyId]);

  const loadComparison = async (id: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getComparison(id);
      setComparison(data);
    } catch (err: any) {
      setError(err.message || '비교 결과를 불러오는데 실패했습니다.');
      console.error('Comparison load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadComparisons = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getComparisons(strategyId);
      setComparisons(data);
      if (data.length > 0 && !comparisonId) {
        setComparison(data[0]);
      }
    } catch (err: any) {
      setError(err.message || '비교 결과 목록을 불러오는데 실패했습니다.');
      console.error('Comparisons load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !comparison) {
    return (
      <div className="comparison-view">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !comparison) {
    return (
      <div className="comparison-view">
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className="comparison-view">
        <div className="empty-state">
          <p>비교 결과가 없습니다.</p>
        </div>
      </div>
    );
  }

  const causeContributions = [
    { name: '슬리피지', value: comparison.slippage_contribution, color: '#ffc107' },
    { name: '수수료', value: comparison.commission_contribution, color: '#17a2b8' },
    { name: '체결 지연', value: comparison.delay_contribution, color: '#6f42c1' },
    { name: '유동성', value: comparison.liquidity_contribution, color: '#e83e8c' },
    { name: '시장 변화', value: comparison.market_change_contribution, color: '#6c757d' }
  ].filter(item => item.value !== null && item.value !== undefined);

  const totalContribution = causeContributions.reduce((sum, item) => sum + (item.value || 0), 0);

  return (
    <div className="comparison-view">
      <div className="comparison-header">
        <h2>백테스트 vs 실전 비교</h2>
        <button onClick={() => loadComparisons()} className="refresh-button">
          새로고침
        </button>
      </div>

      {/* 비교 결과 요약 */}
      <div className="comparison-summary">
        <div className="comparison-card">
          <div className="comparison-card-label">백테스트 수익률</div>
          <div className={`comparison-card-value ${comparison.backtest_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(comparison.backtest_return)}
          </div>
        </div>
        <div className="comparison-card">
          <div className="comparison-card-label">실전 수익률</div>
          <div className={`comparison-card-value ${comparison.live_return >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(comparison.live_return)}
          </div>
        </div>
        <div className="comparison-card">
          <div className="comparison-card-label">차이</div>
          <div className={`comparison-card-value ${comparison.return_difference >= 0 ? 'positive' : 'negative'}`}>
            {formatPercent(comparison.return_difference)}
          </div>
        </div>
        <div className="comparison-card">
          <div className="comparison-card-label">거래 횟수 차이</div>
          <div className="comparison-card-value">
            {comparison.trade_difference > 0 ? '+' : ''}{comparison.trade_difference}회
          </div>
        </div>
      </div>

      {/* 차이 원인 분석 */}
      {causeContributions.length > 0 && (
        <div className="cause-analysis-section">
          <h3>차이 원인 분석</h3>
          <div className="cause-chart">
            {causeContributions.map((item, index) => {
              const percentage = totalContribution > 0 ? (item.value || 0) / totalContribution * 100 : 0;
              return (
                <div key={index} className="cause-item">
                  <div className="cause-header">
                    <span className="cause-name">{item.name}</span>
                    <span className="cause-percentage">{percentage.toFixed(1)}%</span>
                  </div>
                  <div className="cause-bar-container">
                    <div
                      className="cause-bar"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: item.color
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 상세 정보 */}
      <div className="comparison-details">
        <div className="detail-section">
          <h4>백테스트 정보</h4>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">거래 횟수:</span>
              <span className="detail-value">{comparison.backtest_trades}회</span>
            </div>
          </div>
        </div>
        <div className="detail-section">
          <h4>실전 정보</h4>
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">거래 횟수:</span>
              <span className="detail-value">{comparison.live_trades}회</span>
            </div>
          </div>
        </div>
      </div>

      {/* 비교 결과 목록 (여러 개인 경우) */}
      {comparisons.length > 1 && (
        <div className="comparison-list-section">
          <h3>다른 비교 결과</h3>
          <div className="comparison-list">
            {comparisons
              .filter(c => c.id !== comparison.id)
              .slice(0, 5)
              .map((c) => (
                <div
                  key={c.id}
                  className="comparison-list-item"
                  onClick={() => loadComparison(c.id)}
                >
                  <div className="list-item-header">
                    <span>비교 #{c.id}</span>
                    <span className={`list-item-diff ${c.return_difference >= 0 ? 'positive' : 'negative'}`}>
                      {formatPercent(c.return_difference)}
                    </span>
                  </div>
                  <div className="list-item-details">
                    백테스트: {formatPercent(c.backtest_return)} | 실전: {formatPercent(c.live_return)}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

