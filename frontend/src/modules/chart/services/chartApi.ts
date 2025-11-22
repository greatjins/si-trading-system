/**
 * 차트 API 서비스
 */
import { httpClient } from '../../../services/http';
import { ENDPOINTS } from '../../../services/endpoints';
import { Candle } from '../../../app/store/chartStore';

export interface OHLCResponse {
  symbol: string;
  interval: string;
  count: number;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

export interface CurrentPriceResponse {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
}

/**
 * OHLC 데이터 조회
 */
export const fetchOHLC = async (
  symbol: string,
  interval: string,
  limit = 100
): Promise<Candle[]> => {
  const response = await httpClient.get<OHLCResponse>(
    ENDPOINTS.PRICE.OHLC(symbol),
    {
      params: { interval, limit },
    }
  );
  
  return response.data.data.map((item) => ({
    timestamp: item.timestamp,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume,
  }));
};

/**
 * 현재가 조회
 */
export const fetchCurrentPrice = async (
  symbol: string
): Promise<CurrentPriceResponse> => {
  const response = await httpClient.get<CurrentPriceResponse>(
    ENDPOINTS.PRICE.CURRENT(symbol)
  );
  
  return response.data;
};

/**
 * 종목 목록 조회
 */
export const fetchSymbols = async (): Promise<string[]> => {
  const response = await httpClient.get<{ count: number; symbols: string[] }>(
    ENDPOINTS.PRICE.SYMBOLS
  );
  
  return response.data.symbols;
};
