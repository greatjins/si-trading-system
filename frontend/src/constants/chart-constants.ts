/**
 * 차트 관련 상수
 */
export const CHART_INTERVALS = {
  '1m': { label: '1분', value: '1m' },
  '5m': { label: '5분', value: '5m' },
  '15m': { label: '15분', value: '15m' },
  '30m': { label: '30분', value: '30m' },
  '1h': { label: '1시간', value: '1h' },
  '1d': { label: '1일', value: '1d' },
} as const;

export type ChartInterval = keyof typeof CHART_INTERVALS;

export const CHART_COLORS = {
  UP: '#1a7f37',
  DOWN: '#cf222e',
  BACKGROUND: '#ffffff',
  GRID: '#e1e4e8',
  TEXT: '#24292f',
} as const;
