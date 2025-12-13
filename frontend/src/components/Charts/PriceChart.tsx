import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, UTCTimestamp } from 'lightweight-charts';
import { OHLC, TradeMarker } from '../../types/backtest';

interface PriceChartProps {
  ohlcData: OHLC[];
  trades: TradeMarker[];
  symbol: string;
  height?: number;
}

const PriceChart: React.FC<PriceChartProps> = ({ 
  ohlcData, 
  trades, 
  symbol, 
  height = 400 
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [isLoading, setIsLoading] = useState(false); // 초기값을 false로 변경

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1, // Normal crosshair mode
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // 캔들스틱 시리즈 생성
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chart) {
        chart.remove();
      }
    };
  }, [height]);

  useEffect(() => {
    console.log('🔍 PriceChart useEffect 실행:', {
      hasCandlestickSeries: !!candlestickSeriesRef.current,
      ohlcDataLength: ohlcData.length,
      ohlcData: ohlcData.slice(0, 3) // 처음 3개만 로그
    });

    if (!candlestickSeriesRef.current) {
      console.log('⚠️ candlestickSeries가 없음');
      return;
    }

    if (!ohlcData.length) {
      console.log('⚠️ OHLC 데이터가 없음');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);

    try {
      // OHLC 데이터를 lightweight-charts 형식으로 변환
      const candlestickData: CandlestickData[] = ohlcData.map(item => {
        const timestamp = new Date(item.timestamp).getTime() / 1000;
        return {
          time: timestamp as UTCTimestamp,
          open: Number(item.open),
          high: Number(item.high),
          low: Number(item.low),
          close: Number(item.close),
        };
      });

      console.log('✅ 캔들스틱 데이터 변환 완료:', candlestickData.length, '개');

      // 캔들스틱 데이터 설정
      candlestickSeriesRef.current.setData(candlestickData);

      // 차트 범위 자동 조정
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }

      console.log('✅ 차트 렌더링 완료');
      setIsLoading(false);
    } catch (error) {
      console.error('❌ 차트 렌더링 실패:', error);
      setIsLoading(false);
    }
  }, [ohlcData]);

  useEffect(() => {
    if (!chartRef.current || !trades.length) return;

    // 기존 마커 제거
    const chart = chartRef.current;
    
    // 매매 마커 생성
    const markers = trades.map(trade => {
      const timestamp = (new Date(trade.timestamp).getTime() / 1000) as UTCTimestamp;
      
      return {
        time: timestamp,
        position: trade.side === 'buy' ? 'belowBar' as const : 'aboveBar' as const,
        color: trade.side === 'buy' ? '#26a69a' : '#ef5350',
        shape: trade.side === 'buy' ? 'arrowUp' as const : 'arrowDown' as const,
        text: `${trade.side.toUpperCase()}\n${trade.quantity}주\n₩${trade.price.toLocaleString()}${trade.pnl !== undefined ? `\nP&L: ₩${trade.pnl.toLocaleString()}` : ''}`,
        size: 1,
      };
    });

    // 마커 설정
    if (candlestickSeriesRef.current) {
      candlestickSeriesRef.current.setMarkers(markers);
    }
  }, [trades]);

  if (isLoading) {
    return (
      <div 
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height: `${height}px` }}
      >
        <div className="text-gray-500">차트를 로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          {symbol} 가격 차트 및 매매 내역
        </h3>
        <p className="text-sm text-gray-600">
          녹색 화살표: 매수, 빨간색 화살표: 매도
        </p>
      </div>
      <div 
        ref={chartContainerRef} 
        className="w-full border border-gray-200 rounded-lg"
        style={{ height: `${height}px` }}
      />
      {trades.length > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          총 {trades.length}개의 거래가 표시됩니다.
        </div>
      )}
    </div>
  );
};

export default PriceChart;