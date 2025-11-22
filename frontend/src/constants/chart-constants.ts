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
  UP: '#26a69a',
  DOWN: '#ef5350',
  BACKGROUND: '#1e222d',
  GRID: '#2a2e39',
  TEXT: '#d1d4dc',
} as const;
