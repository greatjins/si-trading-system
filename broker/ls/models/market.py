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


@dataclass
class LSFinancialInfo:
    """LS증권 재무 정보 (t3320)"""
    
    # 기본 정보
    symbol: str
    company: str
    market: str
    market_name: str
    
    # 주식 정보
    price: float
    prev_close: float
    market_cap: float  # 시가총액
    shares: float  # 주식수
    capital: float  # 자본금
    par_value: float  # 액면가
    
    # 재무 지표
    per: Optional[float] = None  # PER
    eps: Optional[float] = None  # EPS
    pbr: Optional[float] = None  # PBR
    bps: Optional[float] = None  # BPS
    roa: Optional[float] = None  # ROA
    roe: Optional[float] = None  # ROE
    
    # 추가 지표
    sps: Optional[float] = None  # SPS (주당매출액)
    cps: Optional[float] = None  # CPS (주당현금흐름)
    ebitda: Optional[float] = None  # EBITDA
    ev_ebitda: Optional[float] = None  # EV/EBITDA
    peg: Optional[float] = None  # PEG
    
    # 배당 정보
    dividend: Optional[float] = None  # 배당금
    dividend_yield: Optional[float] = None  # 배당수익률
    
    # 외국인 정보
    foreign_ratio: Optional[float] = None  # 외국인지분율
    
    # 결산 정보
    fiscal_year: Optional[str] = None  # 최근결산년도
    fiscal_month: Optional[str] = None  # 결산월
    fiscal_ym: Optional[str] = None  # 최근결산년월
    
    # 기타
    group_name: Optional[str] = None  # 그룹명
    homepage: Optional[str] = None  # 홈페이지
    address: Optional[str] = None  # 본사주소
    tel: Optional[str] = None  # 본사전화번호
