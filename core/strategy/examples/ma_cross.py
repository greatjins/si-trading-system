"""
이동평균 교차 전략 (Moving Average Crossover)
"""
from typing import List
import pandas as pd

from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy
from utils.types import OHLC, Position, Account, OrderSignal, OrderSide, OrderType, Order
from utils.logger import setup_logger
from utils.signal_logger import get_signal_logger, SignalType

logger = setup_logger(__name__)
signal_logger = get_signal_logger()


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
        bars: pd.DataFrame,
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        새로운 바마다 호출
        
        Args:
            bars: OHLCV DataFrame (timestamp 인덱스, ['open', 'high', 'low', 'close', 'volume', 'value'] 컬럼)
            positions: 현재 포지션 리스트
            account: 계좌 정보
        
        Returns:
            주문 신호 리스트
        """
        signals: List[OrderSignal] = []
        
        # 데이터 검증
        if not self._validate_bars(bars):
            return signals
        
        # 데이터 부족 시 대기
        if len(bars) < self.long_period:
            logger.debug(f"[{self.name}] 데이터 부족: {len(bars)} < {self.long_period}")
            return signals
        
        # 이동평균 계산 (pandas 활용)
        short_ma = bars['close'].rolling(window=self.short_period).mean()
        long_ma = bars['close'].rolling(window=self.long_period).mean()
        
        # 현재 및 이전 값
        current_short_ma = short_ma.iloc[-1]
        current_long_ma = long_ma.iloc[-1]
        prev_short_ma = short_ma.iloc[-2] if len(short_ma) > 1 else current_short_ma
        prev_long_ma = long_ma.iloc[-2] if len(long_ma) > 1 else current_long_ma
        
        current_price = bars['close'].iloc[-1]
        position = self.get_position(self.symbol, positions)
        
        # 골든크로스 감지 (매수 신호)
        golden_cross = prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma
        
        # 데드크로스 감지 (매도 신호)
        dead_cross = prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma
        
        # 현재 상태 로깅 (분석용)
        current_state = "관망"
        if golden_cross:
            current_state = "매수 신호"
        elif dead_cross:
            current_state = "매도 신호"
        
        signal_logger.log_state(
            strategy_name=self.name,
            symbol=self.symbol,
            timestamp=bars.index[-1],
            state=current_state,
            indicators={
                'short_ma': current_short_ma,
                'long_ma': current_long_ma,
                'price': current_price
            }
        )
        
        # 골든크로스 (매수)
        if golden_cross:
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
                    
                    # SignalLogger 사용
                    signal_logger.log_entry_signal(
                        strategy_name=self.name,
                        signal=signal,
                        reason=f"골든크로스: 단기MA({self.short_period})가 장기MA({self.long_period})를 상향 돌파",
                        current_price=current_price,
                        account_equity=account.equity,
                        indicators={
                            '단기MA': current_short_ma,
                            '장기MA': current_long_ma,
                            '이전_단기MA': prev_short_ma,
                            '이전_장기MA': prev_long_ma
                        }
                    )
            else:
                logger.debug(f"[{self.name}] 골든크로스 감지했으나 이미 포지션 보유 중 (중복 진입 방지)")
        
        # 데드크로스 (매도)
        elif dead_cross:
            if position and position.quantity > 0:  # 포지션이 있을 때만 매도
                signal = OrderSignal(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
                signals.append(signal)
                self.last_signal = "sell"
                
                # SignalLogger 사용
                signal_logger.log_exit_signal(
                    strategy_name=self.name,
                    signal=signal,
                    reason=f"데드크로스: 단기MA({self.short_period})가 장기MA({self.long_period})를 하향 돌파",
                    current_price=current_price,
                    position=position,
                    signal_type=SignalType.EXIT
                )
            else:
                logger.debug(f"[{self.name}] 데드크로스 감지했으나 포지션 없음 (청산 불필요)")
        
        return signals
    
    def on_fill(self, order: Order, position: Position) -> None:
        """주문 체결 시 호출"""
        logger.info(
            f"[{self.name}] 주문 체결: {order.side.value} {order.filled_quantity} "
            f"{order.symbol} @ {order.price or 'MARKET'}"
        )
    
    def _validate_bars(self, bars: pd.DataFrame) -> bool:
        """
        바 데이터 유효성 검증
        
        Args:
            bars: OHLCV DataFrame
        
        Returns:
            유효 여부
        """
        # 필수 컬럼 확인
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in bars.columns]
        
        if missing_cols:
            logger.error(f"[{self.name}] 필수 컬럼 누락: {missing_cols}")
            return False
        
        # 빈 DataFrame 확인
        if len(bars) == 0:
            logger.warning(f"[{self.name}] 빈 DataFrame")
            return False
        
        # NaN 확인
        if bars[required_cols].isna().any().any():
            logger.warning(f"[{self.name}] NaN 값 발견")
            return False
        
        return True
    
    def _calculate_quantity(self, equity: float, price: float) -> int:
        """
        매수 수량 계산
        
        Args:
            equity: 계좌 자산
            price: 현재가
        
        Returns:
            매수 수량
        """
        if price <= 0:
            logger.error(f"[{self.name}] 잘못된 가격: {price}")
            return 0
        
        position_value = equity * self.position_size
        quantity = int(position_value / price)
        
        logger.debug(
            f"[{self.name}] 수량 계산: "
            f"자산={equity:,.0f}, 비율={self.position_size:.1%}, "
            f"포지션금액={position_value:,.0f}, 가격={price:,.0f}, 수량={quantity}"
        )
        
        return max(1, quantity)  # 최소 1주
