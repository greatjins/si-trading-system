/**
 * TradingView Lightweight Charts 캔들스틱 차트
 */
import { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { useChartStore } from '../../../app/store/chartStore';
import { CHART_COLORS } from '../../../constants/chart-constants';

export const CandlestickChart = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  
  const { candles, symbol } = useChartStore();
  
  // 차트 초기화
  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: CHART_COLORS.BACKGROUND },
        textColor: CHART_COLORS.TEXT,
      },
      grid: {
        vertLines: { color: CHART_COLORS.GRID },
        horzLines: { color: CHART_COLORS.GRID },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });
    
    const candleSeries = chart.addCandlestickSeries({
      upColor: CHART_COLORS.UP,
      downColor: CHART_COLORS.DOWN,
      borderUpColor: CHART_COLORS.UP,
      borderDownColor: CHART_COLORS.DOWN,
      wickUpColor: CHART_COLORS.UP,
      wickDownColor: CHART_COLORS.DOWN,
    });
    
    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    
    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);
  
  // 데이터 업데이트
  useEffect(() => {
    if (!candleSeriesRef.current || candles.length === 0) return;
    
    const chartData = candles.map((candle) => ({
      time: Math.floor(new Date(candle.timestamp).getTime() / 1000) as any,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));
    
    candleSeriesRef.current.setData(chartData);
    
    // 차트를 최신 데이터로 스크롤
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [candles]);
  
  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3>{symbol} 차트</h3>
      </div>
      <div ref={chartContainerRef} className="chart" />
    </div>
  );
};
