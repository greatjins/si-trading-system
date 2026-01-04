"""
기술적 지표 계산 유틸리티
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any


def calculate_sma(prices: List[float], period: int) -> float:
    """단순 이동평균 (Simple Moving Average)"""
    if len(prices) < period:
        return 0.0
    return sum(prices[-period:]) / period


def calculate_ema(prices: List[float], period: int) -> float:
    """지수 이동평균 (Exponential Moving Average)"""
    if len(prices) < period:
        return 0.0
    
    df = pd.Series(prices)
    ema = df.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    RSI (Relative Strength Index)
    
    Args:
        prices: 가격 리스트
        period: 기간 (기본: 14)
    
    Returns:
        RSI 값 (0-100)
    """
    if len(prices) < period + 1:
        return 50.0
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """
    ATR (Average True Range)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        period: 기간 (기본: 14)
    
    Returns:
        ATR 값
    """
    if len(closes) < period + 1:
        return 0.0
    
    true_ranges = []
    
    for i in range(1, len(closes)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i-1]
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    # ATR = 최근 N개 TR의 평균
    atr = sum(true_ranges[-period:]) / period
    return atr


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0):
    """
    볼린저 밴드 (Bollinger Bands)
    
    Args:
        prices: 가격 리스트
        period: 기간
        std_dev: 표준편차 배수
    
    Returns:
        (middle, upper, lower)
    """
    if len(prices) < period:
        return 0.0, 0.0, 0.0
    
    df = pd.Series(prices[-period:])
    middle = df.mean()
    std = df.std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return float(middle), float(upper), float(lower)


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: 가격 리스트
        fast: 빠른 EMA 기간
        slow: 느린 EMA 기간
        signal: 시그널 라인 기간
    
    Returns:
        (macd, signal_line, histogram)
    """
    if len(prices) < slow:
        return 0.0, 0.0, 0.0
    
    df = pd.Series(prices)
    
    ema_fast = df.ewm(span=fast, adjust=False).mean()
    ema_slow = df.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], period: int = 14):
    """
    스토캐스틱 오실레이터 (Stochastic Oscillator)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        period: 기간
    
    Returns:
        %K 값 (0-100)
    """
    if len(closes) < period:
        return 50.0
    
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    current_close = closes[-1]
    
    highest = max(recent_highs)
    lowest = min(recent_lows)
    
    if highest == lowest:
        return 50.0
    
    k = ((current_close - lowest) / (highest - lowest)) * 100
    return k


def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """
    ADX (Average Directional Index)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        period: 기간
    
    Returns:
        ADX 값 (0-100)
    """
    if len(closes) < period + 1:
        return 0.0
    
    # 간단한 ADX 근사치 (실제로는 더 복잡)
    # 여기서는 ATR 기반 추세 강도로 근사
    atr = calculate_atr(highs, lows, closes, period)
    
    # 가격 변화율
    price_change = abs(closes[-1] - closes[-period])
    
    if atr == 0:
        return 0.0
    
    # ADX 근사치 (0-100)
    adx = min((price_change / atr) * 10, 100)
    return adx


def calculate_volume_ma(volumes: List[float], period: int = 20) -> float:
    """
    거래량 이동평균 (Volume Moving Average)
    
    Args:
        volumes: 거래량 리스트
        period: 기간
    
    Returns:
        거래량 이동평균
    """
    if len(volumes) < period:
        return 0.0
    return sum(volumes[-period:]) / period


def calculate_obv(closes: List[float], volumes: List[float]) -> float:
    """
    OBV (On-Balance Volume)
    
    Args:
        closes: 종가 리스트
        volumes: 거래량 리스트
    
    Returns:
        OBV 값
    """
    if len(closes) < 2 or len(volumes) < 2:
        return 0.0
    
    obv = 0.0
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv += volumes[i]
        elif closes[i] < closes[i-1]:
            obv -= volumes[i]
    
    return obv


def calculate_cci(highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
    """
    CCI (Commodity Channel Index)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        period: 기간
    
    Returns:
        CCI 값
    """
    if len(closes) < period:
        return 0.0
    
    # Typical Price = (High + Low + Close) / 3
    typical_prices = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(len(closes))]
    
    # SMA of Typical Price
    sma_tp = sum(typical_prices[-period:]) / period
    
    # Mean Deviation
    mean_dev = sum([abs(tp - sma_tp) for tp in typical_prices[-period:]]) / period
    
    if mean_dev == 0:
        return 0.0
    
    # CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
    cci = (typical_prices[-1] - sma_tp) / (0.015 * mean_dev)
    
    return cci


def calculate_williams_r(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """
    Williams %R
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        period: 기간
    
    Returns:
        Williams %R 값 (-100 ~ 0)
    """
    if len(closes) < period:
        return -50.0
    
    highest_high = max(highs[-period:])
    lowest_low = min(lows[-period:])
    
    if highest_high == lowest_low:
        return -50.0
    
    williams_r = ((highest_high - closes[-1]) / (highest_high - lowest_low)) * -100
    
    return williams_r


def calculate_mfi(highs: List[float], lows: List[float], closes: List[float], volumes: List[float], period: int = 14) -> float:
    """
    MFI (Money Flow Index)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        volumes: 거래량 리스트
        period: 기간
    
    Returns:
        MFI 값 (0-100)
    """
    if len(closes) < period + 1:
        return 50.0
    
    # Typical Price = (High + Low + Close) / 3
    typical_prices = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(len(closes))]
    
    # Money Flow = Typical Price × Volume
    money_flows = [typical_prices[i] * volumes[i] for i in range(len(typical_prices))]
    
    # Positive and Negative Money Flow
    positive_flow = 0.0
    negative_flow = 0.0
    
    for i in range(len(typical_prices) - period, len(typical_prices)):
        if i > 0:
            if typical_prices[i] > typical_prices[i-1]:
                positive_flow += money_flows[i]
            elif typical_prices[i] < typical_prices[i-1]:
                negative_flow += money_flows[i]
    
    if negative_flow == 0:
        return 100.0
    
    # Money Flow Ratio
    mfr = positive_flow / negative_flow
    
    # MFI = 100 - (100 / (1 + MFR))
    mfi = 100 - (100 / (1 + mfr))
    
    return mfi


def calculate_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
    """
    VWAP (Volume Weighted Average Price)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
        volumes: 거래량 리스트
    
    Returns:
        VWAP 값
    """
    if len(closes) == 0 or len(volumes) == 0:
        return 0.0
    
    # Typical Price = (High + Low + Close) / 3
    typical_prices = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(len(closes))]
    
    # VWAP = Σ(Typical Price × Volume) / Σ(Volume)
    total_pv = sum([typical_prices[i] * volumes[i] for i in range(len(typical_prices))])
    total_volume = sum(volumes)
    
    if total_volume == 0:
        return 0.0
    
    vwap = total_pv / total_volume
    
    return vwap


def calculate_pivot_points(high: float, low: float, close: float):
    """
    피봇 포인트 (Pivot Points)
    
    Args:
        high: 전일 고가
        low: 전일 저가
        close: 전일 종가
    
    Returns:
        (pivot, r1, r2, s1, s2)
    """
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    
    return pivot, r1, r2, s1, s2


def calculate_ichimoku(highs: List[float], lows: List[float], closes: List[float]):
    """
    일목균형표 (Ichimoku Cloud)
    
    Args:
        highs: 고가 리스트
        lows: 저가 리스트
        closes: 종가 리스트
    
    Returns:
        (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b)
    """
    if len(closes) < 52:
        return 0.0, 0.0, 0.0, 0.0
    
    # 전환선 (Tenkan-sen): 9일 중간값
    tenkan_high = max(highs[-9:])
    tenkan_low = min(lows[-9:])
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    
    # 기준선 (Kijun-sen): 26일 중간값
    kijun_high = max(highs[-26:])
    kijun_low = min(lows[-26:])
    kijun_sen = (kijun_high + kijun_low) / 2
    
    # 선행스팬 A (Senkou Span A): (전환선 + 기준선) / 2
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    
    # 선행스팬 B (Senkou Span B): 52일 중간값
    senkou_high = max(highs[-52:])
    senkou_low = min(lows[-52:])
    senkou_span_b = (senkou_high + senkou_low) / 2
    
    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b


def calculate_fvg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fair Value Gap (FVG) 계산 - ICT 핵심 로직
    
    3개 캔들을 비교하여 Fair Value Gap 구간을 찾고, 이후 캔들들이 FVG를 채웠는지 추적합니다.
    
    - Bullish FVG: 캔들 1의 Low와 캔들 3의 High 사이의 간격 (캔들 1의 High < 캔들 3의 Low)
    - Bearish FVG: 캔들 1의 High와 캔들 3의 Low 사이의 간격 (캔들 1의 Low > 캔들 3의 High)
    
    Args:
        df: OHLC DataFrame (columns: open, high, low, close, index: timestamp)
    
    Returns:
        DataFrame with FVG 정보 추가
        - fvg_type: 'bullish' (상승 FVG) 또는 'bearish' (하락 FVG) 또는 None
        - fvg_top: FVG 상단 가격
        - fvg_bottom: FVG 하단 가격
        - fvg_filled: FVG가 채워졌는지 여부 (True/False/None)
        - fvg_filled_at: FVG가 채워진 인덱스 (채워지지 않았으면 None)
    """
    if len(df) < 3:
        df['fvg_type'] = None
        df['fvg_top'] = None
        df['fvg_bottom'] = None
        df['fvg_filled'] = None
        df['fvg_filled_at'] = None
        return df
    
    # 결과 컬럼 초기화
    df = df.copy()
    df['fvg_type'] = None
    df['fvg_top'] = None
    df['fvg_bottom'] = None
    df['fvg_filled'] = None
    df['fvg_filled_at'] = None
    
    # FVG 리스트 저장 (나중에 필드 여부 확인용)
    fvg_list = []
    
    for i in range(2, len(df)):
        candle1 = df.iloc[i - 2]  # 첫 번째 캔들
        candle2 = df.iloc[i - 1]  # 두 번째 캔들 (중간)
        candle3 = df.iloc[i]      # 세 번째 캔들
        
        # Bullish FVG: 캔들 1의 High < 캔들 3의 Low
        # (캔들 1의 Low와 캔들 3의 High 사이의 간격)
        bullish_fvg = candle1['high'] < candle3['low']
        
        # Bearish FVG: 캔들 1의 Low > 캔들 3의 High
        # (캔들 1의 High와 캔들 3의 Low 사이의 간격)
        bearish_fvg = candle1['low'] > candle3['high']
        
        if bullish_fvg:
            # Bullish FVG: Top = 캔들 3의 Low, Bottom = 캔들 1의 High
            fvg_top = candle3['low']
            fvg_bottom = candle1['high']
            
            # 중간 캔들(캔들 2)에 FVG 정보 표시
            df.iloc[i - 1, df.columns.get_loc('fvg_type')] = 'bullish'
            df.iloc[i - 1, df.columns.get_loc('fvg_top')] = fvg_top
            df.iloc[i - 1, df.columns.get_loc('fvg_bottom')] = fvg_bottom
            
            # FVG 정보 저장
            fvg_list.append({
                'index': i - 1,  # 중간 캔들 인덱스
                'type': 'bullish',
                'top': fvg_top,
                'bottom': fvg_bottom,
                'filled': False,
                'filled_at': None
            })
            
        elif bearish_fvg:
            # Bearish FVG: Top = 캔들 1의 Low, Bottom = 캔들 3의 High
            fvg_top = candle1['low']
            fvg_bottom = candle3['high']
            
            # 중간 캔들(캔들 2)에 FVG 정보 표시
            df.iloc[i - 1, df.columns.get_loc('fvg_type')] = 'bearish'
            df.iloc[i - 1, df.columns.get_loc('fvg_top')] = fvg_top
            df.iloc[i - 1, df.columns.get_loc('fvg_bottom')] = fvg_bottom
            
            # FVG 정보 저장
            fvg_list.append({
                'index': i - 1,  # 중간 캔들 인덱스
                'type': 'bearish',
                'top': fvg_top,
                'bottom': fvg_bottom,
                'filled': False,
                'filled_at': None
            })
    
    # FVG 필드 여부 확인 (이후 캔들들이 FVG 구간을 침범했는지)
    for fvg in fvg_list:
        fvg_idx = fvg['index']
        fvg_top = fvg['top']
        fvg_bottom = fvg['bottom']
        
        # FVG 이후의 캔들들을 확인
        for j in range(fvg_idx + 1, len(df)):
            candle = df.iloc[j]
            
            # 상승 FVG는 하락 캔들이 채움 (저가가 FVG 구간을 침범)
            if fvg['type'] == 'bullish':
                if candle['low'] <= fvg_top:
                    fvg['filled'] = True
                    fvg['filled_at'] = j
                    df.iloc[fvg_idx, df.columns.get_loc('fvg_filled')] = True
                    df.iloc[fvg_idx, df.columns.get_loc('fvg_filled_at')] = j
                    break
            
            # 하락 FVG는 상승 캔들이 채움 (고가가 FVG 구간을 침범)
            elif fvg['type'] == 'bearish':
                if candle['high'] >= fvg_bottom:
                    fvg['filled'] = True
                    fvg['filled_at'] = j
                    df.iloc[fvg_idx, df.columns.get_loc('fvg_filled')] = True
                    df.iloc[fvg_idx, df.columns.get_loc('fvg_filled_at')] = j
                    break
        
        # 채워지지 않은 경우
        if not fvg['filled']:
            df.iloc[fvg_idx, df.columns.get_loc('fvg_filled')] = False
    
    return df


