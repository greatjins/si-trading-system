/**
 * 차트 컨트롤 (종목 선택, 시간 간격 선택)
 */
import { useState } from 'react';
import { useChartStore } from '../../../app/store/chartStore';
import { CHART_INTERVALS, ChartInterval } from '../../../constants/chart-constants';

export const ChartControls = () => {
  const { symbol, interval, setSymbol, setInterval, reset } = useChartStore();
  const [inputValue, setInputValue] = useState(symbol);
  
  const handleSymbolSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && inputValue !== symbol) {
      reset(); // 기존 데이터 초기화
      setSymbol(inputValue.trim());
    }
  };
  
  const handleIntervalChange = (newInterval: ChartInterval) => {
    if (newInterval !== interval) {
      reset(); // 기존 데이터 초기화
      setInterval(newInterval);
    }
  };
  
  return (
    <div className="chart-controls">
      <div className="control-group">
        <label>종목 코드:</label>
        <form onSubmit={handleSymbolSubmit} style={{ display: 'inline' }}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onBlur={handleSymbolSubmit}
            placeholder="005930"
            className="symbol-input"
          />
        </form>
      </div>
      
      <div className="control-group">
        <label>시간 간격:</label>
        <div className="interval-buttons">
          {Object.entries(CHART_INTERVALS).map(([key, { label }]) => (
            <button
              key={key}
              className={`interval-btn ${interval === key ? 'active' : ''}`}
              onClick={() => handleIntervalChange(key as ChartInterval)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
