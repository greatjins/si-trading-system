"""
주문 관련 모델
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """주문 구분"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """주문 유형"""
    MARKET = "market"      # 시장가
    LIMIT = "limit"        # 지정가
    STOP = "stop"          # 정지가
    STOP_LIMIT = "stop_limit"  # 정지지정가


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"        # 대기
    SUBMITTED = "submitted"    # 접수
    PARTIAL = "partial"        # 부분체결
    FILLED = "filled"          # 전량체결
    CANCELLED = "cancelled"    # 취소
    REJECTED = "rejected"      # 거부


@dataclass
class LSOrder:
    """LS증권 주문"""
    
    order_id: str
    """주문번호"""
    
    account_id: str
    """계좌번호"""
    
    symbol: str
    """종목 코드"""
    
    name: str
    """종목명"""
    
    side: OrderSide
    """매수/매도"""
    
    order_type: OrderType
    """주문 유형"""
    
    quantity: int
    """주문 수량"""
    
    price: Optional[float]
    """주문 가격 (시장가는 None)"""
    
    filled_quantity: int = 0
    """체결 수량"""
    
    remaining_quantity: int = 0
    """미체결 수량"""
    
    filled_price: Optional[float] = None
    """체결 가격"""
    
    status: OrderStatus = OrderStatus.PENDING
    """주문 상태"""
    
    order_time: Optional[datetime] = None
    """주문 시간"""
    
    filled_time: Optional[datetime] = None
    """체결 시간"""
    
    message: Optional[str] = None
    """메시지"""


@dataclass
class LSExecution:
    """LS증권 체결"""
    
    execution_id: str
    """체결번호"""
    
    order_id: str
    """주문번호"""
    
    account_id: str
    """계좌번호"""
    
    symbol: str
    """종목 코드"""
    
    name: str
    """종목명"""
    
    side: OrderSide
    """매수/매도"""
    
    quantity: int
    """체결 수량"""
    
    price: float
    """체결 가격"""
    
    amount: float
    """체결 금액"""
    
    commission: float = 0.0
    """수수료"""
    
    tax: float = 0.0
    """세금"""
    
    execution_time: Optional[datetime] = None
    """체결 시간"""
