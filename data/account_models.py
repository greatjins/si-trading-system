"""
계좌 관리 모델
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class BrokerType(str, enum.Enum):
    """증권사/거래소 타입"""
    LS = "ls"  # LS증권
    KIWOOM = "kiwoom"  # 키움증권
    KIS = "kis"  # 한국투자증권
    UPBIT = "upbit"  # 업비트
    BINANCE = "binance"  # 바이낸스
    MOCK = "mock"  # 모의투자


class AccountType(str, enum.Enum):
    """계좌 타입"""
    REAL = "real"  # 실계좌
    PAPER = "paper"  # 모의투자


class TradingAccount(Base):
    """거래 계좌 모델"""
    __tablename__ = "trading_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 사용자 ID
    name = Column(String, nullable=False)  # 계좌 이름 (예: "LS증권 모의투자")
    broker = Column(SQLEnum(BrokerType), nullable=False)  # 증권사
    account_type = Column(SQLEnum(AccountType), nullable=False)  # 계좌 타입
    account_number = Column(String, nullable=False)  # 계좌번호
    
    # API 인증 정보 (암호화 저장 필요)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    app_key = Column(String, nullable=True)  # 한국투자증권용
    app_secret = Column(String, nullable=True)  # 한국투자증권용
    
    # 상태
    is_active = Column(Boolean, default=True)  # 활성화 여부
    is_default = Column(Boolean, default=False)  # 기본 계좌 여부
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_connected_at = Column(DateTime, nullable=True)  # 마지막 연결 시간


# Pydantic 스키마
class TradingAccountCreate(BaseModel):
    """계좌 생성 요청"""
    name: str = Field(..., description="계좌 이름")
    broker: BrokerType = Field(..., description="증권사/거래소")
    account_type: AccountType = Field(..., description="계좌 타입")
    account_number: str = Field(..., description="계좌번호")
    api_key: Optional[str] = Field(None, description="API Key")
    api_secret: Optional[str] = Field(None, description="API Secret")
    app_key: Optional[str] = Field(None, description="App Key (한국투자증권)")
    app_secret: Optional[str] = Field(None, description="App Secret (한국투자증권)")
    is_default: bool = Field(False, description="기본 계좌로 설정")


class TradingAccountUpdate(BaseModel):
    """계좌 수정 요청"""
    name: Optional[str] = None
    account_number: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class TradingAccountResponse(BaseModel):
    """계좌 응답 (민감정보 마스킹)"""
    id: int
    user_id: int
    name: str
    broker: BrokerType
    account_type: AccountType
    account_number_masked: str  # 마스킹된 계좌번호
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    last_connected_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TradingAccountDetail(TradingAccountResponse):
    """계좌 상세 정보 (API 키 포함, 마스킹)"""
    api_key_masked: Optional[str] = None
    has_api_secret: bool = False
    has_app_key: bool = False
    has_app_secret: bool = False
