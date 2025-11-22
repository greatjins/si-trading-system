"""
시세 관련 모델
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class LSOHLC:
    """LS증권 OHLC 데이터"""
    
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    value: float = 0.0


@dataclass
class LSQuote:
    """LS증권 현재가"""
    
    symbol: str
    name: str
    price: float
    change: float
    change_rate: float
    volume: int
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    timestamp: datetime


@dataclass
class LSOrderbook:
    """LS증권 호가"""
    
    symbol: str
    ask_prices: List[float]
    ask_volumes: List[int]
    bid_prices: List[float]
    bid_volumes: List[int]
    timestamp: datetime
