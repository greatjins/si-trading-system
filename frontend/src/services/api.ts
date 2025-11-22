import axios from 'axios'
import type { OHLCData, PriceData, AccountInfo, Order } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 인터셉터: 토큰 자동 추가
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 인증
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  register: async (username: string, email: string, password: string) => {
    const response = await api.post('/api/auth/register', {
      username,
      email,
      password,
    })
    return response.data
  },
}

// 시세
export const priceAPI = {
  getOHLC: async (symbol: string, interval: string = '1d', limit: number = 100) => {
    const response = await api.get<{ data: OHLCData[] }>(`/api/price/${symbol}/ohlc`, {
      params: { interval, limit },
    })
    return response.data.data
  },
  
  getCurrentPrice: async (symbol: string) => {
    const response = await api.get<PriceData>(`/api/price/${symbol}/current`)
    return response.data
  },
  
  getSymbols: async () => {
    const response = await api.get<{ symbols: string[] }>('/api/price/symbols')
    return response.data.symbols
  },
}

// 계좌
export const accountAPI = {
  getAccount: async () => {
    const response = await api.get<AccountInfo>('/api/account')
    return response.data
  },
  
  getPositions: async () => {
    const response = await api.get('/api/account/positions')
    return response.data
  },
}

// 주문
export const orderAPI = {
  placeOrder: async (order: {
    symbol: string
    side: 'buy' | 'sell'
    quantity: number
    order_type: 'market' | 'limit'
    price?: number
  }) => {
    const response = await api.post<Order>('/api/orders', order)
    return response.data
  },
  
  getOrders: async () => {
    const response = await api.get<Order[]>('/api/orders')
    return response.data
  },
  
  cancelOrder: async (orderId: string) => {
    const response = await api.delete(`/api/orders/${orderId}`)
    return response.data
  },
}

export default api