def calculate_liquidity_zones(df: pd.DataFrame, period: int = 20, tolerance: float = 0.001) -> pd.DataFrame:
    """
    Liquidity Zones 계산
    
    특정 기간 내의 최고점/최저점을 유동성 구간으로 정의합니다.
    유동성 구간은 가격이 반복적으로 테스트하는 중요한 지지/저항 레벨입니다.
    
    Args:
        df: OHLC DataFrame (columns: open, high, low, close, index: timestamp)
        period: 유동성 구간을 찾기 위한 기간 (기본: 20)
        tolerance: 유동성 구간으로 인정할 가격 차이 비율 (기본: 0.1%)
    
    Returns:
        DataFrame with Liquidity Zones 정보 추가
        - liquidity_zone_type: 'resistance' (저항) 또는 'support' (지지) 또는 None
        - liquidity_zone_top: 유동성 구간 상단 가격
        - liquidity_zone_bottom: 유동성 구간 하단 가격
        - liquidity_zone_strength: 유동성 구간 강도 (테스트 횟수)
    """
    if len(df) < period:
        df['liquidity_zone_type'] = None
        df['liquidity_zone_top'] = None
        df['liquidity_zone_bottom'] = None
        df['liquidity_zone_strength'] = None
        return df
    
    df = df.copy()
    df['liquidity_zone_type'] = None
    df['liquidity_zone_top'] = None
    df['liquidity_zone_bottom'] = None
    df['liquidity_zone_strength'] = None
    
    # 슬라이딩 윈도우로 유동성 구간 탐지
    for i in range(period, len(df)):
        window = df.iloc[i - period:i]
        
        # 기간 내 최고점과 최저점
        window_high = window['high'].max()
        window_low = window['low'].min()
        high_idx = window['high'].idxmax()
        low_idx = window['low'].idxmin()
        
        # 최고점/최저점 주변의 클러스터 찾기
        tolerance_value = (window_high - window_low) * tolerance
        
        # 저항 구간: 최고점 주변
        resistance_touches = 0
        for j in range(i - period, i):
            candle = df.iloc[j]
            if abs(candle['high'] - window_high) <= tolerance_value:
                resistance_touches += 1
        
        # 지지 구간: 최저점 주변
        support_touches = 0
        for j in range(i - period, i):
            candle = df.iloc[j]
            if abs(candle['low'] - window_low) <= tolerance_value:
                support_touches += 1
        
        # 유동성 구간이 충분히 강한 경우만 표시 (최소 2회 이상 테스트)
        if resistance_touches >= 2:
            df.iloc[i, df.columns.get_loc('liquidity_zone_type')] = 'resistance'
            df.iloc[i, df.columns.get_loc('liquidity_zone_top')] = window_high + tolerance_value
            df.iloc[i, df.columns.get_loc('liquidity_zone_bottom')] = window_high - tolerance_value
            df.iloc[i, df.columns.get_loc('liquidity_zone_strength')] = resistance_touches
        
        if support_touches >= 2:
            # 이미 저항 구간이 있으면 지지 구간도 추가 (둘 다 표시 가능)
            if df.iloc[i, df.columns.get_loc('liquidity_zone_type')] is None:
                df.iloc[i, df.columns.get_loc('liquidity_zone_type')] = 'support'
                df.iloc[i, df.columns.get_loc('liquidity_zone_top')] = window_low + tolerance_value
                df.iloc[i, df.columns.get_loc('liquidity_zone_bottom')] = window_low - tolerance_value
                df.iloc[i, df.columns.get_loc('liquidity_zone_strength')] = support_touches
            else:
                # 둘 다 있는 경우, 더 강한 것을 선택하거나 별도로 표시
                if support_touches > resistance_touches:
                    df.iloc[i, df.columns.get_loc('liquidity_zone_type')] = 'support'
                    df.iloc[i, df.columns.get_loc('liquidity_zone_top')] = window_low + tolerance_value
                    df.iloc[i, df.columns.get_loc('liquidity_zone_bottom')] = window_low - tolerance_value
                    df.iloc[i, df.columns.get_loc('liquidity_zone_strength')] = support_touches
    
    return df


