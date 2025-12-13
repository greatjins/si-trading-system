/**
 * 거래 내역 테이블 컴포넌트
 */
import React, { useState } from 'react';
import { CompletedTrade } from '../../types/backtest';

interface TradeHistoryTableProps {
  /** 완결된 거래 목록 */
  trades: CompletedTrade[];
  /** 거래 클릭 핸들러 */
  onTradeClick?: (trade: CompletedTrade, index: number) => void;
  /** 선택된 거래 인덱스 */
  selectedTradeIndex?: number;
}

type SortField = 'entry_date' | 'exit_date' | 'return_pct' | 'pnl' | 'holding_period';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

export const TradeHistoryTable: React.FC<TradeHistoryTableProps> = ({
  trades,
  onTradeClick,
  selectedTradeIndex
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'entry_date',
    direction: 'desc'
  });

  // 정렬 함수
  const handleSort = (field: SortField) => {
    const direction = 
      sortConfig.field === field && sortConfig.direction === 'asc' 
        ? 'desc' 
        : 'asc';
    
    setSortConfig({ field, direction });
  };

  // 정렬된 거래 목록
  const sortedTrades = [...trades].sort((a, b) => {
    const { field, direction } = sortConfig;
    let aValue: any = a[field];
    let bValue: any = b[field];

    // 날짜 필드는 Date 객체로 변환
    if (field === 'entry_date' || field === 'exit_date') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    }

    if (aValue < bValue) {
      return direction === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // 정렬 아이콘 렌더링
  const renderSortIcon = (field: SortField) => {
    if (sortConfig.field !== field) {
      return <span className="sort-icon">↕️</span>;
    }
    return (
      <span className="sort-icon active">
        {sortConfig.direction === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  // 거래 행 클릭 핸들러
  const handleTradeClick = (trade: CompletedTrade, index: number) => {
    if (onTradeClick) {
      onTradeClick(trade, index);
    }
  };

  // 빈 상태
  if (trades.length === 0) {
    return (
      <div className="trade-history-empty">
        <div className="empty-icon">📊</div>
        <h3>완결된 거래가 없습니다</h3>
        <p>아직 청산된 거래가 없거나 백테스트가 진행 중입니다.</p>
      </div>
    );
  }

  return (
    <div className="trade-history-table">
      <div className="table-header">
        <h3>거래 내역</h3>
        <div className="table-stats">
          <span className="stat">
            총 {trades.length}건
          </span>
          <span className="stat">
            수익: {trades.filter(t => t.pnl > 0).length}건
          </span>
          <span className="stat">
            손실: {trades.filter(t => t.pnl < 0).length}건
          </span>
        </div>
      </div>

      <div className="table-container">
        <table className="trades-table">
          <thead>
            <tr>
              <th>#</th>
              <th 
                className="sortable"
                onClick={() => handleSort('entry_date')}
              >
                진입일 {renderSortIcon('entry_date')}
              </th>
              <th 
                className="sortable"
                onClick={() => handleSort('exit_date')}
              >
                청산일 {renderSortIcon('exit_date')}
              </th>
              <th>매수가</th>
              <th>매도가</th>
              <th>수량</th>
              <th 
                className="sortable"
                onClick={() => handleSort('return_pct')}
              >
                수익률 {renderSortIcon('return_pct')}
              </th>
              <th 
                className="sortable"
                onClick={() => handleSort('pnl')}
              >
                손익 {renderSortIcon('pnl')}
              </th>
              <th 
                className="sortable"
                onClick={() => handleSort('holding_period')}
              >
                보유기간 {renderSortIcon('holding_period')}
              </th>
              <th>수수료</th>
            </tr>
          </thead>
          <tbody>
            {sortedTrades.map((trade, index) => (
              <tr 
                key={index}
                className={`trade-row ${selectedTradeIndex === index ? 'selected' : ''} ${onTradeClick ? 'clickable' : ''}`}
                onClick={() => handleTradeClick(trade, index)}
              >
                <td className="trade-number">{index + 1}</td>
                <td className="date-cell">
                  {new Date(trade.entry_date).toLocaleDateString('ko-KR')}
                </td>
                <td className="date-cell">
                  {new Date(trade.exit_date).toLocaleDateString('ko-KR')}
                </td>
                <td className="price-cell">
                  ₩{trade.entry_price.toLocaleString()}
                </td>
                <td className="price-cell">
                  ₩{trade.exit_price.toLocaleString()}
                </td>
                <td className="quantity-cell">
                  {trade.entry_quantity.toLocaleString()}주
                </td>
                <td className={`return-cell ${trade.return_pct >= 0 ? 'positive' : 'negative'}`}>
                  {trade.return_pct >= 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%
                </td>
                <td className={`pnl-cell ${trade.pnl >= 0 ? 'positive' : 'negative'}`}>
                  {trade.pnl >= 0 ? '+' : ''}₩{trade.pnl.toLocaleString()}
                </td>
                <td className="holding-cell">
                  {trade.holding_period}일
                </td>
                <td className="commission-cell">
                  ₩{trade.commission.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style>{`
        .trade-history-table {
          width: 100%;
        }

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 2px solid #e0e0e0;
        }

        .table-header h3 {
          margin: 0;
          color: #333;
          font-size: 18px;
        }

        .table-stats {
          display: flex;
          gap: 16px;
        }

        .table-stats .stat {
          font-size: 14px;
          color: #666;
          background: #f5f5f5;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .table-container {
          overflow-x: auto;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
        }

        .trades-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 1000px;
          background: white;
        }

        .trades-table th {
          background: #f8f9fa;
          padding: 12px 8px;
          text-align: left;
          font-weight: 600;
          color: #333;
          border-bottom: 2px solid #e0e0e0;
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .trades-table th.sortable {
          cursor: pointer;
          user-select: none;
          transition: background-color 0.2s;
        }

        .trades-table th.sortable:hover {
          background: #e9ecef;
        }

        .sort-icon {
          margin-left: 4px;
          font-size: 12px;
          opacity: 0.6;
        }

        .sort-icon.active {
          opacity: 1;
          color: #2196f3;
        }

        .trades-table td {
          padding: 10px 8px;
          border-bottom: 1px solid #f0f0f0;
          font-size: 14px;
        }

        .trade-row {
          transition: background-color 0.2s;
        }

        .trade-row:hover {
          background: #f8f9fa;
        }

        .trade-row.clickable {
          cursor: pointer;
        }

        .trade-row.selected {
          background: #e3f2fd;
          border-left: 4px solid #2196f3;
        }

        .trade-number {
          font-weight: 600;
          color: #666;
          text-align: center;
          width: 50px;
        }

        .date-cell {
          font-family: monospace;
          font-size: 13px;
          color: #555;
        }

        .price-cell,
        .quantity-cell,
        .commission-cell {
          text-align: right;
          font-family: monospace;
          font-size: 13px;
        }

        .return-cell,
        .pnl-cell {
          text-align: right;
          font-weight: 600;
          font-family: monospace;
        }

        .return-cell.positive,
        .pnl-cell.positive {
          color: #4caf50;
        }

        .return-cell.negative,
        .pnl-cell.negative {
          color: #f44336;
        }

        .holding-cell {
          text-align: center;
          font-family: monospace;
          font-size: 13px;
        }

        .trade-history-empty {
          text-align: center;
          padding: 60px 20px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 2px dashed #ddd;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .trade-history-empty h3 {
          margin: 0 0 8px 0;
          color: #333;
        }

        .trade-history-empty p {
          margin: 0;
          color: #666;
          font-size: 14px;
        }

        /* 반응형 디자인 */
        @media (max-width: 768px) {
          .table-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
          }

          .table-stats {
            flex-wrap: wrap;
            gap: 8px;
          }

          .trades-table th,
          .trades-table td {
            padding: 8px 4px;
            font-size: 12px;
          }

          .trades-table {
            min-width: 800px;
          }
        }

        /* 프린트 스타일 */
        @media print {
          .trade-history-table {
            break-inside: avoid;
          }

          .trades-table th,
          .trades-table td {
            border: 1px solid #000;
            padding: 6px;
          }

          .trade-row:hover {
            background: none;
          }
        }
      `}</style>
    </div>
  );
};