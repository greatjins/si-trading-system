import { useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts'
import type { OHLCData } from '../../types'

interface CandlestickChartProps {
  data: OHLCData[]
  symbol: string
}

export function CandlestickChart({ data, symbol }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  
  useEffect(() => {
    if (!chartContainerRef.current) return
    
    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b2b' },
        horzLines: { color: '#2b2b2b' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2b2b2b',
      },
      timeScale: {
        borderColor: '#2b2b2b',
        timeVisible: true,
        secondsVisible: false,
      },
    })
    
    // 캔들스틱 시리즈 추가
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderVisible: false,
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    })
    
    chartRef.current = chart
    seriesRef.current = candlestickSeries
    
    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }
    
    window.addEventListener('resize', handleResize)
    
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])
  
  useEffect(() => {
    if (!seriesRef.current || !data.length) return
    
    // 데이터 변환
    const chartData: CandlestickData[] = data.map((item) => ({
      time: new Date(item.timestamp).getTime() / 1000,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }))
    
    seriesRef.current.setData(chartData)
    
    // 차트 자동 스케일
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
  }, [data])
  
  return (
    <div style={{ width: '100%', height: '500px' }}>
      <div style={{ marginBottom: '10px', color: '#d1d4dc' }}>
        <h3>{symbol}</h3>
      </div>
      <div ref={chartContainerRef} />
    </div>
  )
}