def calculate_order_block(df: pd.DataFrame, lookback: int = 20, volume_multiplier: float = 1.5) -> pd.DataFrame:
    """
    Order Block 계산 - ICT 핵심 로직
    
    강한 추세 발생 직전의 마지막 반대 색상 캔들을 찾아, 해당 캔들의 몸통 범위를 OB 구간으로 정의합니다.
    
    - 상승 추세에서 하락 전환 전의 마지막 빨간(하락) 캔들의 몸통 = Bearish OB
    - 하락 추세에서 상승 전환 전의 마지막 파란(상승) 캔들의 몸통 = Bullish OB
    
    Args:
        df: OHLC DataFrame (columns: open, high, low, close, volume, index: timestamp)
        lookback: 추세 전환 탐지를 위한 최소 캔들 개수 (기본: 20)
        volume_multiplier: Order Block으로 인정할 최소 거래량 배수 (기본: 1.5배)
    
    Returns:
        DataFrame with Order Block 정보 추가
        - order_block_type: 'bullish' (상승 OB) 또는 'bearish' (하락 OB) 또는 None
        - order_block_top: Order Block 상단 가격 (몸통 상단)
        - order_block_bottom: Order Block 하단 가격 (몸통 하단)
        - order_block_index: Order Block이 발생한 인덱스
        - order_block_volume: Order Block의 거래량
    """
    if len(df) < lookback + 1:
        df['order_block_type'] = None
        df['order_block_top'] = None
        df['order_block_bottom'] = None
        df['order_block_index'] = None
        df['order_block_volume'] = None
        return df
    
    # volume 컬럼이 없으면 기본값 사용
    if 'volume' not in df.columns:
        df['volume'] = 0
    
    df = df.copy()
    df['order_block_type'] = None
    df['order_block_top'] = None
    df['order_block_bottom'] = None
    df['order_block_index'] = None
    df['order_block_volume'] = None
    
    # 캔들 색상 계산 (상승: True, 하락: False)
    df['is_bullish'] = df['close'] > df['open']
    
    # 평균 거래량 계산 (Order Block 필터링용)
    avg_volume = df['volume'].rolling(window=lookback).mean()
    
    for i in range(lookback, len(df)):
        # 현재 위치에서 과거 lookback 기간 동안의 추세 확인
        recent_candles = df.iloc[i - lookback:i]
        
        # 추세 방향 판단 (최근 고점/저점 비교)
        recent_high_idx = recent_candles['high'].idxmax()
        recent_low_idx = recent_candles['low'].idxmin()
        
        # 상승 추세: 최근 저점이 고점보다 앞에 있음
        is_uptrend = recent_low_idx < recent_high_idx
        
        # 하락 추세: 최근 고점이 저점보다 앞에 있음
        is_downtrend = recent_high_idx < recent_low_idx
        
        current_candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]
        
        # 평균 거래량 확인
        current_avg_volume = avg_volume.iloc[i] if not pd.isna(avg_volume.iloc[i]) else 0
        prev_volume = prev_candle['volume'] if 'volume' in prev_candle else 0
        
        # 상승 추세에서 하락 전환 감지 (현재 캔들이 하락 캔들이고, 이전이 상승 캔들)
        if is_uptrend and not current_candle['is_bullish'] and prev_candle['is_bullish']:
            # 거래량 조건 확인 (평균보다 높은 거래량)
            if prev_volume >= current_avg_volume * volume_multiplier:
                # 마지막 상승 캔들(이전 캔들)의 몸통 범위를 Order Block으로 정의
                # Bearish OB: 상승 추세에서 하락 전환 전의 마지막 상승 캔들
                body_top = max(prev_candle['open'], prev_candle['close'])
                body_bottom = min(prev_candle['open'], prev_candle['close'])
                
                df.iloc[i - 1, df.columns.get_loc('order_block_type')] = 'bearish'
                df.iloc[i - 1, df.columns.get_loc('order_block_top')] = body_top
                df.iloc[i - 1, df.columns.get_loc('order_block_bottom')] = body_bottom
                df.iloc[i - 1, df.columns.get_loc('order_block_index')] = i - 1
                df.iloc[i - 1, df.columns.get_loc('order_block_volume')] = prev_volume
        
        # 하락 추세에서 상승 전환 감지 (현재 캔들이 상승 캔들이고, 이전이 하락 캔들)
        elif is_downtrend and current_candle['is_bullish'] and not prev_candle['is_bullish']:
            # 거래량 조건 확인 (평균보다 높은 거래량)
            if prev_volume >= current_avg_volume * volume_multiplier:
                # 마지막 하락 캔들(이전 캔들)의 몸통 범위를 Order Block으로 정의
                # Bullish OB: 하락 추세에서 상승 전환 전의 마지막 하락 캔들
                body_top = max(prev_candle['open'], prev_candle['close'])
                body_bottom = min(prev_candle['open'], prev_candle['close'])
                
                df.iloc[i - 1, df.columns.get_loc('order_block_type')] = 'bullish'
                df.iloc[i - 1, df.columns.get_loc('order_block_top')] = body_top
                df.iloc[i - 1, df.columns.get_loc('order_block_bottom')] = body_bottom
                df.iloc[i - 1, df.columns.get_loc('order_block_index')] = i - 1
                df.iloc[i - 1, df.columns.get_loc('order_block_volume')] = prev_volume
    
    # is_bullish 컬럼 제거 (임시 컬럼)
    if 'is_bullish' in df.columns:
        df = df.drop(columns=['is_bullish'])
    
    return df


