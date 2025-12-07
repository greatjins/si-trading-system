/**
 * 데이터 수집 페이지
 */
import { useState, useEffect } from 'react';
import { PageLayout } from '../components/Layout/PageLayout';

interface CollectionStatus {
  is_running: boolean;
  current_symbol: string | null;
  progress: number;
  total: number;
  logs: string[];
  start_time: string | null;
  error: string | null;
}

interface Stock {
  symbol: string;
  name: string;
  market: string;
  current_price: number;
  volume_amount: number;
  price_position: number;
  updated_at: string;
}

interface DataStats {
  stock_count: number;
  ohlc_count: number;
  last_updated: string | null;
}

export default function DataCollection() {
  const [status, setStatus] = useState<CollectionStatus>({
    is_running: false,
    current_symbol: null,
    progress: 0,
    total: 0,
    logs: [],
    start_time: null,
    error: null,
  });
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [stats, setStats] = useState<DataStats>({
    stock_count: 0,
    ohlc_count: 0,
    last_updated: null,
  });
  const [count, setCount] = useState(200);
  const [days, setDays] = useState(180);
  const [page, setPage] = useState(1);
  const [totalStocks, setTotalStocks] = useState(0);
  const itemsPerPage = 50;

  // 상태 폴링
  useEffect(() => {
    let wasRunning = false;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/data/collect/status');
        const data = await res.json();
        
        // 수집이 완료되면 자동 새로고침
        if (wasRunning && !data.is_running) {
          loadStocks();
          loadStats();
        }
        
        wasRunning = data.is_running;
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // 초기 데이터 로드
  useEffect(() => {
    loadStocks();
    loadStats();
  }, []);

  const loadStocks = async (pageNum: number = page) => {
    try {
      const offset = (pageNum - 1) * itemsPerPage;
      const res = await fetch(`/api/data/stocks?limit=${itemsPerPage}&offset=${offset}`);
      const data = await res.json();
      setStocks(data.stocks);
      setTotalStocks(data.total);
    } catch (error) {
      console.error('Failed to load stocks:', error);
    }
  };

  const loadStats = async () => {
    try {
      const res = await fetch('/api/data/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleStart = async () => {
    try {
      await fetch('/api/data/collect/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count, days }),
      });
    } catch (error) {
      console.error('Failed to start collection:', error);
    }
  };

  const handleStop = async () => {
    try {
      await fetch('/api/data/collect/stop', { method: 'POST' });
    } catch (error) {
      console.error('Failed to stop collection:', error);
    }
  };

  const handleRefresh = () => {
    loadStocks(page);
    loadStats();
  };

  const handlePrevPage = () => {
    if (page > 1) {
      const newPage = page - 1;
      setPage(newPage);
      loadStocks(newPage);
    }
  };

  const handleNextPage = () => {
    const totalPages = Math.ceil(totalStocks / itemsPerPage);
    if (page < totalPages) {
      const newPage = page + 1;
      setPage(newPage);
      loadStocks(newPage);
    }
  };

  const progress = status.total > 0 ? (status.progress / status.total) * 100 : 0;

  return (
    <PageLayout title="데이터 수집" description="LS증권 API를 통해 시장 데이터를 수집합니다">
      <div className="data-collection-content">
        
        {/* 통계 카드 */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">수집된 종목</div>
            <div className="stat-value">{stats.stock_count}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">OHLC 데이터</div>
            <div className="stat-value">{stats.ohlc_count.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">마지막 업데이트</div>
            <div className="stat-value-small">
              {stats.last_updated
                ? new Date(stats.last_updated).toLocaleString('ko-KR')
                : '-'}
            </div>
          </div>
        </div>

        {/* 수집 컨트롤 */}
        <div className="builder-section">
          <h2>데이터 수집 설정</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label>수집 종목 수</label>
              <input
                type="number"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                disabled={status.is_running}
                className="form-input"
                min="1"
                max="500"
              />
              <small>거래대금 상위 종목 (최대 500)</small>
            </div>
            
            <div className="form-group">
              <label>수집 기간 (일)</label>
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                disabled={status.is_running}
                className="form-input"
                min="30"
                max="365"
              />
              <small>최근 N일 데이터 (권장: 180일)</small>
            </div>
          </div>

          <div className="button-group">
            <button
              className="btn btn-primary"
              onClick={handleStart}
              disabled={status.is_running}
            >
              ▶ 수집 시작
            </button>
            <button
              className="btn btn-danger"
              onClick={handleStop}
              disabled={!status.is_running}
            >
              ■ 중지
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleRefresh}
            >
              🔄 새로고침
            </button>
          </div>

          {/* 진행 상태 */}
          {status.is_running && (
            <div className="progress-section">
              <div className="progress-info">
                <span>{status.current_symbol || '준비 중...'}</span>
                <span>{status.progress} / {status.total} ({progress.toFixed(1)}%)</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* 에러 */}
          {status.error && (
            <div className="error-message">
              ❌ {status.error}
            </div>
          )}
        </div>

        {/* 로그 */}
        <div className="builder-section">
          <h2>수집 로그</h2>
          <div className="log-container">
            {status.logs.length === 0 ? (
              <div className="log-empty">로그가 없습니다</div>
            ) : (
              status.logs.map((log, idx) => (
                <div key={idx} className="log-line">{log}</div>
              ))
            )}
          </div>
        </div>

        {/* 종목 목록 */}
        <div className="builder-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2>수집된 종목 목록</h2>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                className="btn btn-secondary"
                onClick={handlePrevPage}
                disabled={page === 1}
                style={{ padding: '6px 12px' }}
              >
                ◀ 이전
              </button>
              <span style={{ padding: '0 12px', color: '#666' }}>
                {page} / {Math.ceil(totalStocks / itemsPerPage) || 1} 페이지 (총 {totalStocks}개)
              </span>
              <button
                className="btn btn-secondary"
                onClick={handleNextPage}
                disabled={page >= Math.ceil(totalStocks / itemsPerPage)}
                style={{ padding: '6px 12px' }}
              >
                다음 ▶
              </button>
            </div>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>종목코드</th>
                  <th>종목명</th>
                  <th>시장</th>
                  <th style={{ textAlign: 'right' }}>현재가</th>
                  <th style={{ textAlign: 'right' }}>거래대금</th>
                  <th style={{ textAlign: 'right' }}>가격위치</th>
                  <th>업데이트</th>
                </tr>
              </thead>
              <tbody>
                {stocks.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                      수집된 종목이 없습니다
                    </td>
                  </tr>
                ) : (
                  stocks.map((stock) => (
                    <tr key={stock.symbol}>
                      <td>{stock.symbol}</td>
                      <td>{stock.name}</td>
                      <td>
                        <span className={`badge ${stock.market === 'KOSPI' ? 'badge-primary' : 'badge-secondary'}`}>
                          {stock.market}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {stock.current_price?.toLocaleString()}원
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {(stock.volume_amount / 100000000).toLocaleString('ko-KR', { maximumFractionDigits: 0 })}억
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {(stock.price_position * 100).toFixed(1)}%
                      </td>
                      <td>
                        {new Date(stock.updated_at).toLocaleDateString('ko-KR')}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
