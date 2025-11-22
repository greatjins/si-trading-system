/**
 * 계좌 상태 관리 (Zustand)
 */
import { create } from 'zustand';

export interface Account {
  account_id: string;
  balance: number;
  equity: number;
  margin_used: number;
  margin_available: number;
}

interface AccountState {
  account: Account | null;
  isLoading: boolean;
  error: string | null;
  setAccount: (account: Account) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAccountStore = create<AccountState>((set) => ({
  account: null,
  isLoading: false,
  error: null,
  setAccount: (account) => set({ account, error: null }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ account: null, isLoading: false, error: null }),
}));