def calculate_mss_bos(df: pd.DataFrame, swing_lookback: int = 5) -> pd.DataFrame:
    """
    Market Structure Shift (MSS) & Break of Structure (BOS) 계산
    
    시장 구조 변화 및 구조 돌파 지점을 탐지합니다.
    - MSS: 상승 구조에서 하락 구조로 전환 (Higher High → Lower Low) 또는 그 반대
    - BOS: 이전 고점/저점을 돌파하는 지점
    
    Args:
        df: OHLC DataFrame (columns: open, high, low, close, index: timestamp)
        swing_lookback: Swing High/Low 판단을 위한 캔들 개수 (기본: 5)
    
    Returns:
        DataFrame with MSS & BOS 정보 추가
        - mss_type: 'bullish' (상승 구조 전환) 또는 'bearish' (하락 구조 전환) 또는 None
        - mss_index: MSS가 발생한 인덱스
        - bos_type: 'bullish' (상승 BOS - 고점 돌파) 또는 'bearish' (하락 BOS - 저점 돌파) 또는 None
        - bos_index: BOS가 발생한 인덱스
        - bos_break_level: 돌파된 가격 레벨
        - swing_high: Swing High 가격
        - swing_low: Swing Low 가격
    """
    if len(df) < swing_lookback * 2 + 1:
        df['mss_type'] = None
        df['mss_index'] = None
        df['bos_type'] = None
        df['bos_index'] = None
        df['bos_break_level'] = None
        df['swing_high'] = None
        df['swing_low'] = None
        return df
    
    df = df.copy()
    df['mss_type'] = None
    df['mss_index'] = None
    df['bos_type'] = None
    df['bos_index'] = None
    df['bos_break_level'] = None
    df['swing_high'] = None
    df['swing_low'] = None
    
    # Swing High/Low 탐지
    swing_highs = []
    swing_lows = []
    
    for i in range(swing_lookback, len(df) - swing_lookback):
        current_high = df.iloc[i]['high']
        current_low = df.iloc[i]['low']
        
        # Swing High: 양쪽 lookback 기간 내에서 최고점
        is_swing_high = True
        for j in range(i - swing_lookback, i + swing_lookback + 1):
            if j != i and df.iloc[j]['high'] >= current_high:
                is_swing_high = False
                break
        
        # Swing Low: 양쪽 lookback 기간 내에서 최저점
        is_swing_low = True
        for j in range(i - swing_lookback, i + swing_lookback + 1):
            if j != i and df.iloc[j]['low'] <= current_low:
                is_swing_low = False
                break
        
        if is_swing_high:
            swing_highs.append((i, current_high))
        if is_swing_low:
            swing_lows.append((i, current_low))
    
    # Market Structure Shift & Break of Structure 탐지
    # 최소 2개의 Swing High/Low가 필요
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        # 최근 Swing High/Low 비교
        last_swing_high_idx, last_swing_high = swing_highs[-1]
        prev_swing_high_idx, prev_swing_high = swing_highs[-2]
        
        last_swing_low_idx, last_swing_low = swing_lows[-1]
        prev_swing_low_idx, prev_swing_low = swing_lows[-2]
        
        # 하락 구조 전환: Higher High → Lower Low
        # (이전 Swing High보다 높았지만, 최근 Swing Low가 이전 Swing Low보다 낮음)
        if (last_swing_high > prev_swing_high and 
            last_swing_low < prev_swing_low and
            last_swing_low_idx > last_swing_high_idx):
            # Lower Low 지점에 MSS 표시
            df.iloc[last_swing_low_idx, df.columns.get_loc('mss_type')] = 'bearish'
            df.iloc[last_swing_low_idx, df.columns.get_loc('mss_index')] = last_swing_low_idx
            df.iloc[last_swing_low_idx, df.columns.get_loc('swing_high')] = last_swing_high
            df.iloc[last_swing_low_idx, df.columns.get_loc('swing_low')] = last_swing_low
        
        # 상승 구조 전환: Lower Low → Higher High
        # (이전 Swing Low보다 낮았지만, 최근 Swing High가 이전 Swing High보다 높음)
        elif (last_swing_low < prev_swing_low and 
              last_swing_high > prev_swing_high and
              last_swing_high_idx > last_swing_low_idx):
            # Higher High 지점에 MSS 표시
            df.iloc[last_swing_high_idx, df.columns.get_loc('mss_type')] = 'bullish'
            df.iloc[last_swing_high_idx, df.columns.get_loc('mss_index')] = last_swing_high_idx
            df.iloc[last_swing_high_idx, df.columns.get_loc('swing_high')] = last_swing_high
            df.iloc[last_swing_high_idx, df.columns.get_loc('swing_low')] = last_swing_low
        
        # Break of Structure (BOS) 탐지
        # 이전 Swing High/Low를 돌파하는 지점 찾기
        for i in range(max(last_swing_high_idx, last_swing_low_idx) + 1, len(df)):
            candle = df.iloc[i]
            
            # 상승 BOS: 이전 Swing High를 돌파
            if candle['high'] > prev_swing_high and df.iloc[i, df.columns.get_loc('bos_type')] is None:
                df.iloc[i, df.columns.get_loc('bos_type')] = 'bullish'
                df.iloc[i, df.columns.get_loc('bos_index')] = i
                df.iloc[i, df.columns.get_loc('bos_break_level')] = prev_swing_high
            
            # 하락 BOS: 이전 Swing Low를 돌파
            if candle['low'] < prev_swing_low and df.iloc[i, df.columns.get_loc('bos_type')] is None:
                df.iloc[i, df.columns.get_loc('bos_type')] = 'bearish'
                df.iloc[i, df.columns.get_loc('bos_index')] = i
                df.iloc[i, df.columns.get_loc('bos_break_level')] = prev_swing_low
    
    return df


