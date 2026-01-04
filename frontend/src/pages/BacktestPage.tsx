/**
 * 백테스트 페이지
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';
import { ENDPOINTS } from '../services/endpoints';

interface Strategy {
  name: string;
  description: string;
  author: string;
  version: string;
  is_portfolio?: boolean;
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
  const navigate = useNavigate();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [isPortfolioStrategy, setIsPortfolioStrategy] = useState(false);
  const [symbol, setSymbol] = useState('005930');
  const [startDate, setStartDate] = useState('2025-08-14');
  const [endDate, setEndDate] = useState('2025-11-21');
  const [initialCapital, setInitialCapital] = useState(10000000);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  
  // 전략 파라미터 (포트폴리오 전략용)
  const [parameters, setParameters] = useState<Record<string, any>>({
    per_max: 15.0,
    pbr_max: 1.5,
    roe_min: 5.0,
    max_stocks: 20,
  });
  
  // 포트폴리오 전략 목록 (하드코딩)
  const portfolioStrategies = ['ValuePortfolioStrategy', 'SimplePortfolioStrategy', '200일선초과일목상향돌파'];
  
  // 전략 목록 로드
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        // 코드 기반 전략 로드
        const codeStrategiesResponse = await httpClient.get(ENDPOINTS.STRATEGY.LIST);
        const codeStrategies = codeStrategiesResponse.data;
        
        // 전략 빌더 전략 로드
        let builderStrategies = [];
        let builderPortfolioStrategies: string[] = [];
        try {
          const builderResponse = await httpClient.get('/api/strategy-builder/list');
          builderStrategies = builderResponse.data.map((s: any) => {
            // 포트폴리오 전략이면 목록에 추가
            if (s.is_portfolio) {
              builderPortfolioStrategies.push(s.name);
            }
            return {
              name: s.name,
              description: s.description,
              author: 'Strategy Builder',
              version: '1.0.0',
              is_portfolio: s.is_portfolio,
            };
          });
        } catch (err) {
          console.log('전략 빌더 전략 로드 실패 (로그인 필요):', err);
        }
        
        // 전략 합치기
        const allStrategies = [...codeStrategies, ...builderStrategies];
        setStrategies(allStrategies);
        
        // 포트폴리오 전략 목록 업데이트
        const allPortfolioStrategies = [...portfolioStrategies, ...builderPortfolioStrategies];
        
        if (allStrategies.length > 0) {
          const firstStrategy = allStrategies[0].name;
          setSelectedStrategy(firstStrategy);
          setIsPortfolioStrategy(allPortfolioStrategies.includes(firstStrategy));
        }
      } catch (err) {
        console.error('전략 목록 로드 실패:', err);
      }
    };
    
    loadStrategies();
  }, []);
  
  // 전략 변경 시 포트폴리오 여부 체크
  useEffect(() => {
    // 선택된 전략 찾기
    const strategy = strategies.find(s => s.name === selectedStrategy);
    const isPortfolio = strategy?.is_portfolio || portfolioStrategies.includes(selectedStrategy);
    
    console.log(`🔍 전략 타입 확인: ${selectedStrategy}`, {
      strategy: strategy,
      is_portfolio_from_api: strategy?.is_portfolio,
      is_in_hardcoded_list: portfolioStrategies.includes(selectedStrategy),
      final_is_portfolio: isPortfolio
    });
    
    setIsPortfolioStrategy(isPortfolio);
    
    // 전략별 기본 파라미터 설정
    if (selectedStrategy === 'ValuePortfolioStrategy') {
      setParameters({
        per_max: 15.0,
        pbr_max: 1.5,
        roe_min: 5.0,
        max_stocks: 20,
        rebalance_days: 30,
      });
    } else if (selectedStrategy === 'SimplePortfolioStrategy') {
      setParameters({
        max_stocks: 10,
        rebalance_days: 7,
      });
    }
  }, [selectedStrategy, strategies]);
  
  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setError(null);
    setResult(null);
    
    const endpoint = isPortfolioStrategy ? ENDPOINTS.BACKTEST.PORTFOLIO : ENDPOINTS.BACKTEST.RUN;
    const requestData: any = {
      strategy_name: selectedStrategy,
      interval: '1d',
      start_date: startDate + 'T00:00:00',
      end_date: endDate + 'T23:59:59',
      initial_capital: initialCapital,
      parameters: isPortfolioStrategy ? parameters : {},
    };
    
    // 단일 종목 전략인 경우에만 symbol 추가
    if (!isPortfolioStrategy) {
      requestData.symbol = symbol;
    }
    
    console.log(`🧪 ${isPortfolioStrategy ? '포트폴리오' : '단일 종목'} 백테스트 실행:`, requestData);
    
    try {
      const response = await httpClient.post(endpoint, requestData);
      
      console.log('✅ 백테스트 응답:', response.data);
      
      // 포트폴리오 백테스트는 비동기 작업 (task_id 반환)
      if (isPortfolioStrategy && response.data.task_id) {
        setTaskId(response.data.task_id);
        // 상태 폴링 시작
        pollBacktestStatus(response.data.task_id);
      } else {
        // 단일 종목 백테스트는 즉시 결과 반환
        setResult(response.data);
        setIsRunning(false);
      }
    } catch (err: any) {
      console.error('❌ 백테스트 실패:', err);
      setError(err.response?.data?.detail || '백테스트 실행 실패');
      setIsRunning(false);
    }
  };
  
  const handleParameterChange = (key: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [key]: value,
    }));
  };
  
  // 포트폴리오 백테스트 상태 폴링
  const pollBacktestStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await httpClient.get(`${ENDPOINTS.BACKTEST.PORTFOLIO}/${taskId}`);
        const status = response.data;
        
        console.log('📊 백테스트 상태:', status);
        
        if (status.status === 'completed' && status.result) {
          // 완료: 결과 표시
          setResult(status.result);
          setIsRunning(false);
          setTaskId(null);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        } else if (status.status === 'failed') {
          // 실패: 에러 표시
          setError(status.error || '백테스트 실패');
          setIsRunning(false);
          setTaskId(null);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        }
        // running 상태면 계속 폴링
      } catch (err: any) {
        console.error('❌ 상태 조회 실패:', err);
        setError('백테스트 상태 조회 실패');
        setIsRunning(false);
        setTaskId(null);
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      }
    };
    
    // 즉시 한 번 실행
    await poll();
    
    // 2초마다 폴링
    const interval = setInterval(poll, 2000);
    setPollingInterval(interval);
  };
  
  // 컴포넌트 언마운트 시 폴링 정리
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);
  
  
  return (
    <PageLayout title="백테스트" description="전략을 선택하고 과거 데이터로 성과를 테스트하세요">
      
      {/* 페이지 헤더 */}
      <div className="page-header">
        <div></div>
        <div>
          <button 
            onClick={() => navigate('/backtest/compare')} 
            className="btn btn-outline"
          >
            📊 백테스트 비교
          </button>
        </div>
      </div>
      
      <div className="backtest-content" style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px' }}>
        <div className="grid" style={{ gridTemplateColumns: '1fr', gap: '30px' }}>
          <div className="backtest-form-section">
            <h2 className="mb-3">백테스트 설정</h2>
            
            {isPortfolioStrategy && (
              <div className="info-banner mb-3">
                📈 포트폴리오 전략: 전략이 자동으로 종목을 선택합니다
              </div>
            )}
            
            <div className="card" style={{ padding: '30px', width: '100%', maxWidth: 'none' }}>
              <form onSubmit={handleRunBacktest} style={{ width: '100%' }}>
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
            
            {/* 단일 종목 전략인 경우에만 종목 코드 입력 */}
            {!isPortfolioStrategy && (
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
            )}
            
            {/* 포트폴리오 전략인 경우 파라미터 입력 */}
            {isPortfolioStrategy && (
              <div className="parameters-section">
                <h3>전략 파라미터</h3>
                
                {selectedStrategy === 'ValuePortfolioStrategy' && (
                  <>
                    <div className="form-row">
                      <div className="form-group">
                        <label>최대 PER</label>
                        <input
                          type="number"
                          value={parameters.per_max}
                          onChange={(e) => handleParameterChange('per_max', parseFloat(e.target.value))}
                          className="form-input"
                          step="0.1"
                        />
                      </div>
                      
                      <div className="form-group">
                        <label>최대 PBR</label>
                        <input
                          type="number"
                          value={parameters.pbr_max}
                          onChange={(e) => handleParameterChange('pbr_max', parseFloat(e.target.value))}
                          className="form-input"
                          step="0.1"
                        />
                      </div>
                    </div>
                    
                    <div className="form-row">
                      <div className="form-group">
                        <label>최소 ROE (%)</label>
                        <input
                          type="number"
                          value={parameters.roe_min}
                          onChange={(e) => handleParameterChange('roe_min', parseFloat(e.target.value))}
                          className="form-input"
                          step="0.1"
                        />
                      </div>
                      
                      <div className="form-group">
                        <label>최대 보유 종목 수</label>
                        <input
                          type="number"
                          value={parameters.max_stocks}
                          onChange={(e) => handleParameterChange('max_stocks', parseInt(e.target.value))}
                          className="form-input"
                          min="1"
                          max="50"
                        />
                      </div>
                    </div>
                    
                    <div className="form-group">
                      <label>리밸런싱 주기 (일)</label>
                      <input
                        type="number"
                        value={parameters.rebalance_days}
                        onChange={(e) => handleParameterChange('rebalance_days', parseInt(e.target.value))}
                        className="form-input"
                        min="1"
                        max="365"
                      />
                    </div>
                  </>
                )}
                
                {selectedStrategy === 'SimplePortfolioStrategy' && (
                  <>
                    <div className="form-group">
                      <label>최대 보유 종목 수</label>
                      <input
                        type="number"
                        value={parameters.max_stocks}
                        onChange={(e) => handleParameterChange('max_stocks', parseInt(e.target.value))}
                        className="form-input"
                        min="1"
                        max="50"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label>리밸런싱 주기 (일)</label>
                      <input
                        type="number"
                        value={parameters.rebalance_days}
                        onChange={(e) => handleParameterChange('rebalance_days', parseInt(e.target.value))}
                        className="form-input"
                        min="1"
                        max="365"
                      />
                    </div>
                  </>
                )}
              </div>
            )}
            
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
            
            {error && <div className="message message-error">{error}</div>}
            
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={isRunning || strategies.length === 0}
            >
              {isRunning ? '백테스트 실행 중...' : '백테스트 실행'}
            </button>
              </form>
            </div>
          </div>
        </div>
        
        {taskId && isRunning && (
          <div className="backtest-result-section">
            <h2 className="mb-4">백테스트 진행 중...</h2>
            <div className="card text-center" style={{ padding: '40px' }}>
              <div className="mb-3">
                <div className="spinner" style={{ margin: '0 auto' }}></div>
              </div>
              <p>백테스트가 실행 중입니다. 잠시만 기다려주세요...</p>
              <p className="text-sm text-secondary mt-2">작업 ID: {taskId}</p>
            </div>
          </div>
        )}
        
        {result && result.final_equity !== undefined && (
          <div className="backtest-result-section">
            <h2 className="mb-4">백테스트 결과</h2>
            
            <div className="grid grid-3 mb-4">
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">총 수익률</div>
                <div className={`text-xl font-weight-bold ${(result.total_return ?? 0) >= 0 ? 'metric-positive' : 'metric-negative'}`}>
                  {result.total_return !== undefined ? (result.total_return * 100).toFixed(2) : 'N/A'}%
                </div>
              </div>
              
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">최종 자산</div>
                <div className="text-xl font-weight-bold">
                  {result.final_equity !== undefined ? result.final_equity.toLocaleString() : 'N/A'}원
                </div>
              </div>
              
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">MDD</div>
                <div className="text-xl font-weight-bold metric-negative">
                  {result.mdd !== undefined ? (result.mdd * 100).toFixed(2) : 'N/A'}%
                </div>
              </div>
              
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">샤프 비율</div>
                <div className="text-xl font-weight-bold">
                  {result.sharpe_ratio !== undefined ? result.sharpe_ratio.toFixed(2) : 'N/A'}
                </div>
              </div>
              
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">승률</div>
                <div className="text-xl font-weight-bold">
                  {result.win_rate !== undefined ? (result.win_rate * 100).toFixed(1) : 'N/A'}%
                </div>
              </div>
              
              <div className="card text-center">
                <div className="text-sm text-secondary mb-1">총 거래 수</div>
                <div className="text-xl font-weight-bold">
                  {result.total_trades !== undefined ? `${result.total_trades}회 (${Math.floor(result.total_trades / 2)}쌍)` : 'N/A'}
                </div>
              </div>
            </div>
            
            <div className="card">
              <h3 className="mb-3">상세 정보</h3>
              <table className="table">
                <tbody>
                  <tr>
                    <td>전략</td>
                    <td>{result.strategy_name}</td>
                  </tr>
                  {result.symbol && (
                    <tr>
                      <td>종목</td>
                      <td>{result.symbol}</td>
                    </tr>
                  )}
                  <tr>
                    <td>백테스트 ID</td>
                    <td>{result.backtest_id}</td>
                  </tr>
                </tbody>
              </table>
              
              <div className="text-center mt-4">
                <button 
                  onClick={() => navigate(`/backtest/results/${result.backtest_id}`)}
                  className="btn btn-primary"
                >
                  📊 상세 분석 보기
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* 추가 스타일 */}
      <style>{`
        .backtest-form-section .card {
          width: 100% !important;
          max-width: none !important;
        }
        
        .backtest-form-section .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        
        .backtest-form-section .form-group {
          margin-bottom: 20px;
        }
        
        .backtest-form-section .parameters-section {
          margin: 20px 0;
          padding: 20px;
          background: var(--color-background);
          border-radius: var(--radius-sm);
        }
        
        @media (max-width: 768px) {
          .backtest-form-section .form-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </PageLayout>
  );
};
