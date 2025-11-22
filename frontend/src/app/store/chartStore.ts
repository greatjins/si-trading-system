/**
 * 차트 상태 관리 (Zustand)
 */
import { create } from 'zustand';

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartState {
  symbol: string;
  interval: '1m' | '5m' | '15m' | '30m' | '1h' | '1d';
  candles: Candle[];
  isLoading: boolean;
  error: string | null;
  setSymbol: (symbol: string) => void;
  setInterval: (interval: ChartState['interval']) => void;
  setCandles: (candles: Candle[]) => void;
  addCandle: (candle: Candle) => void;
  updateLastCandle: (candle: Candle) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useChartStore = create<ChartState>((set) => ({
  symbol: '005930',
  interval: '1d',
  candles: [],
  isLoading: false,
  error: null,
  
  setSymbol: (symbol) => set({ symbol }),
  setInterval: (interval) => set({ interval }),
  setCandles: (candles) => set({ candles, error: null }),
  
  addCandle: (candle) =>
    set((state) => ({
      candles: [...state.candles, candle],
    })),
  
  updateLastCandle: (candle) =>
    set((state) => ({
      candles: state.candles.length > 0
        ? [...state.candles.slice(0, -1), candle]
        : [candle],
    })),
  
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ candles: [], isLoading: false, error: null }),
}));