def calculate_mss(df: pd.DataFrame, swing_lookback: int = 5) -> pd.DataFrame:
    """
    Market Structure Shift (MSS) 계산 (하위 호환성을 위한 별칭)
    
    Args:
        df: OHLC DataFrame
        swing_lookback: Swing High/Low 판단을 위한 캔들 개수
    
    Returns:
        DataFrame with MSS 정보 추가
    """
    return calculate_mss_bos(df, swing_lookback)


def calculate_custom_indicators(df: pd.DataFrame, config_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    UI에서 전달받은 JSON 설정을 바탕으로 동적으로 지표를 계산하는 함수
    
    Args:
        df: OHLC DataFrame (columns: open, high, low, close, volume, index: timestamp)
        config_list: 지표 설정 리스트
            예: [
                {'name': 'MA', 'params': {'period': 20, 'type': 'SMA'}},
                {'name': 'RSI', 'params': {'period': 14}},
                {'name': 'fvg', 'params': {}},
                {'name': 'order_block', 'params': {'lookback': 20, 'volume_multiplier': 1.5}}
            ]
    
    Returns:
        지표가 추가된 DataFrame
    
    지원하는 지표:
        기술적 지표:
            - MA (SMA/EMA): {'name': 'MA', 'params': {'period': 20, 'type': 'SMA'|'EMA'}}
            - RSI: {'name': 'RSI', 'params': {'period': 14}}
            - MACD: {'name': 'MACD', 'params': {'fast': 12, 'slow': 26, 'signal': 9}}
            - Bollinger Bands: {'name': 'BB', 'params': {'period': 20, 'std_dev': 2.0}}
            - ATR: {'name': 'ATR', 'params': {'period': 14}}
            - Stochastic: {'name': 'STOCH', 'params': {'period': 14}}
            - ADX: {'name': 'ADX', 'params': {'period': 14}}
            - Volume MA: {'name': 'VOLUME_MA', 'params': {'period': 20}}
            - OBV: {'name': 'OBV', 'params': {}}
            - CCI: {'name': 'CCI', 'params': {'period': 20}}
            - Williams %R: {'name': 'WILLR', 'params': {'period': 14}}
            - MFI: {'name': 'MFI', 'params': {'period': 14}}
            - VWAP: {'name': 'VWAP', 'params': {}}
        
        ICT 지표:
            - FVG: {'name': 'fvg', 'params': {}}
            - Liquidity Zones: {'name': 'liquidity', 'params': {'period': 20, 'tolerance': 0.001}}
            - Order Block: {'name': 'order_block', 'params': {'lookback': 20, 'volume_multiplier': 1.5}}
            - MSS/BOS: {'name': 'mss_bos', 'params': {'swing_lookback': 5}}
    """
    if df.empty:
        return df
    
    # 필수 컬럼 확인
    required_columns = ['open', 'high', 'low', 'close']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
    
    # volume 컬럼이 없으면 기본값 추가
    if 'volume' not in df.columns:
        df = df.copy()
        df['volume'] = 0
    
    df = df.copy()
    
    for config in config_list:
        if not isinstance(config, dict) or 'name' not in config:
            continue
        
        indicator_name = config['name'].lower()
        params = config.get('params', {})
        
        try:
            if indicator_name == 'ma':
                # 이동평균 (SMA/EMA)
                period = params.get('period', 20)
                ma_type = params.get('type', 'SMA').upper()
                
                if ma_type == 'SMA':
                    df[f'MA_{period}'] = df['close'].rolling(window=period).mean()
                elif ma_type == 'EMA':
                    df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
                else:
                    raise ValueError(f"지원하지 않는 MA 타입: {ma_type}")
            
            elif indicator_name == 'rsi':
                # RSI
                period = params.get('period', 14)
                df[f'RSI_{period}'] = _calculate_rsi_series(df['close'], period)
            
            elif indicator_name == 'macd':
                # MACD
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                
                ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
                ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal, adjust=False).mean()
                histogram = macd_line - signal_line
                
                df[f'MACD_{fast}_{slow}'] = macd_line
                df[f'MACD_Signal_{signal}'] = signal_line
                df[f'MACD_Histogram'] = histogram
            
            elif indicator_name == 'bb' or indicator_name == 'bollinger':
                # 볼린저 밴드
                period = params.get('period', 20)
                std_dev = params.get('std_dev', 2.0)
                
                sma = df['close'].rolling(window=period).mean()
                std = df['close'].rolling(window=period).std()
                
                df[f'BB_Middle_{period}'] = sma
                df[f'BB_Upper_{period}'] = sma + (std * std_dev)
                df[f'BB_Lower_{period}'] = sma - (std * std_dev)
            
            elif indicator_name == 'atr':
                # ATR
                period = params.get('period', 14)
                df[f'ATR_{period}'] = _calculate_atr_series(df, period)
            
            elif indicator_name == 'stoch' or indicator_name == 'stochastic':
                # 스토캐스틱
                period = params.get('period', 14)
                df[f'STOCH_{period}'] = _calculate_stochastic_series(df, period)
            
            elif indicator_name == 'adx':
                # ADX
                period = params.get('period', 14)
                df[f'ADX_{period}'] = _calculate_adx_series(df, period)
            
            elif indicator_name == 'volume_ma' or indicator_name == 'vol_ma':
                # 거래량 이동평균
                period = params.get('period', 20)
                df[f'Volume_MA_{period}'] = df['volume'].rolling(window=period).mean()
            
            elif indicator_name == 'obv':
                # OBV
                df['OBV'] = _calculate_obv_series(df)
            
            elif indicator_name == 'cci':
                # CCI
                period = params.get('period', 20)
                df[f'CCI_{period}'] = _calculate_cci_series(df, period)
            
            elif indicator_name == 'willr' or indicator_name == 'williams_r':
                # Williams %R
                period = params.get('period', 14)
                df[f'WilliamsR_{period}'] = _calculate_williams_r_series(df, period)
            
            elif indicator_name == 'mfi':
                # MFI
                period = params.get('period', 14)
                df[f'MFI_{period}'] = _calculate_mfi_series(df, period)
            
            elif indicator_name == 'vwap':
                # VWAP
                df['VWAP'] = _calculate_vwap_series(df)
            
            # ICT 지표
            elif indicator_name == 'fvg':
                # Fair Value Gap
                df = calculate_fvg(df)
            
            elif indicator_name == 'liquidity' or indicator_name == 'liquidity_zones':
                # Liquidity Zones
                period = params.get('period', 20)
                tolerance = params.get('tolerance', 0.001)
                df = calculate_liquidity_zones(df, period=period, tolerance=tolerance)
            
            elif indicator_name == 'order_block' or indicator_name == 'ob':
                # Order Block
                lookback = params.get('lookback', 20)
                volume_multiplier = params.get('volume_multiplier', 1.5)
                df = calculate_order_block(df, lookback=lookback, volume_multiplier=volume_multiplier)
            
            elif indicator_name == 'mss' or indicator_name == 'mss_bos' or indicator_name == 'bos':
                # Market Structure Shift / Break of Structure
                swing_lookback = params.get('swing_lookback', 5)
                df = calculate_mss_bos(df, swing_lookback=swing_lookback)
            
            else:
                # 지원하지 않는 지표
                print(f"경고: 지원하지 않는 지표 '{indicator_name}'는 무시됩니다.")
        
        except Exception as e:
            print(f"경고: 지표 '{indicator_name}' 계산 중 오류 발생: {e}")
            continue
    
    return df


# DataFrame 기반 시리즈 계산 헬퍼 함수들

def _calculate_rsi_series(close_series: pd.Series, period: int = 14) -> pd.Series:
    """RSI 시리즈 계산"""
    delta = close_series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _calculate_atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr.fillna(0.0)


def _calculate_stochastic_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """스토캐스틱 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    stoch = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    return stoch.fillna(50.0)


def _calculate_adx_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ADX 시리즈 계산 (간단한 근사치)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # ATR 기반 추세 강도 근사
    atr = _calculate_atr_series(df, period)
    price_change = abs(close - close.shift(period))
    
    adx = (price_change / atr) * 10
    adx = adx.clip(upper=100)
    
    return adx.fillna(0.0)


def _calculate_obv_series(df: pd.DataFrame) -> pd.Series:
    """OBV 시리즈 계산"""
    close = df['close']
    volume = df['volume']
    
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def _calculate_cci_series(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """CCI 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci.fillna(0.0)


def _calculate_williams_r_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Williams %R 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    willr = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return willr.fillna(-50.0)


def _calculate_mfi_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """MFI 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    tp = (high + low + close) / 3
    money_flow = tp * volume
    
    positive_flow = money_flow.where(tp > tp.shift(), 0).rolling(window=period).mean()
    negative_flow = money_flow.where(tp < tp.shift(), 0).rolling(window=period).mean()
    
    mfr = positive_flow / negative_flow
    mfi = 100 - (100 / (1 + mfr))
    
    return mfi.fillna(50.0)


def _calculate_vwap_series(df: pd.DataFrame) -> pd.Series:
    """VWAP 시리즈 계산"""
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    tp = (high + low + close) / 3
    pv = tp * volume
    
    vwap = pv.cumsum() / volume.cumsum()
    return vwap.fillna(close)
