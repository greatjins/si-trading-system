"""
ICT (Inner Circle Trader) 기반 전략
- Smart Money Concepts 적용
- 기관투자자 관점의 시장 분석
- 유동성 기반 진입/청산
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order
from utils.logger import setup_logger

logger = setup_logger(__name__)


@strategy(
    name="ICTStrategy",
    description="ICT 이론 기반 Smart Money 전략 - 기관투자자 관점의 시장 분석",
    author="LS HTS Team",
    version="1.0.0",
    parameters={
        "symbol": {
            "type": "str",
            "default": "005930",
            "description": "종목 코드"
        },
        "lookback_period": {
            "type": "int",
            "default": 50,
            "min": 20,
            "max": 200,
            "description": "시장 구조 분석 기간"
        },
        "fvg_threshold": {
            "type": "float",
            "default": 0.002,
            "min": 0.001,
            "max": 0.01,
            "description": "Fair Value Gap 최소 크기 (비율)"
        },
        "liquidity_threshold": {
            "type": "float",
            "default": 0.015,
            "min": 0.005,
            "max": 0.05,
            "description": "유동성 풀 감지 임계값 (비율)"
        },
        "risk_per_trade": {
            "type": "float",
            "default": 0.02,
            "min": 0.01,
            "max": 0.05,
            "description": "거래당 리스크 (계좌 대비 비율)"
        },
        "rr_ratio": {
            "type": "float",
            "default": 2.0,
            "min": 1.0,
            "max": 5.0,
            "description": "Risk-Reward 비율"
        }
    }
)
class ICTStrategy(BaseStrategy):
    """
    ICT (Inner Circle Trader) 전략
    
    핵심 로직:
    1. Market Structure 분석 (BOS, CHoCH 감지)
    2. Liquidity Pool 식별 (고점/저점 클러스터)
    3. Fair Value Gap (FVG) 감지
    4. Order Block 식별
    5. Smart Money 흐름 분석
    6. 유동성 기반 진입/청산
    """
    
    def __init__(self, params: dict):
        super().__init__(params)
        
        self.symbol = self.get_param("symbol", "005930")
        self.lookback_period = self.get_param("lookback_period", 50)
        self.fvg_threshold = self.get_param("fvg_threshold", 0.002)
        self.liquidity_threshold = self.get_param("liquidity_threshold", 0.015)
        self.risk_per_trade = self.get_param("risk_per_trade", 0.02)
        self.rr_ratio = self.get_param("rr_ratio", 2.0)
        
        # 상태 변수
        self.market_structure = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
        self.last_bos = None  # Break of Structure
        self.order_blocks = []  # 식별된 Order Block들
        self.liquidity_pools = {"highs": [], "lows": []}
        self.fair_value_gaps = []
        
        logger.info(f"ICT Strategy initialized: {self.symbol}")
    
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        ICT 분석 및 신호 생성
        """
        signals: List[OrderSignal] = []
        
        if not self._validate_data(bars):
            return signals
        
        if len(bars) < self.lookback_period:
            return signals
        
        # 1. Market Structure 분석
        self._analyze_market_structure(bars)
        
        # 2. Liquidity Pool 식별
        self._identify_liquidity_pools(bars)
        
        # 3. Fair Value Gap 감지
        self._detect_fair_value_gaps(bars)
        
        # 4. Order Block 식별
        self._identify_order_blocks(bars)
        
        # 5. 진입 신호 생성
        entry_signal = self._generate_entry_signal(bars, positions, account)
        if entry_signal:
            signals.append(entry_signal)
        
        # 6. 청산 신호 생성
        exit_signal = self._generate_exit_signal(bars, positions)
        if exit_signal:
            signals.append(exit_signal)
        
        return signals
    
    def _analyze_market_structure(self, bars: pd.DataFrame) -> None:
        """
        시장 구조 분석 (BOS, CHoCH 감지)
        """
        if len(bars) < 20:
            return
        
        # Swing High/Low 식별
        highs = self._find_swing_points(bars['high'], 'high')
        lows = self._find_swing_points(bars['low'], 'low')
        
        # BOS (Break of Structure) 감지
        current_price = bars['close'].iloc[-1]
        
        # 상승 BOS: 이전 고점 돌파
        if highs and current_price > max(highs[-3:]) * 1.001:
            if self.market_structure != "BULLISH":
                self.market_structure = "BULLISH"
                self.last_bos = {"type": "BULLISH", "price": current_price, "time": bars.index[-1]}
                logger.info(f"🟢 Bullish BOS detected at {current_price:,.0f}")
        
        # 하락 BOS: 이전 저점 하향 돌파
        elif lows and current_price < min(lows[-3:]) * 0.999:
            if self.market_structure != "BEARISH":
                self.market_structure = "BEARISH"
                self.last_bos = {"type": "BEARISH", "price": current_price, "time": bars.index[-1]}
                logger.info(f"🔴 Bearish BOS detected at {current_price:,.0f}")
    
    def _identify_liquidity_pools(self, bars: pd.DataFrame) -> None:
        """
        유동성 풀 식별 (고점/저점 클러스터)
        """
        if len(bars) < 20:
            return
        
        # 최근 N개 봉의 고점/저점 분석
        recent_bars = bars.tail(self.lookback_period)
        
        # 고점 클러스터 (저항선)
        highs = recent_bars['high'].rolling(window=5).max()
        high_clusters = self._find_price_clusters(highs.dropna(), self.liquidity_threshold)
        
        # 저점 클러스터 (지지선)
        lows = recent_bars['low'].rolling(window=5).min()
        low_clusters = self._find_price_clusters(lows.dropna(), self.liquidity_threshold)
        
        self.liquidity_pools = {
            "highs": high_clusters,
            "lows": low_clusters
        }
        
        logger.debug(f"Liquidity pools - Highs: {len(high_clusters)}, Lows: {len(low_clusters)}")
    
    def _detect_fair_value_gaps(self, bars: pd.DataFrame) -> None:
        """
        Fair Value Gap (FVG) 감지
        """
        if len(bars) < 3:
            return
        
        self.fair_value_gaps = []
        
        for i in range(2, len(bars)):
            # 3개 봉 패턴 분석
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
                        "time": bars.index[i],
                        "filled": False
                    }
                    self.fair_value_gaps.append(fvg)
            
            # Bearish FVG: 이전 저점 > 다음 고점
            elif prev_bar['low'] > next_bar['high']:
                gap_size = (prev_bar['low'] - next_bar['high']) / next_bar['high']
                
                if gap_size >= self.fvg_threshold:
                    fvg = {
                        "type": "BEARISH",
                        "top": prev_bar['low'],
                        "bottom": next_bar['high'],
                        "time": bars.index[i],
                        "filled": False
                    }
                    self.fair_value_gaps.append(fvg)
        
        # 최근 10개만 유지
        self.fair_value_gaps = self.fair_value_gaps[-10:]
    
    def _identify_order_blocks(self, bars: pd.DataFrame) -> None:
        """
        Order Block 식별 (기관 주문 집중 구간)
        """
        if len(bars) < 10:
            return
        
        self.order_blocks = []
        
        for i in range(5, len(bars) - 5):
            bar = bars.iloc[i]
            
            # 높은 거래량 + 큰 몸통 = Order Block 후보
            avg_volume = bars['volume'].rolling(window=20).mean().iloc[i]
            body_size = abs(bar['close'] - bar['open']) / bar['open']
            
            if (bar['volume'] > avg_volume * 1.5 and 
                body_size > 0.02):  # 2% 이상 몸통
                
                # 다음 5개 봉에서 반응 확인
                next_bars = bars.iloc[i+1:i+6]
                
                if bar['close'] > bar['open']:  # 양봉 Order Block
                    # 이후 상승 지속 확인
                    if next_bars['close'].min() > bar['low'] * 0.995:
                        order_block = {
                            "type": "BULLISH",
                            "top": bar['high'],
                            "bottom": bar['low'],
                            "time": bars.index[i],
                            "strength": bar['volume'] / avg_volume
                        }
                        self.order_blocks.append(order_block)
                
                else:  # 음봉 Order Block
                    # 이후 하락 지속 확인
                    if next_bars['close'].max() < bar['high'] * 1.005:
                        order_block = {
                            "type": "BEARISH",
                            "top": bar['high'],
                            "bottom": bar['low'],
                            "time": bars.index[i],
                            "strength": bar['volume'] / avg_volume
                        }
                        self.order_blocks.append(order_block)
        
        # 최근 5개만 유지
        self.order_blocks = self.order_blocks[-5:]
    
    def _generate_entry_signal(
        self, 
        bars: pd.DataFrame, 
        positions: List[Position], 
        account: Account
    ) -> Optional[OrderSignal]:
        """
        ICT 기반 진입 신호 생성
        """
        position = self.get_position(self.symbol, positions)
        if position:  # 이미 포지션 보유 중
            return None
        
        current_price = bars['close'].iloc[-1]
        
        # 상승 진입 조건
        if self._check_bullish_entry(bars, current_price):
            quantity = self._calculate_position_size(account.equity, current_price, "BUY")
            
            if quantity > 0:
                logger.info(f"🟢 ICT Bullish Entry: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
        
        # 하락 진입 조건 (공매도)
        elif self._check_bearish_entry(bars, current_price):
            quantity = self._calculate_position_size(account.equity, current_price, "SELL")
            
            if quantity > 0:
                logger.info(f"🔴 ICT Bearish Entry: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
        
        return None
    
    def _check_bullish_entry(self, bars: pd.DataFrame, current_price: float) -> bool:
        """
        상승 진입 조건 확인
        """
        # 1. 상승 시장 구조
        if self.market_structure != "BULLISH":
            return False
        
        # 2. FVG 리테스트
        for fvg in self.fair_value_gaps:
            if (fvg["type"] == "BULLISH" and 
                not fvg["filled"] and
                fvg["bottom"] <= current_price <= fvg["top"]):
                return True
        
        # 3. Order Block 리테스트
        for ob in self.order_blocks:
            if (ob["type"] == "BULLISH" and
                ob["bottom"] <= current_price <= ob["top"]):
                return True
        
        # 4. 유동성 풀 테스트 후 반등
        for low_pool in self.liquidity_pools["lows"]:
            if abs(current_price - low_pool) / low_pool < 0.005:  # 0.5% 이내
                # 반등 확인
                if len(bars) >= 3:
                    recent_low = bars['low'].tail(3).min()
                    if current_price > recent_low * 1.002:  # 0.2% 반등
                        return True
        
        return False
    
    def _check_bearish_entry(self, bars: pd.DataFrame, current_price: float) -> bool:
        """
        하락 진입 조건 확인
        """
        # 1. 하락 시장 구조
        if self.market_structure != "BEARISH":
            return False
        
        # 2. FVG 리테스트
        for fvg in self.fair_value_gaps:
            if (fvg["type"] == "BEARISH" and 
                not fvg["filled"] and
                fvg["bottom"] <= current_price <= fvg["top"]):
                return True
        
        # 3. Order Block 리테스트
        for ob in self.order_blocks:
            if (ob["type"] == "BEARISH" and
                ob["bottom"] <= current_price <= ob["top"]):
                return True
        
        # 4. 유동성 풀 테스트 후 하락
        for high_pool in self.liquidity_pools["highs"]:
            if abs(current_price - high_pool) / high_pool < 0.005:  # 0.5% 이내
                # 하락 확인
                if len(bars) >= 3:
                    recent_high = bars['high'].tail(3).max()
                    if current_price < recent_high * 0.998:  # 0.2% 하락
                        return True
        
        return False
    
    def _generate_exit_signal(
        self, 
        bars: pd.DataFrame, 
        positions: List[Position]
    ) -> Optional[OrderSignal]:
        """
        청산 신호 생성
        """
        position = self.get_position(self.symbol, positions)
        if not position:
            return None
        
        current_price = bars['close'].iloc[-1]
        
        # 손절/익절 로직
        if position.quantity > 0:  # 롱 포지션
            # 손절: 최근 저점 하향 돌파
            recent_low = bars['low'].tail(10).min()
            if current_price < recent_low * 0.995:
                logger.info(f"🔴 Long Stop Loss: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
            
            # 익절: 유동성 풀 도달
            for high_pool in self.liquidity_pools["highs"]:
                if current_price >= high_pool * 0.998:
                    logger.info(f"🟢 Long Take Profit: {current_price:,.0f}")
                    return OrderSignal(
                        symbol=self.symbol,
                        side=OrderSide.SELL,
                        quantity=position.quantity,
                        order_type=OrderType.MARKET
                    )
        
        return None
    
    def _calculate_position_size(
        self, 
        equity: float, 
        price: float, 
        direction: str
    ) -> int:
        """
        ICT 리스크 관리 기반 포지션 사이징
        """
        risk_amount = equity * self.risk_per_trade
        
        # 스탑로스 거리 계산 (ATR 기반)
        stop_distance = price * 0.02  # 2% 기본 스탑
        
        if stop_distance <= 0:
            return 0
        
        # 포지션 크기 = 리스크 금액 / 스탑 거리
        position_value = risk_amount / (stop_distance / price)
        quantity = int(position_value / price)
        
        return max(1, quantity)
    
    def _find_swing_points(self, series: pd.Series, point_type: str) -> List[float]:
        """
        Swing High/Low 찾기
        """
        points = []
        window = 5
        
        for i in range(window, len(series) - window):
            if point_type == 'high':
                if series.iloc[i] == series.iloc[i-window:i+window+1].max():
                    points.append(series.iloc[i])
            else:  # low
                if series.iloc[i] == series.iloc[i-window:i+window+1].min():
                    points.append(series.iloc[i])
        
        return points[-10:]  # 최근 10개만
    
    def _find_price_clusters(self, prices: pd.Series, threshold: float) -> List[float]:
        """
        가격 클러스터 찾기 (유동성 풀)
        """
        if len(prices) < 3:
            return []
        
        clusters = []
        sorted_prices = sorted(prices.unique())
        
        for price in sorted_prices:
            # 임계값 내의 가격들 그룹화
            nearby_prices = [p for p in sorted_prices 
                           if abs(p - price) / price <= threshold]
            
            if len(nearby_prices) >= 3:  # 최소 3개 이상
                cluster_price = np.mean(nearby_prices)
                if not any(abs(cluster_price - c) / c <= threshold for c in clusters):
                    clusters.append(cluster_price)
        
        return clusters[-5:]  # 최근 5개만
    
    def _validate_data(self, bars: pd.DataFrame) -> bool:
        """
        데이터 유효성 검증
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in bars.columns for col in required_cols) and len(bars) > 0
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(f"[ICT] Order filled: {order.side.value} {order.filled_quantity} @ {order.price}")