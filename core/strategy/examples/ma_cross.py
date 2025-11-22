"""
이동평균 교차 전략 (Moving Average Crossover)
"""
from typing import List
import pandas as pd

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order
from utils.logger import setup_logger

logger = setup_logger(__name__)


@strategy(
    name="MACrossStrategy",
    description="이동평균 교차 전략 - 골든크로스/데드크로스 기반 매매",
    author="LS HTS Team",
    version="1.0.0",
    parameters={
        "symbol": {
            "type": "str",
            "default": "005930",
            "description": "종목 코드"
        },
        "short_period": {
            "type": "int",
            "default": 5,
            "min": 2,
            "max": 50,
            "description": "단기 이동평균 기간"
        },
        "long_period": {
            "type": "int",
            "default": 20,
            "min": 10,
            "max": 200,
            "description": "장기 이동평균 기간"
        },
        "position_size": {
            "type": "float",
            "default": 0.1,
            "min": 0.01,
            "max": 1.0,
            "description": "포지션 크기 (계좌 자산 대비 비율)"
        }
    }
)
class MACrossStrategy(BaseStrategy):
    """
    이동평균 교차 전략
    
    - 단기 이동평균이 장기 이동평균을 상향 돌파 → 매수 (골든크로스)
    - 단기 이동평균이 장기 이동평균을 하향 돌파 → 매도 (데드크로스)
    """
    
    STRATEGY_NAME = "MACrossStrategy"
    DESCRIPTION = "이동평균 교차 전략 - 골든크로스/데드크로스 기반 매매"
    AUTHOR = "LS HTS Team"
    VERSION = "1.0.0"
    
    def __init__(self, params: dict):
        super().__init__(params)
        
        self.symbol = self.get_param("symbol", "005930")
        self.short_period = self.get_param("short_period", 5)
        self.long_period = self.get_param("long_period", 20)
        self.position_size = self.get_param("position_size", 0.1)
        
        # 상태 변수
        self.last_signal = None  # "buy", "sell", None
    
    def on_bar(
        self,
        bars: List[OHLC],
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """새로운 바마다 호출"""
        signals: List[OrderSignal] = []
        
        # 데이터 부족 시 대기
        if len(bars) < self.long_period:
            return signals
        
        # 종가 데이터 추출
        closes = [bar.close for bar in bars]
        
        # 이동평균 계산
        short_ma = sum(closes[-self.short_period:]) / self.short_period
        long_ma = sum(closes[-self.long_period:]) / self.long_period
        
        # 이전 이동평균 (교차 감지용)
        prev_short_ma = sum(closes[-self.short_period-1:-1]) / self.short_period
        prev_long_ma = sum(closes[-self.long_period-1:-1]) / self.long_period
        
        current_price = bars[-1].close
        position = self.get_position(self.symbol, positions)
        
        # 골든크로스 (매수 신호)
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            if not position:  # 포지션이 없을 때만 매수
                quantity = self._calculate_quantity(account.equity, current_price)
                
                if quantity > 0:
                    signal = OrderSignal(
                        symbol=self.symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                    signals.append(signal)
                    self.last_signal = "buy"
                    
                    logger.info(f"[{self.name}] 골든크로스 매수 신호: {self.symbol}, 수량: {quantity}")
        
        # 데드크로스 (매도 신호)
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            if position and position.quantity > 0:  # 포지션이 있을 때만 매도
                signal = OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
                signals.append(signal)
                self.last_signal = "sell"
                
                logger.info(f"[{self.name}] 데드크로스 매도 신호: {self.symbol}, 수량: {position.quantity}")
        
        return signals
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(
            f"[{self.name}] 주문 체결: {order.side.value} {order.filled_quantity} "
            f"{order.symbol} @ {order.price or 'MARKET'}"
        )
    
    def _calculate_quantity(self, equity: float, price: float) -> int:
        """
        매수 수량 계산
        
        Args:
            equity: 계좌 자산
            price: 현재가
        
        Returns:
            매수 수량
        """
        position_value = equity * self.position_size
        quantity = int(position_value / price)
        return quantity
