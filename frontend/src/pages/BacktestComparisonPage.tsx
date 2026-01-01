/**
 * 백테스트 비교 페이지
 */
import { ComparisonView } from '../modules/analysis/components/ComparisonView';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '../components/Layout/PageLayout';
import { ComparisonChart } from '../components/Charts';
import { LoadingSpinner } from '../components/UI';
import { httpClient } from '../services/http';
import { BacktestComparison } from '../types/backtest';

interface BacktestListItem {
  backtest_id: number;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_return: number;
  mdd: number;
  sharpe_ratio: number;
  final_equity: number;
  created_at: string;
}

export const BacktestComparisonPage: React.FC = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const [backtests, setBacktests] = useState<BacktestListItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [comparison, setComparison] = useState<BacktestComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 백테스트 목록 로드
  useEffect(() => {
    const loadBacktests = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 실제 API 호출로 백테스트 목록 조회
        const response = await httpClient.get('/api/backtest/results');
        const apiBacktests = response.data;
        
        // API 응답을 컴포넌트에서 사용하는 형식으로 변환
        const formattedBacktests: BacktestListItem[] = apiBacktests.map((bt: any) => ({
          backtest_id: bt.backtest_id,
          strategy_name: bt.strategy_name,
          start_date: bt.start_date,
          end_date: bt.end_date,
          total_return: (bt.total_return || 0) * 100, // 소수를 퍼센트로 변환
          mdd: (bt.mdd || 0) * 100, // 소수를 퍼센트로 변환
          sharpe_ratio: bt.sharpe_ratio || 0,
          final_equity: bt.final_equity || 0,
          created_at: bt.created_at
        }));
        
        console.log(`✅ 백테스트 목록 로드 완료: ${formattedBacktests.length}개`);
        setBacktests(formattedBacktests);
      } catch (err: any) {
        console.error('❌ 백테스트 목록 로드 실패:', err);
        setError('백테스트 목록을 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadBacktests();
  }, []);

  // 체크박스 변경 핸들러
  const handleCheckboxChange = (backtestId: number, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(backtestId);
    } else {
      newSelected.delete(backtestId);
    }
    setSelectedIds(newSelected);
  };

  // 전체 선택/해제
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(backtests.map(bt => bt.backtest_id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  // 비교 실행
  const handleCompare = async () => {
    if (selectedIds.size < 2) {
      alert('비교하려면 최소 2개의 백테스트를 선택해주세요.');
      return;
    }

    try {
      setComparing(true);
      setError(null);

      const response = await httpClient.post('/api/backtest/results/compare', {
        backtest_ids: Array.from(selectedIds)
      });

      setComparison(response.data);
    } catch (err: any) {
      console.error('❌ 백테스트 비교 실패:', err);
      setError(err.response?.data?.detail || '백테스트 비교에 실패했습니다.');
    } finally {
      setComparing(false);
    }
  };

  // 개별 백테스트 삭제
  const handleDeleteSingle = async (backtestId: number) => {
    if (!confirm('이 백테스트를 삭제하시겠습니까?')) {
      return;
    }

    try {
      setError(null);
      
      await httpClient.delete(`/api/backtest/results/${backtestId}`);
      
      // 목록에서 제거
      setBacktests(prev => prev.filter(bt => bt.backtest_id !== backtestId));
      
      // 선택된 항목에서도 제거
      const newSelected = new Set(selectedIds);
      newSelected.delete(backtestId);
      setSelectedIds(newSelected);
      
      alert('백테스트가 성공적으로 삭제되었습니다.');
    } catch (err: any) {
      console.error('❌ 백테스트 삭제 실패:', err);
      setError(err.response?.data?.detail || '백테스트 삭제에 실패했습니다.');
    }
  };

  // 선택된 백테스트 일괄 삭제
  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) {
      alert('삭제할 백테스트를 선택해주세요.');
      return;
    }

    if (!confirm(`선택된 ${selectedIds.size}개의 백테스트를 삭제하시겠습니까?`)) {
      return;
    }

    try {
      setDeleting(true);
      setError(null);

      const response = await httpClient.delete('/api/backtest/results/batch', {
        data: Array.from(selectedIds)
      });

      // 성공적으로 삭제된 항목들을 목록에서 제거
      setBacktests(prev => prev.filter(bt => !selectedIds.has(bt.backtest_id)));
      
      // 선택 초기화
      setSelectedIds(new Set());
      
      alert(`${response.data.deleted_count}개의 백테스트가 성공적으로 삭제되었습니다.`);
    } catch (err: any) {
      console.error('❌ 백테스트 일괄 삭제 실패:', err);
      setError(err.response?.data?.detail || '백테스트 삭제에 실패했습니다.');
    } finally {
      setDeleting(false);
    }
  };

  // 개별 결과 보기
  const handleViewResult = (backtestId: number) => {
    navigate(`/backtest/results/${backtestId}`);
  };

  // 뒤로 가기
  const handleGoBack = () => {
    navigate('/backtest');
  };

  // 로딩 상태
  if (loading) {
    return (
      <PageLayout title="백테스트 비교" description="백테스트 목록을 불러오는 중...">
        <LoadingSpinner message="백테스트 목록을 불러오는 중..." size="large" />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="백테스트 비교" description="여러 백테스트 결과를 비교 분석합니다">
      <div className="comparison-page">
        {/* 헤더 */}
        <div className="page-header">
          <button onClick={handleGoBack} className="btn btn-secondary">
            ← 뒤로 가기
          </button>
          
          <div className="d-flex gap-2">
            <button 
              onClick={handleDeleteSelected}
              disabled={selectedIds.size === 0 || deleting}
              className="btn btn-danger"
            >
              {deleting ? '삭제 중...' : `선택된 ${selectedIds.size}개 삭제`}
            </button>
            
            <button 
              onClick={handleCompare}
              disabled={selectedIds.size < 2 || comparing}
              className="btn btn-primary"
            >
              {comparing ? '비교 중...' : `선택된 ${selectedIds.size}개 비교`}
            </button>
          </div>
        </div>

        {error && (
          <div className="message message-error">
            {error}
          </div>
        )}

        {/* 백테스트 목록 */}
        <div className="backtest-list-section">
          <div className="section-header">
            <h3>📊 백테스트 목록</h3>
            <label className="select-all">
              <input
                type="checkbox"
                checked={selectedIds.size === backtests.length && backtests.length > 0}
                onChange={(e) => handleSelectAll(e.target.checked)}
              />
              전체 선택
            </label>
          </div>

          <div className="grid grid-auto">
            {backtests.map((backtest) => (
              <div 
                key={backtest.backtest_id}
                className={`card ${selectedIds.has(backtest.backtest_id) ? 'selected' : ''}`}
              >
                <div className="card-header">
                  <label className="d-flex align-items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(backtest.backtest_id)}
                      onChange={(e) => handleCheckboxChange(backtest.backtest_id, e.target.checked)}
                    />
                    <span className="font-weight-medium">{backtest.strategy_name}</span>
                  </label>
                  
                  <div className="d-flex gap-2">
                    <button
                      onClick={() => handleViewResult(backtest.backtest_id)}
                      className="btn btn-sm btn-outline"
                    >
                      상세보기
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSingle(backtest.backtest_id);
                      }}
                      className="btn btn-sm btn-danger-outline"
                      title="삭제"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <div className="card-content">
                  <div className="metric-row">
                    <span className="label">기간:</span>
                    <span className="value">
                      {new Date(backtest.start_date).toLocaleDateString('ko-KR')} ~ 
                      {new Date(backtest.end_date).toLocaleDateString('ko-KR')}
                    </span>
                  </div>
                  
                  <div className="metric-row">
                    <span className="label">수익률:</span>
                    <span className={`value ${backtest.total_return >= 0 ? 'metric-positive' : 'metric-negative'}`}>
                      {backtest.total_return.toFixed(2)}%
                    </span>
                  </div>
                  
                  <div className="metric-row">
                    <span className="label">MDD:</span>
                    <span className="value metric-negative">
                      {backtest.mdd.toFixed(2)}%
                    </span>
                  </div>
                  
                  <div className="metric-row">
                    <span className="label">샤프 비율:</span>
                    <span className="value">
                      {backtest.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                  
                  <div className="metric-row">
                    <span className="label">최종 자산:</span>
                    <span className="value">
                      {backtest.final_equity.toLocaleString()}원
                    </span>
                  </div>
                </div>

                <div className="card-footer">
                  <span className="text-sm text-muted">
                    {new Date(backtest.created_at).toLocaleDateString('ko-KR')} 생성
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 백테스트-실전 비교 (Phase 4) */}
        <div className="backtest-live-comparison-section">
          <h3>백테스트 vs 실전 비교</h3>
          <ComparisonView />
        </div>

        {/* 비교 결과 */}
        {comparison && (
          <div className="card">
            <h3 className="mb-3">📈 비교 결과</h3>
            
            {/* 비교 차트 */}
            <div className="mb-4">
              <ComparisonChart 
                comparisons={comparison.comparison}
                height={400}
              />
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>전략명</th>
                    <th>수익률</th>
                    <th>MDD</th>
                    <th>샤프 비율</th>
                    <th>승률</th>
                    <th>손익비</th>
                    <th>총 거래 (쌍)</th>
                    <th>순위</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.comparison
                    .sort((a, b) => b.total_return - a.total_return)
                    .map((item, index) => (
                    <tr 
                      key={item.backtest_id}
                      className={item.is_best ? 'best-result' : ''}
                      style={item.is_best ? { backgroundColor: '#fff3e0' } : {}}
                    >
                      <td className="font-weight-medium">
                        {item.strategy_name}
                        {item.is_best && <span className="ml-2">🏆</span>}
                      </td>
                      <td className={`number-cell ${item.total_return >= 0 ? 'metric-positive' : 'metric-negative'}`}>
                        {item.total_return.toFixed(2)}%
                      </td>
                      <td className="number-cell metric-negative">
                        {item.mdd.toFixed(2)}%
                      </td>
                      <td className="number-cell">
                        {item.sharpe_ratio.toFixed(2)}
                      </td>
                      <td className="number-cell">
                        {item.win_rate.toFixed(1)}%
                      </td>
                      <td className="number-cell">
                        {item.profit_factor.toFixed(2)}
                      </td>
                      <td className="number-cell">
                        {item.total_trades}회 ({Math.floor(item.total_trades / 2)}쌍)
                      </td>
                      <td className="number-cell text-center font-weight-medium">
                        #{index + 1}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* 최소한의 커스텀 스타일 */}
      <style>{`
        .comparison-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        .backtest-list-section {
          margin-bottom: 40px;
        }

        .select-all {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-size: 14px;
          color: var(--color-text-secondary);
        }

        .ml-2 {
          margin-left: 8px;
        }

        .text-muted {
          color: var(--color-text-muted);
        }
        
        .text-secondary {
          color: var(--color-text-secondary);
        }
      `}</style>
    </PageLayout>
  );
};