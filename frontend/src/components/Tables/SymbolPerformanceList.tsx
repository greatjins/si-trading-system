/**
 * 종목별 성과 리스트 컴포넌트
 */
import React, { useState } from 'react';
import { SymbolPerformance } from '../../types/backtest';
import styles from './SymbolPerformanceList.module.css';

type SortField = 'symbol' | 'name' | 'total_return' | 'trade_count' | 'win_rate' | 'profit_factor' | 'total_pnl';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

interface SymbolPerformanceListProps {
  /** 종목별 성과 데이터 */
  performances: SymbolPerformance[];
  /** 종목 클릭 핸들러 */
  onSymbolClick: (symbol: string) => void;
  /** 로딩 상태 */
  loading?: boolean;
}

export const SymbolPerformanceList: React.FC<SymbolPerformanceListProps> = ({
  performances,
  onSymbolClick,
  loading = false
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'total_return',
    direction: 'desc'
  });

  // 정렬 핸들러
  const handleSort = (field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  // 데이터 정렬
  const sortedPerformances = React.useMemo(() => {
    if (!performances || performances.length === 0) return [];

    return [...performances].sort((a, b) => {
      const { field, direction } = sortConfig;
      let aValue = a[field];
      let bValue = b[field];

      // 문자열 정렬
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) {
        return direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [performances, sortConfig]);

  // 정렬 아이콘 렌더링
  const renderSortIcon = (field: SortField) => {
    if (sortConfig.field !== field) {
      return <span className={styles.sortIcon}>↕️</span>;
    }
    return (
      <span className={`${styles.sortIcon} active`}>
        {sortConfig.direction === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className={styles.performanceListContainer}>
        <div className={styles.loadingMessage}>
          종목별 성과를 불러오는 중...
        </div>
      </div>
    );
  }

  // 데이터 없음
  if (!performances || performances.length === 0) {
    return (
      <div className={styles.performanceListContainer}>
        <div className={styles.noDataMessage}>
          거래된 종목이 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className={styles.performanceListContainer}>
      <div className={styles.tableWrapper}>
        <table className={styles.performanceTable}>
          <thead>
            <tr>
              <th 
                className={styles.sortableHeader}
                onClick={() => handleSort('symbol')}
              >
                종목코드 {renderSortIcon('symbol')}
              </th>
              <th 
                className={styles.sortableHeader}
                onClick={() => handleSort('name')}
              >
                종목명 {renderSortIcon('name')}
              </th>
              <th 
                className={`${styles.sortableHeader} ${styles.numberColumn}`}
                onClick={() => handleSort('total_return')}
              >
                수익률 {renderSortIcon('total_return')}
              </th>
              <th 
                className={`${styles.sortableHeader} ${styles.numberColumn}`}
                onClick={() => handleSort('trade_count')}
              >
                거래횟수 {renderSortIcon('trade_count')}
              </th>
              <th 
                className={`${styles.sortableHeader} ${styles.numberColumn}`}
                onClick={() => handleSort('win_rate')}
              >
                승률 {renderSortIcon('win_rate')}
              </th>
              <th 
                className={`${styles.sortableHeader} ${styles.numberColumn}`}
                onClick={() => handleSort('profit_factor')}
              >
                손익비 {renderSortIcon('profit_factor')}
              </th>
              <th 
                className={`${styles.sortableHeader} ${styles.numberColumn}`}
                onClick={() => handleSort('total_pnl')}
              >
                총손익 {renderSortIcon('total_pnl')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedPerformances.map((performance) => (
              <tr 
                key={performance.symbol}
                className={styles.performanceRow}
                onClick={() => onSymbolClick(performance.symbol)}
              >
                <td className={styles.symbolCell}>
                  <span className={styles.symbolCode}>{performance.symbol}</span>
                </td>
                <td className={styles.nameCell}>
                  <span className={styles.symbolName}>{performance.name}</span>
                </td>
                <td className={`${styles.numberCell} ${performance.total_return >= 0 ? styles.positive : styles.negative}`}>
                  {performance.total_return.toFixed(2)}%
                </td>
                <td className={styles.numberCell}>
                  {performance.trade_count}회
                </td>
                <td className={styles.numberCell}>
                  <span className={performance.win_rate >= 50 ? styles.goodRate : styles.poorRate}>
                    {performance.win_rate.toFixed(1)}%
                  </span>
                </td>
                <td className={styles.numberCell}>
                  <span className={performance.profit_factor >= 1 ? styles.goodRatio : styles.poorRatio}>
                    {performance.profit_factor.toFixed(2)}
                  </span>
                </td>
                <td className={`${styles.numberCell} ${performance.total_pnl >= 0 ? styles.positive : styles.negative}`}>
                  {performance.total_pnl.toLocaleString()}원
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 요약 정보 */}
      <div className={styles.summaryInfo}>
        <div className={styles.summaryItem}>
          <span className="label">총 종목 수:</span>
          <span className="value">{performances.length}개</span>
        </div>
        <div className={styles.summaryItem}>
          <span className="label">수익 종목:</span>
          <span className={`value ${styles.positive}`}>
            {performances.filter(p => p.total_return > 0).length}개
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className="label">손실 종목:</span>
          <span className={`value ${styles.negative}`}>
            {performances.filter(p => p.total_return < 0).length}개
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className="label">평균 수익률:</span>
          <span className={`value ${performances.reduce((sum, p) => sum + p.total_return, 0) / performances.length >= 0 ? styles.positive : styles.negative}`}>
            {(performances.reduce((sum, p) => sum + p.total_return, 0) / performances.length).toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );
};