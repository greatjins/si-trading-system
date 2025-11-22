"""
계좌 관련 모델
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class LSAccount:
    """LS증권 계좌 정보"""
    
    account_id: str
    """계좌번호"""
    
    balance: float
    """예수금 (현금)"""
    
    equity: float
    """총 평가금액 (예수금 + 주식평가금액)"""
    
    stock_value: float
    """주식 평가금액"""
    
    profit_loss: float
    """평가 손익"""
    
    profit_loss_rate: float
    """수익률 (%)"""
    
    margin_used: float = 0.0
    """사용 증거금"""
    
    margin_available: float = 0.0
    """주문 가능 금액"""
    
    deposit: float = 0.0
    """예탁금"""
    
    withdraw_available: float = 0.0
    """출금 가능 금액"""
    
    updated_at: Optional[datetime] = None
    """업데이트 시간"""


@dataclass
class LSPosition:
    """LS증권 보유 종목"""
    
    symbol: str
    """종목 코드"""
    
    name: str
    """종목명"""
    
    quantity: int
    """보유 수량"""
    
    available_quantity: int
    """매도 가능 수량"""
    
    avg_price: float
    """평균 매입가"""
    
    current_price: float
    """현재가"""
    
    eval_amount: float
    """평가 금액"""
    
    profit_loss: float
    """평가 손익"""
    
    profit_loss_rate: float
    """수익률 (%)"""
    
    buy_amount: float
    """매입 금액"""
    
    loan_date: Optional[str] = None
    """대출일 (신용거래)"""
    
    updated_at: Optional[datetime] = None
    """업데이트 시간"""
