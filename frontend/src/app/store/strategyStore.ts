/**
 * 전략 상태 관리
 */
import { create } from 'zustand';

export interface SavedStrategy {
  id: string;
  name: string;
  description: string;
  config: any;
  created_at: string;
  backtest_results?: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
  };
}

interface StrategyStore {
  strategies: SavedStrategy[];
  selectedStrategy: SavedStrategy | null;
  
  // Actions
  setStrategies: (strategies: SavedStrategy[]) => void;
  addStrategy: (strategy: SavedStrategy) => void;
  selectStrategy: (strategy: SavedStrategy | null) => void;
  updateStrategy: (id: string, updates: Partial<SavedStrategy>) => void;
  deleteStrategy: (id: string) => void;
}

export const useStrategyStore = create<StrategyStore>((set) => ({
  strategies: [],
  selectedStrategy: null,
  
  setStrategies: (strategies) => set({ strategies }),
  
  addStrategy: (strategy) =>
    set((state) => ({
      strategies: [...state.strategies, strategy],
    })),
  
  selectStrategy: (strategy) => set({ selectedStrategy: strategy }),
  
  updateStrategy: (id, updates) =>
    set((state) => ({
      strategies: state.strategies.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),
  
  deleteStrategy: (id) =>
    set((state) => ({
      strategies: state.strategies.filter((s) => s.id !== id),
      selectedStrategy:
        state.selectedStrategy?.id === id ? null : state.selectedStrategy,
    })),
}));
