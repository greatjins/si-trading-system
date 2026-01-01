"""
ICT 기반 Pyramiding 전략
- 일봉에서 FVG/OB 탐지
- 60분봉에서 진입 컨펌
- 추세 지속 시 추가 매수 (Pyramiding)
"""
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from core.strategy.ict_analyzer import ICTAnalyzer
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order
from utils.logger import setup_logger

logger = setup_logger(__name__)


@strategy(
    name="ict_pyramiding",
    description="ICT 기반 Pyramiding 전략 - 일봉 FVG/OB 탐지, 60분봉 진입, 추세 지속 시 추가 매수",
    author="LS HTS Team",
    version="1.0.0",
    parameters={
        "symbol": {
            "type": "str",
            "default": "005930",
            "description": "종목 코드"
        },
        "fvg_threshold": {
            "type": "float",
            "default": 0.002,
            "min": 0.001,
            "max": 0.01,
            "description": "FVG 최소 크기 (비율)"
        },
        "ob_volume_ratio": {
            "type": "float",
            "default": 1.5,
            "min": 1.0,
            "max": 5.0,
            "description": "Order Block 거래량 배수"
        },
        "pyramid_levels": {
            "type": "int",
            "default": 2,
            "min": 0,
            "max": 5,
            "description": "최대 추가 매수 횟수"
        },
        "pyramid_distance": {
            "type": "float",
            "default": 0.02,
            "min": 0.01,
            "max": 0.1,
            "description": "추가 매수 거리 (비율)"
        },
        "stop_loss_pct": {
            "type": "float",
            "default": 0.03,
            "min": 0.01,
            "max": 0.1,
            "description": "손절 비율"
        },
        "take_profit_pct": {
            "type": "float",
            "default": 0.06,
            "min": 0.02,
            "max": 0.2,
            "description": "익절 비율"
        }
    }
)
class ICTPyramidingStrategy(BaseStrategy):
    """
    ICT 기반 Pyramiding 전략
    
    전략 흐름:
    1. 일봉: 거래량 터진 날의 OHLC 기준으로 FVG/OB 탐지
    2. 60분봉: 일봉에서 찾은 가격대 도달 시 진입 컨펌
    3. Pyramiding: 추세 지속 시 리스크 관리와 함께 추가 매수
    4. Exit: ICT 추세 이탈, 볼린저 밴드 하향 돌파, 대량 거래 음봉 발생 시 분할 매도
    """
    
    def __init__(self, params: dict):
        super().__init__(params)
        
        # 파라미터
        self.symbol = self.get_param("symbol", "005930")
        self.fvg_threshold = self.get_param("fvg_threshold", 0.002)
        self.ob_volume_ratio = self.get_param("ob_volume_ratio", 1.5)
        self.pyramid_levels = self.get_param("pyramid_levels", 2)  # 최대 추가 매수 횟수
        self.pyramid_distance = self.get_param("pyramid_distance", 0.02)  # 추가 매수 거리 (2%)
        self.stop_loss_pct = self.get_param("stop_loss_pct", 0.03)  # 손절 (3%)
        self.take_profit_pct = self.get_param("take_profit_pct", 0.06)  # 익절 (6%)
        
        # ICT 분석기
        self.ict_analyzer = ICTAnalyzer(
            fvg_threshold=self.fvg_threshold,
            ob_volume_ratio=self.ob_volume_ratio
        )
        
        # 상태
        self.daily_levels = []  # 일봉에서 찾은 가격 레벨들
        self.pyramid_count = {}  # 종목별 추가 매수 횟수
        
        logger.info(f"ICT Pyramiding Strategy initialized: {self.symbol}")
    
    def on_bar(
        self,
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        Multi-timeframe 분석 및 신호 생성
        
        Args:
            bars: 60분봉 DataFrame (실시간 분석용)
            positions: 현재 포지션
            account: 계좌 상태
        
        Returns:
            주문 신호 리스트
        """
        signals: List[OrderSignal] = []
        
        if len(bars) < 5:
            return signals
        
        # 일봉 데이터는 별도로 로드 필요 (여기서는 가정)
        # 실제로는 백테스트 엔진에서 일봉과 60분봉을 모두 제공해야 함
        
        # 1. 일봉 레벨 업데이트 (매일 한 번)
        # TODO: 일봉 데이터를 별도로 받아서 분석
        
        # 2. 60분봉에서 진입 신호 확인
        entry_signal = self._check_entry_signal(bars, positions, account)
        if entry_signal:
            signals.append(entry_signal)
        
        # 3. Pyramiding 신호 확인
        pyramid_signal = self._check_pyramid_signal(bars, positions, account)
        if pyramid_signal:
            signals.append(pyramid_signal)
        
        # 4. 청산 신호 확인
        exit_signal = self._check_exit_signal(bars, positions)
        if exit_signal:
            signals.append(exit_signal)
        
        return signals
    
    def analyze_daily_candles(self, daily_bars: pd.DataFrame) -> None:
        """
        일봉 데이터 분석 (FVG/OB 탐지)
        
        Args:
            daily_bars: 일봉 DataFrame
        """
        # FVG 탐지
        fvgs = self.ict_analyzer.detect_fvg(daily_bars)
        
        # Order Block 탐지
        obs = self.ict_analyzer.detect_order_blocks(daily_bars)
        
        # 레벨 통합
        self.daily_levels = []
        for fvg in fvgs:
            self.daily_levels.append({
                **fvg,
                "level_type": "FVG"
            })
        for ob in obs:
            self.daily_levels.append({
                **ob,
                "level_type": "OB"
            })
        
        logger.info(f"Daily analysis: {len(fvgs)} FVGs, {len(obs)} OBs found")
    
    def _check_entry_signal(
        self,
        minute_bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> Optional[OrderSignal]:
        """60분봉에서 진입 신호 확인"""
        position = self.get_position(self.symbol, positions)
        if position:
            return None  # 이미 포지션 보유
        
        current_price = minute_bars['close'].iloc[-1]
        
        # 일봉 레벨과 매칭
        for level in self.daily_levels:
            top = level.get('top', 0)
            bottom = level.get('bottom', 0)
            level_type = level.get('type', '')
            
            # 가격대 내 진입 확인
            if bottom <= current_price <= top:
                # Bullish 진입
                if level_type == 'BULLISH':
                    quantity = self._calculate_position_size(account.equity, current_price)
                    if quantity > 0:
                        logger.info(f"🟢 ICT Entry: {current_price:,.0f} (Level: {level.get('level_type')})")
                        return OrderSignal(
                            symbol=self.symbol,
                            side=OrderSide.BUY,
                            quantity=quantity,
                            order_type=OrderType.MARKET
                        )
                
                # Bearish 진입 (공매도)
                elif level_type == 'BEARISH':
                    quantity = self._calculate_position_size(account.equity, current_price)
                    if quantity > 0:
                        logger.info(f"🔴 ICT Entry: {current_price:,.0f} (Level: {level.get('level_type')})")
                        return OrderSignal(
                            symbol=self.symbol,
                            side=OrderSide.SELL,
                            quantity=quantity,
                            order_type=OrderType.MARKET
                        )
        
        return None
    
    def _check_pyramid_signal(
        self,
        minute_bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> Optional[OrderSignal]:
        """Pyramiding 신호 확인"""
        position = self.get_position(self.symbol, positions)
        if not position or position.quantity <= 0:
            return None  # 롱 포지션만
        
        # 추가 매수 횟수 확인
        pyramid_count = self.pyramid_count.get(self.symbol, 0)
        if pyramid_count >= self.pyramid_levels:
            return None
        
        current_price = minute_bars['close'].iloc[-1]
        entry_price = position.avg_price
        
        # 추세 지속 확인 (추가 매수 거리만큼 상승)
        price_increase = (current_price - entry_price) / entry_price
        
        if price_increase >= self.pyramid_distance * (pyramid_count + 1):
            # 추가 매수
            quantity = self._calculate_position_size(account.equity, current_price) // 2  # 절반만
            if quantity > 0:
                logger.info(f"📈 Pyramid Entry: {current_price:,.0f} (Level {pyramid_count + 1})")
                self.pyramid_count[self.symbol] = pyramid_count + 1
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
        
        return None
    
    def _check_exit_signal(
        self,
        minute_bars: pd.DataFrame,
        positions: List[Position]
    ) -> Optional[OrderSignal]:
        """청산 신호 확인"""
        position = self.get_position(self.symbol, positions)
        if not position:
            return None
        
        current_price = minute_bars['close'].iloc[-1]
        entry_price = position.avg_price
        
        # 1. 손절/익절
        if position.quantity > 0:  # 롱 포지션
            pnl_pct = (current_price - entry_price) / entry_price
            
            # 손절
            if pnl_pct <= -self.stop_loss_pct:
                logger.info(f"🔴 Stop Loss: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
            
            # 익절
            if pnl_pct >= self.take_profit_pct:
                logger.info(f"🟢 Take Profit: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
        
        # 2. 볼린저 밴드 하향 돌파
        if len(minute_bars) >= 20:
            bb_lower = self._calculate_bollinger_lower(minute_bars)
            if current_price < bb_lower:
                logger.info(f"🔴 Bollinger Lower Break: {current_price:,.0f}")
                return OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
        
        # 3. 대량 거래 음봉 발생
        if len(minute_bars) >= 2:
            last_bar = minute_bars.iloc[-1]
            avg_volume = minute_bars['volume'].tail(20).mean()
            
            # 음봉 + 거래량 급증
            if (last_bar['close'] < last_bar['open'] and 
                last_bar['volume'] > avg_volume * 2.0):
                logger.info(f"🔴 High Volume Bearish: {current_price:,.0f}")
                # 분할 매도 (50%)
                exit_quantity = position.quantity // 2
                if exit_quantity > 0:
                    return OrderSignal(
                        symbol=self.symbol,
                        side=OrderSide.SELL,
                        quantity=exit_quantity,
                        order_type=OrderType.MARKET
                    )
        
        return None
    
    def _calculate_position_size(self, equity: float, price: float) -> int:
        """포지션 사이즈 계산"""
        # 자본의 5% 투자
        max_investment = equity * 0.05
        quantity = int(max_investment / price)
        return max(1, min(quantity, 100))  # 최소 1주, 최대 100주
    
    def _calculate_bollinger_lower(self, bars: pd.DataFrame, period: int = 20, std: float = 2.0) -> float:
        """볼린저 밴드 하단 계산"""
        sma = bars['close'].rolling(period).mean().iloc[-1]
        std_dev = bars['close'].rolling(period).std().iloc[-1]
        return sma - (std * std_dev)
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(f"[ICT Pyramiding] Order filled: {order.side.value} {order.filled_quantity} @ {order.price}")
        
        # 포지션 청산 시 Pyramiding 카운트 리셋
        if position.quantity == 0:
            self.pyramid_count.pop(self.symbol, None)
