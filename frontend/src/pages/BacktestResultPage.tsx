/**
 * 백테스트 결과 페이지
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageLayout } from '../components/Layout/PageLayout';
import { EquityCurveChart } from '../components/Charts';
import { SymbolPerformanceList } from '../components/Tables';
import { SymbolDetailModal } from '../components/Modals';
import { LoadingSpinner, ErrorMessage } from '../components/UI';
import { httpClient } from '../services/http';
import { BacktestResultDetail } from '../types/backtest';

interface BacktestResultPageProps {}

export const BacktestResultPage: React.FC<BacktestResultPageProps> = () => {
  const { backtestId } = useParams<{ backtestId: string }>();
  const navigate = useNavigate();
  
  // 상태 관리
  const [result, setResult] = useState<BacktestResultDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  
  // 백테스트 결과 로드
  useEffect(() => {
    const loadBacktestResult = async () => {
      if (!backtestId) {
        setError('백테스트 ID가 없습니다.');
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        setError(null);
        
        const response = await httpClient.get(`/api/backtest/results/${backtestId}`);
        setResult(response.data);
        
        console.log('✅ 백테스트 결과 로드 완료:', response.data);
      } catch (err: any) {
        console.error('❌ 백테스트 결과 로드 실패:', err);
        setError(err.response?.data?.detail || '백테스트 결과를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    loadBacktestResult();
  }, [backtestId]);
  
  // 종목 클릭 핸들러
  const handleSymbolClick = (symbol: string) => {
    setSelectedSymbol(symbol);
  };
  
  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setSelectedSymbol(null);
  };
  
  // 뒤로 가기 핸들러
  const handleGoBack = () => {
    // 브라우저 히스토리를 사용하여 이전 페이지로 이동
    // 만약 히스토리가 없다면 백테스트 페이지로 이동
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/backtest');
    }
  };
  
  // 로딩 상태
  if (loading) {
    return (
      <PageLayout title="백테스트 결과" description="백테스트 결과를 불러오는 중...">
        <LoadingSpinner message="백테스트 결과를 불러오는 중..." size="large" />
      </PageLayout>
    );
  }
  
  // 에러 상태
  if (error) {
    return (
      <PageLayout title="백테스트 결과" description="백테스트 결과 조회 실패">
        <ErrorMessage
          title="백테스트 결과 조회 실패"
          message={error}
          showRetry={true}
          onRetry={handleGoBack}
          type="error"
        />
      </PageLayout>
    );
  }
  
  // 결과 없음
  if (!result) {
    return (
      <PageLayout title="백테스트 결과" description="백테스트 결과가 없습니다">
        <div className="no-result-container">
          <p>백테스트 결과가 없습니다.</p>
          <button onClick={handleGoBack} className="btn btn-primary">
            백테스트 페이지로 돌아가기
          </button>
        </div>
      </PageLayout>
    );
  }
  
  return (
    <PageLayout 
      title={`백테스트 결과: ${result.strategy_name}`}
      description={`${result.start_date} ~ ${result.end_date}`}
    >
      <div className="backtest-result-page">
        {/* 헤더 */}
        <div className="page-header">
          <button onClick={handleGoBack} className="btn btn-secondary">
            ← 뒤로 가기
          </button>
          
          <div>
            <h2 className="mb-3">{result.strategy_name}</h2>
            <div className="d-flex gap-4" style={{ flexWrap: 'wrap' }}>
              <div className="text-center">
                <span className="text-xs text-secondary d-block mb-1">총 수익률</span>
                <span className={`text-lg font-weight-bold ${result.total_return >= 0 ? 'metric-positive' : 'metric-negative'}`}>
                  {result.total_return.toFixed(2)}%
                </span>
              </div>
              <div className="text-center">
                <span className="text-xs text-secondary d-block mb-1">MDD</span>
                <span className="text-lg font-weight-bold metric-negative">
                  {result.mdd.toFixed(2)}%
                </span>
              </div>
              <div className="text-center">
                <span className="text-xs text-secondary d-block mb-1">샤프 비율</span>
                <span className="text-lg font-weight-bold">
                  {result.sharpe_ratio.toFixed(2)}
                </span>
              </div>
              <div className="text-center">
                <span className="text-xs text-secondary d-block mb-1">승률</span>
                <span className="text-lg font-weight-bold">
                  {result.win_rate.toFixed(1)}%
                </span>
              </div>
              <div className="text-center">
                <span className="text-xs text-secondary d-block mb-1">총 거래</span>
                <span className="text-lg font-weight-bold">
                  {result.total_trades}회 ({Math.floor(result.total_trades / 2)}쌍)
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* 자산 곡선 차트 */}
        <div className="chart-section">
          <h3 className="mb-3">📈 자산 곡선</h3>
          <EquityCurveChart
            equityData={result.equity_curve}
            timestamps={result.equity_timestamps}
            initialCapital={result.initial_capital}
            mdd={result.mdd}
            height={400}
          />
        </div>
        
        {/* 종목별 성과 리스트 */}
        <div className="performance-section">
          <h3 className="mb-3">📊 종목별 성과</h3>
          <SymbolPerformanceList
            performances={result.symbol_performances}
            onSymbolClick={handleSymbolClick}
            loading={false}
          />
        </div>
        
        {/* 종목 상세 모달 */}
        {selectedSymbol && backtestId && (
          <SymbolDetailModal
            backtestId={backtestId}
            symbol={selectedSymbol}
            onClose={handleCloseModal}
          />
        )}
      </div>
      
      {/* 최소한의 커스텀 스타일 */}
      <style>{`
        .backtest-result-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .text-secondary {
          color: var(--color-text-secondary);
        }
        
        .chart-section {
          margin-bottom: 60px;
        }
        
        .performance-section {
          margin-bottom: 40px;
          margin-top: 60px;
          clear: both;
        }
      `}</style>
    </PageLayout>
  );
};