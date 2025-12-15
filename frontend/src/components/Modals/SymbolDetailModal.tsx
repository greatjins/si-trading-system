/**
 * 종목 상세 모달 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { httpClient } from '../../services/http';
import { SymbolDetail, OHLC, TradeMarker, CompletedTrade } from '../../types/backtest';
import { PriceChart } from '../Charts';
import { TradeHistoryTable } from '../Tables';

interface SymbolDetailModalProps {
  /** 백테스트 ID */
  backtestId: string;
  /** 종목 코드 */
  symbol: string;
  /** 모달 닫기 핸들러 */
  onClose: () => void;
}

// 거래 데이터를 차트 마커로 변환하는 함수
const convertTradesToMarkers = (trades: any[]): TradeMarker[] => {
  return trades.map(trade => ({
    timestamp: trade.timestamp,
    price: trade.price,
    side: trade.side as 'buy' | 'sell',
    quantity: trade.quantity,
    pnl: undefined // 개별 거래에서는 P&L을 계산하지 않음
  }));
};

export const SymbolDetailModal: React.FC<SymbolDetailModalProps> = ({
  backtestId,
  symbol,
  onClose
}) => {
  const [symbolDetail, setSymbolDetail] = useState<SymbolDetail | null>(null);
  const [ohlcData, setOhlcData] = useState<OHLC[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chart' | 'trades'>('chart');
  const [selectedTradeIndex, setSelectedTradeIndex] = useState<number | undefined>(undefined);

  // 데이터 로드
  useEffect(() => {
    const loadSymbolData = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('🔍 종목 상세 데이터 로드 시작:', { backtestId, symbol });

        // 종목 상세 정보 로드
        const detailResponse = await httpClient.get(`/api/backtest/results/${backtestId}/symbols/${symbol}`);
        console.log('✅ 종목 상세 정보 로드 완료:', detailResponse.data);
        setSymbolDetail(detailResponse.data);

        // OHLC 데이터 로드 (별도 처리)
        try {
          const ohlcResponse = await httpClient.get(`/api/backtest/results/${backtestId}/ohlc/${symbol}`);
          console.log('✅ OHLC 데이터 로드 완료:', ohlcResponse.data.length, '개');
          setOhlcData(ohlcResponse.data);
        } catch (ohlcError: any) {
          console.warn('⚠️ OHLC 데이터 로드 실패:', ohlcError.response?.data?.detail || ohlcError.message);
          setOhlcData([]); // 빈 배열로 설정하여 차트 없이 진행
        }
      } catch (err: any) {
        console.error('❌ 종목 상세 데이터 로드 실패:', err);
        setError(err.response?.data?.detail || '종목 상세 정보를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadSymbolData();
  }, [backtestId, symbol]);

  // ESC 키 핸들러
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscKey);
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [onClose]);

  // 모달 외부 클릭 핸들러
  const handleOverlayClick = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  // 거래 클릭 핸들러 (차트 하이라이트용)
  const handleTradeClick = (trade: CompletedTrade, index: number) => {
    setSelectedTradeIndex(index);
    // 차트 탭으로 전환하여 해당 거래를 하이라이트
    setActiveTab('chart');
    // TODO: 차트에서 해당 거래 기간을 하이라이트하는 로직 추가
    console.log('거래 선택됨:', trade, '인덱스:', index);
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>📈 {symbol} 상세 분석</h3>
            <button onClick={onClose} className="close-btn">✕</button>
          </div>
          <div className="modal-body">
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>종목 상세 정보를 불러오는 중...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>📈 {symbol} 상세 분석</h3>
            <button onClick={onClose} className="close-btn">✕</button>
          </div>
          <div className="modal-body">
            <div className="error-container">
              <p className="error-message">{error}</p>
              <button onClick={onClose} className="btn btn-primary">
                닫기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 데이터 없음
  if (!symbolDetail) {
    return (
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>📈 {symbol} 상세 분석</h3>
            <button onClick={onClose} className="close-btn">✕</button>
          </div>
          <div className="modal-body">
            <div className="no-data-container">
              <p>종목 상세 정보가 없습니다.</p>
              <button onClick={onClose} className="btn btn-primary">
                닫기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content">
        {/* 모달 헤더 */}
        <div className="modal-header">
          <div className="symbol-info">
            <h3>📈 {symbolDetail.symbol} - {symbolDetail.name}</h3>
            <div className="symbol-metrics">
              <span className={`metric ${(symbolDetail.total_return ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                {(symbolDetail.total_return ?? 0).toFixed(2)}%
              </span>
              <span className="metric">
                {symbolDetail.trade_count ?? 0}회 거래
              </span>
              <span className="metric">
                승률 {(symbolDetail.win_rate ?? 0).toFixed(1)}%
              </span>
            </div>
          </div>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>

        {/* 탭 네비게이션 */}
        <div className="tab-navigation">
          <button 
            className={`tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
            onClick={() => setActiveTab('chart')}
          >
            📊 차트 분석
          </button>
          <button 
            className={`tab-btn ${activeTab === 'trades' ? 'active' : ''}`}
            onClick={() => setActiveTab('trades')}
          >
            📋 거래 내역
          </button>
        </div>

        {/* 모달 바디 */}
        <div className="modal-body">
          {activeTab === 'chart' && (
            <div className="chart-tab">
              {ohlcData === null ? (
                <div className="chart-placeholder">
                  <div className="loading-spinner"></div>
                  <h4>차트를 로딩 중...</h4>
                  <p>OHLC 데이터를 불러오는 중입니다.</p>
                </div>
              ) : ohlcData.length > 0 ? (
                <PriceChart
                  ohlcData={ohlcData}
                  trades={convertTradesToMarkers(symbolDetail.all_trades)}
                  symbol={symbolDetail.symbol}
                  height={500}
                />
              ) : (
                <div className="chart-placeholder">
                  <h4>⚠️ 가격 차트 데이터 없음</h4>
                  <p>해당 종목의 OHLC 데이터가 없습니다.</p>
                  <p>백테스트 기간: {symbolDetail ? `${symbolDetail.symbol}` : '확인 중...'}</p>
                  <small>데이터베이스에 해당 기간의 가격 데이터가 없을 수 있습니다.</small>
                </div>
              )}
              
              <div className="chart-info">
                <div className="info-grid">
                  <div className="info-row">
                    <span>평균 매수가:</span>
                    <span>{(symbolDetail.avg_buy_price ?? 0).toLocaleString()}원</span>
                  </div>
                  <div className="info-row">
                    <span>평균 매도가:</span>
                    <span>{(symbolDetail.avg_sell_price ?? 0).toLocaleString()}원</span>
                  </div>
                  <div className="info-row">
                    <span>평균 보유기간:</span>
                    <span>{(symbolDetail.avg_holding_days ?? 0).toFixed(1)}일</span>
                  </div>
                  <div className="info-row">
                    <span>총 거래 횟수:</span>
                    <span>{symbolDetail.all_trades.length}회</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'trades' && (
            <div className="trades-tab">
              <div className="trades-summary">
                <div className="summary-card">
                  <h4>거래 요약</h4>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span className="label">총 거래:</span>
                      <span className="value">{symbolDetail.trade_count}회</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">승률:</span>
                      <span className={`value ${(symbolDetail.win_rate ?? 0) >= 50 ? 'positive' : 'negative'}`}>
                        {(symbolDetail.win_rate ?? 0).toFixed(1)}%
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="label">손익비:</span>
                      <span className={`value ${(symbolDetail.profit_factor ?? 0) >= 1 ? 'positive' : 'negative'}`}>
                        {(symbolDetail.profit_factor ?? 0) >= 999 ? '∞' : (symbolDetail.profit_factor ?? 0).toFixed(2)}
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="label">총 손익:</span>
                      <span className={`value ${(symbolDetail.total_pnl ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                        {(symbolDetail.total_pnl ?? 0).toLocaleString()}원
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 거래 내역 테이블 */}
              <TradeHistoryTable
                trades={symbolDetail.completed_trades}
                onTradeClick={handleTradeClick}
                selectedTradeIndex={selectedTradeIndex}
              />
            </div>
          )}
        </div>
      </div>

      {/* 스타일 */}
      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          width: 100%;
          max-width: 1000px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
          box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 24px;
          border-bottom: 1px solid #e0e0e0;
        }

        .symbol-info h3 {
          margin: 0 0 8px 0;
          color: #333;
        }

        .symbol-metrics {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
        }

        .symbol-metrics .metric {
          font-size: 14px;
          padding: 4px 8px;
          background: #f5f5f5;
          border-radius: 4px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #666;
          padding: 4px;
          border-radius: 4px;
          transition: background-color 0.2s;
        }

        .close-btn:hover {
          background: #f0f0f0;
          color: #333;
        }

        .tab-navigation {
          display: flex;
          border-bottom: 1px solid #e0e0e0;
        }

        .tab-btn {
          flex: 1;
          padding: 16px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 16px;
          color: #666;
          transition: all 0.2s;
          border-bottom: 3px solid transparent;
        }

        .tab-btn:hover {
          background: #f8f9fa;
          color: #333;
        }

        .tab-btn.active {
          color: #2196f3;
          border-bottom-color: #2196f3;
          background: #f8f9fa;
        }

        .modal-body {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
        }

        .chart-placeholder {
          text-align: center;
          padding: 60px 20px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 2px dashed #ddd;
        }

        .chart-placeholder h4 {
          margin: 0 0 16px 0;
          color: #333;
        }

        .chart-info {
          margin-top: 24px;
          background: #f8f9fa;
          border-radius: 8px;
          padding: 20px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
        }

        .info-row span:first-child {
          color: #666;
          font-size: 14px;
        }

        .info-row span:last-child {
          font-weight: 600;
          color: #333;
        }

        .positive {
          color: #4caf50;
        }

        .negative {
          color: #f44336;
        }

        .loading-container,
        .error-container,
        .no-data-container {
          text-align: center;
          padding: 60px 20px;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #3498db;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          color: #f44336;
          margin-bottom: 20px;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: background-color 0.2s;
        }

        .btn-primary {
          background: #2196f3;
          color: white;
        }

        .btn-primary:hover {
          background: #1976d2;
        }

        @media (max-width: 768px) {
          .modal-content {
            margin: 10px;
            max-height: calc(100vh - 20px);
          }

          .modal-header {
            padding: 16px;
          }

          .symbol-metrics {
            flex-direction: column;
            gap: 8px;
          }

          .tab-btn {
            padding: 12px;
            font-size: 14px;
          }

          .modal-body {
            padding: 16px;
          }

          .summary-grid {
            grid-template-columns: 1fr;
          }

          .trades-table th,
          .trades-table td {
            padding: 8px;
            font-size: 14px;
          }
        }

        .trades-summary {
          margin-bottom: 24px;
        }

        .summary-card {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 20px;
        }

        .summary-card h4 {
          margin: 0 0 16px 0;
          color: #333;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .summary-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .summary-item .label {
          color: #666;
          font-size: 14px;
        }

        .summary-item .value {
          font-weight: 600;
          font-size: 16px;
        }

        .trades-table-container {
          overflow-x: auto;
        }

        .trades-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 800px;
        }

        .trades-table th,
        .trades-table td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #e0e0e0;
        }

        .trades-table th {
          background: #f8f9fa;
          font-weight: 600;
          color: #333;
          position: sticky;
          top: 0;
        }

        .trade-row {
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .trade-row:hover {
          background: #f8f9fa;
        }

        .trade-row.selected {
          background: #e3f2fd;
        }

        .no-trades {
          text-align: center;
          padding: 60px 20px;
          color: #666;
          background: #f8f9fa;
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
};