/**
 * 주문 API 서비스
 */
import { httpClient } from '../../../services/http';
import { ENDPOINTS } from '../../../services/endpoints';
import { Order } from '../../../app/store/orderStore';

export interface CreateOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: number;
  price?: number;
}

/**
 * 주문 생성
 */
export const createOrder = async (request: CreateOrderRequest): Promise<Order> => {
  const response = await httpClient.post<Order>(ENDPOINTS.ORDERS.CREATE, request);
  return response.data;
};

/**
 * 주문 목록 조회
 */
export const fetchOrders = async (): Promise<Order[]> => {
  const response = await httpClient.get<Order[]>(ENDPOINTS.ORDERS.LIST);
  return response.data;
};

/**
 * 주문 취소
 */
export const cancelOrder = async (orderId: string): Promise<void> => {
  await httpClient.delete(ENDPOINTS.ORDERS.CANCEL(orderId));
};

/**
 * 주문 상세 조회
 */
export const fetchOrder = async (orderId: string): Promise<Order> => {
  const response = await httpClient.get<Order>(ENDPOINTS.ORDERS.GET(orderId));
  return response.data;
};
