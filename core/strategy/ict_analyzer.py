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
from utils.indicators import calculate_fvg, calculate_order_block

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
        
        utils/indicators.py의 calculate_fvg 함수를 사용하여 FVG를 계산하고,
        결과를 리스트 형태로 변환합니다.
        
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
        
        # utils/indicators.py의 공통 함수 사용
        bars_with_fvg = calculate_fvg(bars.copy())
        
        # DataFrame에서 FVG 정보 추출하여 리스트로 변환
        fvgs = []
        for idx, row in bars_with_fvg.iterrows():
            if pd.notna(row.get('fvg_type')):
                fvg = {
                    "type": row['fvg_type'].upper(),  # 'bullish' -> 'BULLISH'
                    "top": row['fvg_top'],
                    "bottom": row['fvg_bottom'],
                    "timestamp": idx,
                    "filled": row.get('fvg_filled', False)
                }
                fvgs.append(fvg)
        
        logger.debug(f"Detected {len(fvgs)} FVGs")
        return fvgs
    
    def detect_order_blocks(self, bars: pd.DataFrame) -> List[Dict]:
        """
        Order Block (OB) 탐지
        
        utils/indicators.py의 calculate_order_block 함수를 사용하여 Order Block을 계산하고,
        결과를 리스트 형태로 변환합니다.
        
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
        if len(bars) < 20:
            return []
        
        # utils/indicators.py의 공통 함수 사용
        bars_with_ob = calculate_order_block(
            bars.copy(),
            lookback=20,
            volume_multiplier=self.ob_volume_ratio
        )
        
        # DataFrame에서 Order Block 정보 추출하여 리스트로 변환
        order_blocks = []
        for idx, row in bars_with_ob.iterrows():
            if pd.notna(row.get('order_block_type')):
                ob = {
                    "type": row['order_block_type'].upper(),  # 'bullish' -> 'BULLISH'
                    "top": row['order_block_top'],
                    "bottom": row['order_block_bottom'],
                    "timestamp": idx,
                    "strength": row.get('order_block_volume', 0) / bars['volume'].mean() if bars['volume'].mean() > 0 else 0
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
