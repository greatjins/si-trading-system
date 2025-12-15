import React from 'react';
import './BacktestWarning.css';

interface BacktestWarningProps {
  mdd: number;
  totalTrades: number;
  createdAt: string;
}

const BacktestWarning: React.FC<BacktestWarningProps> = ({ mdd, totalTrades, createdAt }) => {
  // 2024년 12월 14일 이전 결과이고 MDD > 50% 또는 거래 수 = 0인 경우
  const cutoffDate = new Date('2024-12-14');
  const resultDate = new Date(createdAt);
  
  const isOldResult = resultDate < cutoffDate;
  const hasHighMDD = mdd > 0.5; // 50% 이상
  const hasNoTrades = totalTrades === 0;
  
  if (!isOldResult || (!hasHighMDD && !hasNoTrades)) {
    return null;
  }
  
  return (
    <div className="backtest-warning">
      <div className="warning-icon">⚠️</div>
      <div className="warning-content">
        <h4>백테스트 결과 주의사항</h4>
        <p>
          이 결과는 시스템 개선 이전({cutoffDate.toLocaleDateString()})에 생성된 것으로, 
          {hasHighMDD && ' MDD 계산에 오류가 있을 수 있습니다.'}
          {hasNoTrades && ' 거래 실행에 문제가 있었을 수 있습니다.'}
        </p>
        <p className="warning-suggestion">
          정확한 결과를 위해 <strong>새로운 백테스트를 실행</strong>해 주세요.
        </p>
      </div>
    </div>
  );
};

export default BacktestWarning;