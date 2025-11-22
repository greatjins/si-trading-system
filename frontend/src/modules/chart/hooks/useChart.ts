/**
 * 차트 데이터 관리 훅
 */
import { useEffect } from 'react';
import { useChartStore } from '../../../app/store/chartStore';
import { fetchOHLC } from '../services/chartApi';
import { useWebSocket } from '../../../hooks/useWebSocket';
import { WS_EVENTS } from '../../../constants/ws-events';

export const useChart = () => {
  const {
    symbol,
    interval,
    candles,
    isLoading,
    error,
    setCandles,
    setLoading,
    setError,
    updateLastCandle,
  } = useChartStore();
  
  const { subscribe, unsubscribe, isConnected } = useWebSocket();
  
  // 초기 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const data = await fetchOHLC(symbol, interval, 100);
        setCandles(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터 로드 실패');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [symbol, interval, setCandles, setLoading, setError]);
  
  // WebSocket 실시간 구독
  useEffect(() => {
    if (!isConnected) return;
    
    const topic = `price:${symbol}`;
    
    // 구독
    subscribe(topic, (message) => {
      if (message.type === WS_EVENTS.PRICE && message.symbol === symbol) {
        const newCandle = {
          timestamp: message.data.timestamp,
          open: message.data.open,
          high: message.data.high,
          low: message.data.low,
          close: message.data.price,
          volume: message.data.volume,
        };
        
        updateLastCandle(newCandle);
      }
    });
    
    return () => {
      unsubscribe(topic);
    };
  }, [symbol, isConnected, subscribe, unsubscribe, updateLastCandle]);
  
  return {
    symbol,
    interval,
    candles,
    isLoading,
    error,
  };
};
