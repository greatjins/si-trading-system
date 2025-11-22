/**
 * 백테스트 페이지
 */
import { useState, useEffect } from 'react';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';
import { ENDPOINTS } from '../services/endpoints';

interface Strategy {
  name: string;
  description: string;
  author: string;
  version: string;
}

interface BacktestResult {
  backtest_id: number;
  strategy_name: string;
  symbol: string;
  total_return: number;
  mdd: number;
  sharpe_ratio: number;
  win_rate: number;
  total_trades: number;
  final_equity: number;
}

export const BacktestPage = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [symbol, setSymbol] = useState('005930');
  // 테스트 데이터 범위 (2025-08-14 ~ 2025-11-22)
  const [startDate, setStartDate] = useState('2025-08-14');
  const [endDate, setEndDate] = useState('2025-11-22');
  const [initialCapital, setInitialCapital] = useState(10000000);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // 전략 목록 로드
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const response = await httpClient.get(ENDPOINTS.STRATEGY.LIST);
        setStrategies(response.data);
        if (response.data.length > 0) {
          setSelectedStrategy(response.data[0].name);
        }
      } catch (err) {
        console.error('전략 목록 로드 실패:', err);
      }
    };
    
    loadStrategies();
  }, []);
  
  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setError(null);
    setResult(null);
    
    console.log('🧪 백테스트 실행:', { selectedStrategy, symbol, startDate, endDate });
    
    try {
      const response = await httpClient.post(ENDPOINTS.BACKTEST.RUN, {
        strategy_name: selectedStrategy,
        symbol,
        interval: '1d',
        start_date: startDate + 'T00:00:00',
        end_date: endDate + 'T23:59:59',
        initial_capital: initialCapital,
        parameters: {},
      });
      
      console.log('✅ 백테스트 완료:', response.data);
      setResult(response.data);
    } catch (err: any) {
      console.error('❌ 백테스트 실패:', err);
      setError(err.response?.data?.detail || '백테스트 실행 실패');
    } finally {
      setIsRunning(false);
    }
  };
  
  
  return (
    <PageLayout title="백테스트" description="전략을 선택하고 과거 데이터로 성과를 테스트하세요">
      
      <div className="backtest-content">
        <div className="backtest-form-section">
          <h2>백테스트 설정</h2>
          
          <form onSubmit={handleRunBacktest} className="backtest-form">
            <div className="form-group">
              <label>전략 선택</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="form-select"
                required
              >
                {strategies.map((strategy) => (
                  <option key={strategy.name} value={strategy.name}>
                    {strategy.name} - {strategy.description}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>종목 코드</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="form-input"
                placeholder="005930"
                required
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>시작일</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="form-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>종료일</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="form-input"
                  required
                />
              </div>
            </div>
            
            <div className="form-group">
              <label>초기 자본금</label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="form-input"
                min="1000000"
                step="1000000"
                required
              />
            </div>
            
            {error && <div className="error-message">{error}</div>}
            
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={isRunning || strategies.length === 0}
            >
              {isRunning ? '백테스트 실행 중...' : '백테스트 실행'}
            </button>
          </form>
        </div>
        
        {result && (
          <div className="backtest-result-section">
            <h2>백테스트 결과</h2>
            
            <div className="result-grid">
              <div className="result-card">
                <div className="result-label">총 수익률</div>
                <div className={`result-value ${result.total_return >= 0 ? 'positive' : 'negative'}`}>
                  {(result.total_return * 100).toFixed(2)}%
                </div>
              </div>
              
              <div className="result-card">
                <div className="result-label">최종 자산</div>
                <div className="result-value">
                  {result.final_equity.toLocaleString()}원
                </div>
              </div>
              
              <div className="result-card">
                <div className="result-label">MDD</div>
                <div className="result-value negative">
                  {(result.mdd * 100).toFixed(2)}%
                </div>
              </div>
              
              <div className="result-card">
                <div className="result-label">샤프 비율</div>
                <div className="result-value">
                  {result.sharpe_ratio.toFixed(2)}
                </div>
              </div>
              
              <div className="result-card">
                <div className="result-label">승률</div>
                <div className="result-value">
                  {(result.win_rate * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="result-card">
                <div className="result-label">총 거래 수</div>
                <div className="result-value">
                  {result.total_trades}회
                </div>
              </div>
            </div>
            
            <div className="result-details">
              <h3>상세 정보</h3>
              <table>
                <tbody>
                  <tr>
                    <td>전략</td>
                    <td>{result.strategy_name}</td>
                  </tr>
                  <tr>
                    <td>종목</td>
                    <td>{result.symbol}</td>
                  </tr>
                  <tr>
                    <td>백테스트 ID</td>
                    <td>{result.backtest_id}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
};
