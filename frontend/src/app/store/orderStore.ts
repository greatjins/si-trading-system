/**
 * 주문 상태 관리 (Zustand)
 */
import { create } from 'zustand';

export interface Order {
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: number;
  price?: number;
  status: string;
  created_at: string;
}

interface OrderState {
  orders: Order[];
  activeOrders: Order[];
  isLoading: boolean;
  error: string | null;
  addOrder: (order: Order) => void;
  updateOrder: (orderId: string, updates: Partial<Order>) => void;
  removeOrder: (orderId: string) => void;
  setOrders: (orders: Order[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useOrderStore = create<OrderState>((set) => ({
  orders: [],
  activeOrders: [],
  isLoading: false,
  error: null,
  
  addOrder: (order) =>
    set((state) => ({
      orders: [order, ...state.orders],
      activeOrders: order.status === 'submitted' || order.status === 'pending'
        ? [order, ...state.activeOrders]
        : state.activeOrders,
    })),
  
  updateOrder: (orderId, updates) =>
    set((state) => ({
      orders: state.orders.map((o) =>
        o.order_id === orderId ? { ...o, ...updates } : o
      ),
      activeOrders: state.activeOrders.map((o) =>
        o.order_id === orderId ? { ...o, ...updates } : o
      ),
    })),
  
  removeOrder: (orderId) =>
    set((state) => ({
      orders: state.orders.filter((o) => o.order_id !== orderId),
      activeOrders: state.activeOrders.filter((o) => o.order_id !== orderId),
    })),
  
  setOrders: (orders) =>
    set({
      orders,
      activeOrders: orders.filter(
        (o) => o.status === 'submitted' || o.status === 'pending'
      ),
    }),
  
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  reset: () => set({ orders: [], activeOrders: [], isLoading: false, error: null }),
}));
