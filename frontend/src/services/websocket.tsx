/**
 * WebSocket 클라이언트 및 Provider
 */
import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';

// WebSocket URL 자동 감지
const getWebSocketUrl = () => {
  // 1. 환경변수가 있으면 사용 (강제 지정)
  const envWsUrl = (import.meta as any).env?.VITE_WS_URL;
  if (envWsUrl) {
    console.log('WS_BASE_URL:', envWsUrl, '(환경변수 사용)');
    return envWsUrl;
  }
  
  // 2. 현재 호스트 자동 감지
  const currentHost = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // localhost면 프론트엔드 포트(3000) 사용 (Vite 프록시)
  // 외부 접근이면 백엔드 포트(8000) 사용
  let port = '8000';
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    port = window.location.port || '3000';
    console.log('WS_BASE_URL:', `${protocol}//${currentHost}:${port}`, '(로컬 - Vite 프록시)');
  } else {
    console.log('WS_BASE_URL:', `${protocol}//${currentHost}:${port}`, '(외부 - 직접 연결)');
  }
  
  return `${protocol}//${currentHost}:${port}`;
};

const WS_BASE_URL = getWebSocketUrl();

interface WebSocketContextType {
  isConnected: boolean;
  sendMessage: (message: any) => void;
  subscribe: (topic: string, handler: (message: any) => void) => void;
  unsubscribe: (topic: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }: { children: ReactNode }) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [subscriptions, setSubscriptions] = useState<Map<string, Set<(message: any) => void>>>(
    new Map()
  );
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.log('No access token found');
      return;
    }
    
    const url = `${WS_BASE_URL}/api/ws?token=${token}`;
    console.log('Connecting to WebSocket:', url);
    
    const websocket = new WebSocket(url);
    
    websocket.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
    };
    
    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('📨 WebSocket message:', message);
        
        // 토픽별 핸들러 실행
        if (message.topic) {
          const handlers = subscriptions.get(message.topic);
          if (handlers) {
            handlers.forEach((handler) => handler(message));
          }
        }
        
        // 전역 핸들러 실행
        const globalHandlers = subscriptions.get('*');
        if (globalHandlers) {
          globalHandlers.forEach((handler) => handler(message));
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };
    
    websocket.onclose = (event) => {
      console.log('🔌 WebSocket disconnected:', event.code, event.reason);
      setIsConnected(false);
    };
    
    setWs(websocket);
    
    return () => {
      console.log('Cleaning up WebSocket connection');
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, []);
  
  const sendMessage = useCallback(
    (message: any) => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
      } else {
        console.warn('WebSocket is not connected, message queued:', message);
      }
    },
    [ws]
  );
  
  const subscribe = useCallback(
    (topic: string, handler: (message: any) => void) => {
      setSubscriptions((prev) => {
        const newSubs = new Map(prev);
        if (!newSubs.has(topic)) {
          newSubs.set(topic, new Set());
        }
        newSubs.get(topic)!.add(handler);
        return newSubs;
      });
      
      // 서버에 구독 요청
      sendMessage({
        type: 'subscribe',
        topic,
      });
    },
    [sendMessage]
  );
  
  const unsubscribe = useCallback(
    (topic: string) => {
      setSubscriptions((prev) => {
        const newSubs = new Map(prev);
        newSubs.delete(topic);
        return newSubs;
      });
      
      // 서버에 구독 해제 요청
      sendMessage({
        type: 'unsubscribe',
        topic,
      });
    },
    [sendMessage]
  );
  
  return (
    <WebSocketContext.Provider value={{ isConnected, sendMessage, subscribe, unsubscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
};
