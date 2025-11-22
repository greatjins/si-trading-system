/**
 * 포맷팅 유틸리티
 */

/**
 * 숫자를 통화 형식으로 포맷
 */
export const formatCurrency = (value: number, currency = 'KRW'): string => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * 숫자를 천단위 구분자로 포맷
 */
export const formatNumber = (value: number, decimals = 0): string => {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * 퍼센트 포맷
 */
export const formatPercent = (value: number, decimals = 2): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

/**
 * 변화율 계산 및 포맷
 */
export const formatChange = (current: number, previous: number): string => {
  const change = ((current - previous) / previous) * 100;
  return formatPercent(change);
};

/**
 * 대용량 숫자를 축약 (1K, 1M, 1B)
 */
export const formatCompactNumber = (value: number): string => {
  return new Intl.NumberFormat('ko-KR', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};
