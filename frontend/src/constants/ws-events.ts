/**
 * WebSocket 이벤트 타입 상수
 */
export const WS_EVENTS = {
  // Client -> Server
  SUBSCRIBE: 'subscribe',
  UNSUBSCRIBE: 'unsubscribe',
  PING: 'ping',
  GET_PRICE: 'get_price',
  GET_ACCOUNT: 'get_account',
  
  // Server -> Client
  CONNECTED: 'connected',
  SUBSCRIBED: 'subscribed',
  UNSUBSCRIBED: 'unsubscribed',
  PONG: 'pong',
  PRICE: 'price',
  ACCOUNT: 'account',
  ORDER: 'order',
  ERROR: 'error',
} as const;

export type WSEventType = typeof WS_EVENTS[keyof typeof WS_EVENTS];
