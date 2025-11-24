"""
핵심 데이터 타입 정의
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class OrderSide(Enum):
    """주문 방향"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """주문 유형"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class OHLC:
    """OHLC 데이터 (거래대금 포함)"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    value: Optional[float] = None  # 거래대금 (volume * price)

    def __post_init__(self) -> None:
        """데이터 검증 및 value 계산"""
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be less than Low ({self.low})")
        if self.open < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        
        # value가 없으면 volume * close로 계산
        if self.value is None:
            self.value = self.volume * self.close


@dataclass
class Order:
    """주문 정보"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float]
    filled_quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    def is_filled(self) -> bool:
        """주문이 완전히 체결되었는지 확인"""
        return self.status == OrderStatus.FILLED

    def is_active(self) -> bool:
        """주문이 활성 상태인지 확인"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]


@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

    def total_value(self) -> float:
        """포지션 총 가치"""
        return self.quantity * self.current_price

    def update_price(self, new_price: float) -> None:
        """현재가 업데이트 및 미실현 손익 재계산"""
        self.current_price = new_price
        self.unrealized_pnl = (new_price - self.avg_price) * self.quantity


@dataclass
class Account:
    """계좌 정보"""
    account_id: str
    balance: float
    equity: float
    margin_used: float
    margin_available: float

    def buying_power(self) -> float:
        """매수 가능 금액"""
        return self.margin_available


@dataclass
class OrderSignal:
    """전략에서 생성하는 주문 신호"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    def to_order(self, order_id: str) -> Order:
        """신호를 주문으로 변환"""
        return Order(
            order_id=order_id,
            symbol=self.symbol,
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity,
            price=self.price,
            filled_quantity=0,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )


@dataclass
class Trade:
    """체결된 거래 기록"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    commission: float
    timestamp: datetime

    def total_cost(self) -> float:
        """총 비용 (수수료 포함)"""
        return (self.quantity * self.price) + self.commission


@dataclass
class BacktestResult:
    """백테스트 결과"""
    strategy_name: str
    parameters: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_equity: float
    total_return: float
    mdd: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    equity_curve: List[float]
    trades: List[Trade]

    def summary(self) -> Dict[str, Any]:
        """결과 요약"""
        return {
            "strategy": self.strategy_name,
            "period": f"{self.start_date} ~ {self.end_date}",
            "total_return": f"{self.total_return:.2%}",
            "mdd": f"{self.mdd:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "win_rate": f"{self.win_rate:.2%}",
            "profit_factor": f"{self.profit_factor:.2f}",
            "total_trades": self.total_trades
        }
