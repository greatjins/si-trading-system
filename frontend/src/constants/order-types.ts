/**
 * 주문 관련 상수
 */
export const ORDER_SIDE = {
  BUY: 'buy',
  SELL: 'sell',
} as const;

export const ORDER_TYPE = {
  MARKET: 'market',
  LIMIT: 'limit',
} as const;

export const ORDER_STATUS = {
  SUBMITTED: 'submitted',
  PENDING: 'pending',
  FILLED: 'filled',
  CANCELLED: 'cancelled',
  REJECTED: 'rejected',
} as const;

export type OrderSide = typeof ORDER_SIDE[keyof typeof ORDER_SIDE];
export type OrderType = typeof ORDER_TYPE[keyof typeof ORDER_TYPE];
export type OrderStatus = typeof ORDER_STATUS[keyof typeof ORDER_STATUS];
