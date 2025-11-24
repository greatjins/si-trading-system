/**
 * 계좌 상태 관리 (Zustand)
 */
import { create } from 'zustand';

export interface AccountBalance {
  account_id: number;
  account_number: string;
  broker: string;
  balance: number;
  equity: number;
  margin_used: number;
  margin_available: number;
  buying_power: number;
  positions: Array<{
    symbol: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    unrealized_pnl: number;
    realized_pnl: number;
  }>;
}

interface AccountState {
  selectedAccountId: number | null;
  accountBalance: AccountBalance | null;
  isLoading: boolean;
  error: string | null;
  setSelectedAccountId: (accountId: number | null) => void;
  setAccountBalance: (balance: AccountBalance | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAccountStore = create<AccountState>((set) => ({
  selectedAccountId: null,
  accountBalance: null,
  isLoading: false,
  error: null,
  setSelectedAccountId: (selectedAccountId) => set({ selectedAccountId }),
  setAccountBalance: (accountBalance) => set({ accountBalance, error: null, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ selectedAccountId: null, accountBalance: null, isLoading: false, error: null }),
}));
