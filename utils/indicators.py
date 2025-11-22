"""
기술적 지표 계산 유틸리티
"""
import pandas as pd
from typing import List


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
