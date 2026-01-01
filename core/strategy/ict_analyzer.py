"""
ICT (Inner Circle Trader) 분석기
- 일봉 데이터에서 FVG (Fair Value Gap) 및 Order Block 탐지
- Multi-timeframe 분석 지원
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ICTAnalyzer:
    """
    ICT 기반 기술적 분석 클래스
    
    주요 기능:
    1. Fair Value Gap (FVG) 탐지
    2. Order Block (OB) 탐지
    3. 지지/저항 레벨 식별
    4. Multi-timeframe 매칭
    """
    
    def __init__(
        self,
        fvg_threshold: float = 0.002,
        ob_volume_ratio: float = 1.5,
        ob_body_ratio: float = 0.02
    ):
        """
        Args:
            fvg_threshold: FVG 최소 크기 (비율, 기본 0.2%)
            ob_volume_ratio: Order Block 거래량 배수 (기본 1.5배)
            ob_body_ratio: Order Block 몸통 최소 크기 (비율, 기본 2%)
        """
        self.fvg_threshold = fvg_threshold
        self.ob_volume_ratio = ob_volume_ratio
        self.ob_body_ratio = ob_body_ratio
        
        logger.info(f"ICTAnalyzer initialized (FVG threshold: {fvg_threshold:.1%}, OB volume: {ob_volume_ratio}x)")
    
    def detect_fvg(self, bars: pd.DataFrame) -> List[Dict]:
        """
        Fair Value Gap (FVG) 탐지
        
        FVG는 3개 봉 패턴으로 식별:
        - Bullish FVG: 이전 고점 < 다음 저점 (상승 갭)
        - Bearish FVG: 이전 저점 > 다음 고점 (하락 갭)
        
        Args:
            bars: OHLC DataFrame (timestamp 인덱스, columns: open, high, low, close, volume)
        
        Returns:
            FVG 리스트 [{
                "type": "BULLISH" | "BEARISH",
                "top": float,
                "bottom": float,
                "timestamp": datetime,
                "filled": bool
            }]
        """
        if len(bars) < 3:
            return []
        
        fvgs = []
        
        for i in range(2, len(bars)):
            prev_bar = bars.iloc[i-2]
            curr_bar = bars.iloc[i-1]
            next_bar = bars.iloc[i]
            
            # Bullish FVG: 이전 고점 < 다음 저점
            if prev_bar['high'] < next_bar['low']:
                gap_size = (next_bar['low'] - prev_bar['high']) / prev_bar['high']
                
                if gap_size >= self.fvg_threshold:
                    fvg = {
                        "type": "BULLISH",
                        "top": next_bar['low'],
                        "bottom": prev_bar['high'],
                        "timestamp": bars.index[i],
                        "filled": False
                    }
                    fvgs.append(fvg)
            
            # Bearish FVG: 이전 저점 > 다음 고점
            elif prev_bar['low'] > next_bar['high']:
                gap_size = (prev_bar['low'] - next_bar['high']) / next_bar['high']
                
                if gap_size >= self.fvg_threshold:
                    fvg = {
                        "type": "BEARISH",
                        "top": prev_bar['low'],
                        "bottom": next_bar['high'],
                        "timestamp": bars.index[i],
                        "filled": False
                    }
                    fvgs.append(fvg)
        
        logger.debug(f"Detected {len(fvgs)} FVGs")
        return fvgs
    
    def detect_order_blocks(self, bars: pd.DataFrame) -> List[Dict]:
        """
        Order Block (OB) 탐지
        
        Order Block은 기관 투자자의 대량 주문이 집중된 구간:
        - 높은 거래량 + 큰 몸통
        - 이후 가격 반응 확인
        
        Args:
            bars: OHLC DataFrame
        
        Returns:
            Order Block 리스트 [{
                "type": "BULLISH" | "BEARISH",
                "top": float,
                "bottom": float,
                "timestamp": datetime,
                "strength": float
            }]
        """
        if len(bars) < 10:
            return []
        
        order_blocks = []
        
        # 이동평균 거래량 계산
        avg_volume = bars['volume'].rolling(window=20).mean()
        
        for i in range(5, len(bars) - 5):
            bar = bars.iloc[i]
            
            # 거래량 및 몸통 크기 확인
            volume_ratio = bar['volume'] / avg_volume.iloc[i] if avg_volume.iloc[i] > 0 else 0
            body_size = abs(bar['close'] - bar['open']) / bar['open']
            
            # Order Block 조건: 높은 거래량 + 큰 몸통
            if volume_ratio >= self.ob_volume_ratio and body_size >= self.ob_body_ratio:
                # 다음 5개 봉에서 반응 확인
                next_bars = bars.iloc[i+1:i+6]
                
                if bar['close'] > bar['open']:  # 양봉 Order Block
                    # 이후 상승 지속 확인 (저점이 Order Block 하단 근처에서 유지)
                    if next_bars['close'].min() > bar['low'] * 0.995:
                        ob = {
                            "type": "BULLISH",
                            "top": bar['high'],
                            "bottom": bar['low'],
                            "timestamp": bars.index[i],
                            "strength": volume_ratio
                        }
                        order_blocks.append(ob)
                
                else:  # 음봉 Order Block
                    # 이후 하락 지속 확인 (고점이 Order Block 상단 근처에서 유지)
                    if next_bars['close'].max() < bar['high'] * 1.005:
                        ob = {
                            "type": "BEARISH",
                            "top": bar['high'],
                            "bottom": bar['low'],
                            "timestamp": bars.index[i],
                            "strength": volume_ratio
                        }
                        order_blocks.append(ob)
        
        logger.debug(f"Detected {len(order_blocks)} Order Blocks")
        return order_blocks
    
    def identify_support_resistance(
        self,
        bars: pd.DataFrame,
        lookback: int = 50,
        cluster_threshold: float = 0.015
    ) -> Dict[str, List[float]]:
        """
        지지/저항 레벨 식별
        
        Args:
            bars: OHLC DataFrame
            lookback: 분석 기간 (기본 50일)
            cluster_threshold: 클러스터 임계값 (기본 1.5%)
        
        Returns:
            {"support": [float], "resistance": [float]}
        """
        if len(bars) < lookback:
            lookback = len(bars)
        
        recent_bars = bars.tail(lookback)
        
        # Swing High/Low 찾기
        swing_highs = self._find_swing_points(recent_bars['high'], 'high')
        swing_lows = self._find_swing_points(recent_bars['low'], 'low')
        
        # 클러스터링
        support_levels = self._cluster_prices(swing_lows, cluster_threshold)
        resistance_levels = self._cluster_prices(swing_highs, cluster_threshold)
        
        return {
            "support": support_levels[-5:],  # 최근 5개
            "resistance": resistance_levels[-5:]
        }
    
    def match_price_levels(
        self,
        daily_levels: List[Dict],
        minute_bars: pd.DataFrame,
        tolerance: float = 0.01
    ) -> List[Dict]:
        """
        일봉에서 찾은 가격대를 60분봉 데이터와 매칭
        
        Args:
            daily_levels: 일봉에서 찾은 레벨들 [{"type": "FVG"|"OB", "top": float, "bottom": float, ...}]
            minute_bars: 60분봉 DataFrame
            tolerance: 매칭 허용 오차 (기본 1%)
        
        Returns:
            매칭된 진입 시그널 [{
                "level": Dict,
                "entry_price": float,
                "timestamp": datetime,
                "signal": "BUY" | "SELL"
            }]
        """
        if minute_bars.empty or not daily_levels:
            return []
        
        signals = []
        current_price = minute_bars['close'].iloc[-1]
        current_time = minute_bars.index[-1]
        
        for level in daily_levels:
            top = level.get('top', 0)
            bottom = level.get('bottom', 0)
            level_type = level.get('type', '')
            
            # 가격대 내 진입 확인
            if bottom <= current_price <= top:
                # Bullish 레벨 (FVG 또는 OB)
                if level_type == 'BULLISH':
                    signal = {
                        "level": level,
                        "entry_price": current_price,
                        "timestamp": current_time,
                        "signal": "BUY",
                        "confidence": self._calculate_confidence(level, minute_bars)
                    }
                    signals.append(signal)
                
                # Bearish 레벨
                elif level_type == 'BEARISH':
                    signal = {
                        "level": level,
                        "entry_price": current_price,
                        "timestamp": current_time,
                        "signal": "SELL",
                        "confidence": self._calculate_confidence(level, minute_bars)
                    }
                    signals.append(signal)
        
        return signals
    
    def _find_swing_points(self, series: pd.Series, point_type: str, window: int = 5) -> List[float]:
        """Swing High/Low 찾기"""
        points = []
        
        for i in range(window, len(series) - window):
            if point_type == 'high':
                if series.iloc[i] == series.iloc[i-window:i+window+1].max():
                    points.append(series.iloc[i])
            else:  # low
                if series.iloc[i] == series.iloc[i-window:i+window+1].min():
                    points.append(series.iloc[i])
        
        return points
    
    def _cluster_prices(self, prices: List[float], threshold: float) -> List[float]:
        """가격 클러스터링"""
        if not prices:
            return []
        
        clusters = []
        sorted_prices = sorted(set(prices))
        
        for price in sorted_prices:
            # 임계값 내의 가격들 그룹화
            nearby_prices = [p for p in sorted_prices 
                           if abs(p - price) / price <= threshold]
            
            if len(nearby_prices) >= 3:  # 최소 3개 이상
                cluster_price = np.mean(nearby_prices)
                if not any(abs(cluster_price - c) / c <= threshold for c in clusters):
                    clusters.append(cluster_price)
        
        return sorted(clusters)
    
    def _calculate_confidence(self, level: Dict, minute_bars: pd.DataFrame) -> float:
        """진입 신호 신뢰도 계산"""
        confidence = 0.5  # 기본값
        
        # Order Block 강도 고려
        if 'strength' in level:
            confidence += min(level['strength'] / 3.0, 0.3)  # 최대 0.3 추가
        
        # 최근 추세 확인
        if len(minute_bars) >= 5:
            recent_trend = (minute_bars['close'].iloc[-1] - minute_bars['close'].iloc[-5]) / minute_bars['close'].iloc[-5]
            if level.get('type') == 'BULLISH' and recent_trend > 0:
                confidence += 0.2
            elif level.get('type') == 'BEARISH' and recent_trend < 0:
                confidence += 0.2
        
        return min(confidence, 1.0)  # 최대 1.0
