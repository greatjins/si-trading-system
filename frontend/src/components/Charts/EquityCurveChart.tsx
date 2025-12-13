/**
 * 자산 곡선 차트 컴포넌트
 */
import React from 'react';
import styles from './EquityCurveChart.module.css';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  ReferenceLine
} from 'recharts';

interface EquityPoint {
  timestamp: string;
  equity: number;
  date: string;
  drawdown?: number;
}

interface EquityCurveChartProps {
  /** 자산 곡선 데이터 */
  equityData: number[];
  /** 타임스탬프 데이터 */
  timestamps: string[];
  /** 초기 자본 */
  initialCapital: number;
  /** 최대 낙폭(MDD) */
  mdd: number;
  /** 차트 높이 */
  height?: number;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  equityData,
  timestamps,
  initialCapital,
  mdd,
  height = 400
}) => {
  // 차트 데이터 변환
  const chartData: EquityPoint[] = React.useMemo(() => {
    if (!equityData || !timestamps || equityData.length === 0 || timestamps.length === 0) {
      return [];
    }

    // 길이가 다른 경우 짧은 쪽에 맞춤
    const minLength = Math.min(equityData.length, timestamps.length);

    let maxEquity = initialCapital;
    
    return equityData.slice(0, minLength).map((equity, index) => {
      // 최고점 업데이트
      if (equity > maxEquity) {
        maxEquity = equity;
      }
      
      // 낙폭 계산 (현재 자산 / 최고점 - 1) * 100
      const drawdown = maxEquity > 0 ? ((equity / maxEquity - 1) * 100) : 0;
      
      return {
        timestamp: timestamps[index],
        equity,
        date: new Date(timestamps[index]).toLocaleDateString('ko-KR'),
        drawdown
      };
    });
  }, [equityData, timestamps, initialCapital]);

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className={styles.equityTooltip}>
          <p className={styles.tooltipDate}>{data.date}</p>
          <p className={styles.tooltipEquity}>
            자산: <span className="value">{data.equity.toLocaleString()}원</span>
          </p>
          <p className={styles.tooltipReturn}>
            수익률: <span className={`value ${data.equity >= initialCapital ? 'positive' : 'negative'}`}>
              {(((data.equity / initialCapital) - 1) * 100).toFixed(2)}%
            </span>
          </p>
          {data.drawdown < 0 && (
            <p className={styles.tooltipDrawdown}>
              낙폭: <span className="value negative">{data.drawdown.toFixed(2)}%</span>
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // 데이터가 없는 경우
  if (!chartData || chartData.length === 0) {
    return (
      <div className={styles.equityChartContainer} style={{ height }}>
        <div className={styles.noDataMessage}>
          자산 곡선 데이터가 없습니다.
        </div>
      </div>
    );
  }

  const minEquity = Math.min(...equityData);
  const maxEquity = Math.max(...equityData);
  const padding = (maxEquity - minEquity) * 0.1;

  return (
    <div className={styles.equityChartContainer} style={{ height: height + 80 }}>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 60,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          
          <XAxis 
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: '#ccc' }}
            axisLine={{ stroke: '#ccc' }}
            interval="preserveStartEnd"
            angle={-45}
            textAnchor="end"
            height={60}
          />
          
          <YAxis 
            domain={[minEquity - padding, maxEquity + padding]}
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: '#ccc' }}
            axisLine={{ stroke: '#ccc' }}
            tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
          />
          
          {/* 초기 자본 기준선 */}
          <ReferenceLine 
            y={initialCapital} 
            stroke="#666" 
            strokeDasharray="5 5"
          />
          
          {/* MDD 구간 하이라이트 (낙폭이 있는 구간) */}
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="none"
            fill="rgba(244, 67, 54, 0.1)"
            fillOpacity={0.3}
          />
          
          {/* 자산 곡선 */}
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#2196F3"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#2196F3', strokeWidth: 2, fill: '#fff' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
        </ComposedChart>
      </ResponsiveContainer>
      
      {/* 차트 정보 */}
      <div className={styles.chartInfo}>
        <div className={styles.infoItem}>
          <span className="label">초기 자본:</span>
          <span className="value">{initialCapital.toLocaleString()}원</span>
        </div>
        <div className={styles.infoItem}>
          <span className="label">최종 자산:</span>
          <span className={`value ${equityData[equityData.length - 1] >= initialCapital ? 'positive' : 'negative'}`}>
            {equityData[equityData.length - 1].toLocaleString()}원
          </span>
        </div>
        <div className={styles.infoItem}>
          <span className="label">총 수익률:</span>
          <span className={`value ${equityData[equityData.length - 1] >= initialCapital ? 'positive' : 'negative'}`}>
            {(((equityData[equityData.length - 1] / initialCapital) - 1) * 100).toFixed(2)}%
          </span>
        </div>
        <div className={styles.infoItem}>
          <span className="label">MDD:</span>
          <span className="value negative">{mdd.toFixed(2)}%</span>
        </div>
      </div>
    </div>
  );
};