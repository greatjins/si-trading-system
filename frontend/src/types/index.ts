// API 타입 정의

export interface OHLCData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface PriceData {
  symbol: string
  price: number
  open: number
  high: number
  low: number
  volume: number
  timestamp: string
}

export interface AccountInfo {
  account_id: string
  balance: number
  equity: number
  margin_used: number
  margin_available: number
}

export interface Order {
  order_id: string
  symbol: string
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  quantity: number
  price?: number
  status: string
  created_at: string
}

export interface Position {
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  pnl: number
  pnl_percent: number
}

export interface WebSocketMessage {
  type: string
  [key: string]: any
}
