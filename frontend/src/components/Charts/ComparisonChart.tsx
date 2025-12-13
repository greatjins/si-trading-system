/**
 * 백테스트 비교 차트 컴포넌트
 */
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts';
import { BacktestComparisonItem } from '../../types/backtest';

interface ComparisonPoint {
  date: string;
  timestamp: string;
  [key: string]: string | number; // 각 백테스트의 자산 곡선
}

interface ComparisonChartProps {
  /** 비교할 백테스트 데이터 */
  comparisons: BacktestComparisonItem[];
  /** 차트 높이 */
  height?: number;
}

// 차트 색상 팔레트
const CHART_COLORS = [
  '#2196F3', // 파란색
  '#4CAF50', // 녹색
  '#FF9800', // 주황색
  '#9C27B0', // 보라색
  '#F44336', // 빨간색
  '#00BCD4', // 청록색
  '#795548', // 갈색
  '#607D8B', // 청회색
];

export const ComparisonChart: React.FC<ComparisonChartProps> = ({
  comparisons,
  height = 500
}) => {
  // 차트 데이터 변환
  const chartData: ComparisonPoint[] = React.useMemo(() => {
    if (!comparisons || comparisons.length === 0) {
      return [];
    }

    // 모든 백테스트의 최대 데이터 포인트 수 찾기
    const maxLength = Math.max(...comparisons.map(c => c.equity_curve.length));
    
    // 각 시점별로 데이터 포인트 생성
    const data: ComparisonPoint[] = [];
    
    for (let i = 0; i < maxLength; i++) {
      const point: ComparisonPoint = {
        date: `Day ${i + 1}`,
        timestamp: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString()
      };
      
      // 각 백테스트의 해당 시점 자산 값 추가
      comparisons.forEach((comparison, index) => {
        const equityIndex = Math.min(i, comparison.equity_curve.length - 1);
        point[`strategy_${comparison.backtest_id}`] = comparison.equity_curve[equityIndex];
      });
      
      data.push(point);
    }
    
    return data;
  }, [comparisons]);

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="comparison-tooltip">
          <p className="tooltip-label">{label}</p>
          {payload.map((entry: any, index: number) => {
            const comparison = comparisons.find(c => `strategy_${c.backtest_id}` === entry.dataKey);
            if (!comparison) return null;
            
            const equity = entry.value;
            const initialCapital = comparison.equity_curve[0] || 10000000; // 기본값
            const returnPct = ((equity / initialCapital - 1) * 100);
            
            return (
              <div key={index} className="tooltip-item">
                <div 
                  className="tooltip-color" 
                  style={{ backgroundColor: entry.color }}
                ></div>
                <span className="tooltip-strategy">{comparison.strategy_name}</span>
                <div className="tooltip-values">
                  <span className="tooltip-equity">
                    {equity.toLocaleString()}원
                  </span>
                  <span className={`tooltip-return ${returnPct >= 0 ? 'positive' : 'negative'}`}>
                    ({returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  // 범례 포맷터
  const formatLegend = (value: string) => {
    const comparison = comparisons.find(c => `strategy_${c.backtest_id}` === value);
    return comparison ? comparison.strategy_name : value;
  };

  // 데이터가 없는 경우
  if (!chartData || chartData.length === 0) {
    return (
      <div className="comparison-chart-container" style={{ height }}>
        <div className="no-data-message">
          비교할 데이터가 없습니다.
        </div>
      </div>
    );
  }

  // Y축 범위 계산
  const allValues = chartData.flatMap(point => 
    comparisons.map(c => point[`strategy_${c.backtest_id}`] as number)
  );
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const padding = (maxValue - minValue) * 0.1;

  return (
    <div className="comparison-chart-container" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 20,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          
          <XAxis 
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: '#ccc' }}
            axisLine={{ stroke: '#ccc' }}
            interval="preserveStartEnd"
          />
          
          <YAxis 
            domain={[minValue - padding, maxValue + padding]}
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: '#ccc' }}
            axisLine={{ stroke: '#ccc' }}
            tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
          />
          
          {/* 기준선들 */}
          {comparisons.map((comparison, index) => {
            const initialCapital = comparison.equity_curve[0] || 10000000;
            return (
              <ReferenceLine 
                key={`ref-${comparison.backtest_id}`}
                y={initialCapital} 
                stroke="#999" 
                strokeDasharray="2 2"
                strokeOpacity={0.5}
              />
            );
          })}
          
          {/* 각 전략의 자산 곡선 */}
          {comparisons.map((comparison, index) => (
            <Line
              key={comparison.backtest_id}
              type="monotone"
              dataKey={`strategy_${comparison.backtest_id}`}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={comparison.is_best ? 3 : 2}
              dot={false}
              activeDot={{ 
                r: 4, 
                stroke: CHART_COLORS[index % CHART_COLORS.length], 
                strokeWidth: 2, 
                fill: '#fff' 
              }}
            />
          ))}
          
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            formatter={formatLegend}
            wrapperStyle={{ paddingTop: '20px' }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* 차트 정보 */}
      <div className="chart-summary">
        <div className="summary-grid">
          {comparisons.map((comparison, index) => {
            const initialCapital = comparison.equity_curve[0] || 10000000;
            const finalEquity = comparison.equity_curve[comparison.equity_curve.length - 1];
            const totalReturn = ((finalEquity / initialCapital - 1) * 100);
            
            return (
              <div 
                key={comparison.backtest_id}
                className={`summary-item ${comparison.is_best ? 'best-strategy' : ''}`}
              >
                <div className="strategy-header">
                  <div 
                    className="color-indicator"
                    style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                  ></div>
                  <span className="strategy-name">
                    {comparison.strategy_name}
                    {comparison.is_best && <span className="best-badge">🏆</span>}
                  </span>
                </div>
                
                <div className="strategy-metrics">
                  <div className="metric">
                    <span className="metric-label">수익률</span>
                    <span className={`metric-value ${totalReturn >= 0 ? 'positive' : 'negative'}`}>
                      {totalReturn.toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">MDD</span>
                    <span className="metric-value negative">
                      {comparison.mdd.toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">샤프</span>
                    <span className="metric-value">
                      {comparison.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* 스타일 */}
      <style>{`
        .comparison-chart-container {
          position: relative;
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .no-data-message {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #666;
          font-size: 16px;
        }
        
        .comparison-tooltip {
          background: white;
          border: 1px solid #ccc;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          min-width: 200px;
        }
        
        .tooltip-label {
          margin: 0 0 10px 0;
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }
        
        .tooltip-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          gap: 8px;
        }
        
        .tooltip-item:last-child {
          margin-bottom: 0;
        }
        
        .tooltip-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
          flex-shrink: 0;
        }
        
        .tooltip-strategy {
          font-weight: 500;
          color: #333;
          flex: 1;
          font-size: 13px;
        }
        
        .tooltip-values {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          font-size: 12px;
        }
        
        .tooltip-equity {
          font-weight: 600;
          color: #333;
        }
        
        .tooltip-return {
          font-size: 11px;
        }
        
        .tooltip-return.positive {
          color: #4caf50;
        }
        
        .tooltip-return.negative {
          color: #f44336;
        }
        
        .chart-summary {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #e0e0e0;
        }
        
        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 15px;
        }
        
        .summary-item {
          background: #f8f9fa;
          border-radius: 6px;
          padding: 15px;
          border: 2px solid transparent;
        }
        
        .summary-item.best-strategy {
          border-color: #ffd700;
          background: #fffbf0;
        }
        
        .strategy-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 10px;
        }
        
        .color-indicator {
          width: 16px;
          height: 16px;
          border-radius: 3px;
          flex-shrink: 0;
        }
        
        .strategy-name {
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }
        
        .best-badge {
          margin-left: 4px;
        }
        
        .strategy-metrics {
          display: flex;
          justify-content: space-between;
        }
        
        .metric {
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        
        .metric-label {
          font-size: 11px;
          color: #666;
          margin-bottom: 2px;
        }
        
        .metric-value {
          font-size: 13px;
          font-weight: 600;
        }
        
        .metric-value.positive {
          color: #4caf50;
        }
        
        .metric-value.negative {
          color: #f44336;
        }
        
        @media (max-width: 768px) {
          .summary-grid {
            grid-template-columns: 1fr;
          }
          
          .strategy-metrics {
            gap: 10px;
          }
        }
      `}</style>
    </div>
  );
};