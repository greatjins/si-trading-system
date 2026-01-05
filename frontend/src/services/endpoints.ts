/**
 * API 엔드포인트 정의
 */
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: `${API_BASE}/api/auth/login`,
    LOGOUT: `${API_BASE}/api/auth/logout`,
    REFRESH: `${API_BASE}/api/auth/refresh`,
  },
  
  // Account
  ACCOUNT: {
    INFO: `${API_BASE}/api/account`,
    POSITIONS: `${API_BASE}/api/account/positions`,
  },
  
  // Orders
  ORDERS: {
    LIST: `${API_BASE}/api/orders`,
    CREATE: `${API_BASE}/api/orders/`,
    GET: (orderId: string) => `${API_BASE}/api/orders/${orderId}`,
    CANCEL: (orderId: string) => `${API_BASE}/api/orders/${orderId}`,
  },
  
  // Price
  PRICE: {
    OHLC: (symbol: string) => `${API_BASE}/api/price/${symbol}/ohlc`,
    CURRENT: (symbol: string) => `${API_BASE}/api/price/${symbol}/current`,
    SYMBOLS: `${API_BASE}/api/price/symbols`,
  },
  
  // Strategy
  STRATEGY: {
    LIST: `${API_BASE}/api/strategies/list`,
    START: `${API_BASE}/api/strategy/start`,
    STOP: `${API_BASE}/api/strategy/stop`,
    STATUS: `${API_BASE}/api/strategy/status`,
  },
  
  // Backtest
  BACKTEST: {
    RUN: `${API_BASE}/api/backtest/run`,
    PORTFOLIO: `${API_BASE}/api/backtest/portfolio`,
    RESULTS: `${API_BASE}/api/backtest/results`,
  },
  
  // WebSocket
  WS: {
    CONNECT: (token: string) => `${WS_BASE}/api/ws?token=${token}`,
  },
} as const;
