"""
API 요청/응답 스키마
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# 계좌 관련
class AccountResponse(BaseModel):
    """계좌 정보 응답"""
    account_id: str
    balance: float
    equity: float
    margin_used: float
    margin_available: float


class PositionResponse(BaseModel):
    """포지션 응답"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float


# 주문 관련
class OrderRequest(BaseModel):
    """주문 요청"""
    symbol: str
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: int = Field(..., gt=0)
    order_type: str = Field(..., pattern="^(market|limit)$")
    price: Optional[float] = None


class OrderResponse(BaseModel):
    """주문 응답"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Optional[float]
    status: str
    created_at: datetime


# 전략 관련
class StrategyStartRequest(BaseModel):
    """전략 시작 요청"""
    strategy_name: str
    parameters: Dict[str, Any]
    symbols: List[str]


class StrategyResponse(BaseModel):
    """전략 응답"""
    strategy_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    symbols: List[str]
    is_running: bool
    created_at: datetime


# 백테스트 관련
class BacktestRequest(BaseModel):
    """백테스트 요청"""
    strategy_name: str
    parameters: Dict[str, Any]
    symbol: Optional[str] = None  # 단일 종목 전략용 (포트폴리오 전략은 None)
    interval: str = "1d"
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10_000_000
    commission: Optional[float] = 0.0015  # 수수료율 (기본: 0.15%)
    slippage: Optional[float] = 0.001  # 기본 슬리피지 (기본: 0.1%)
    execution_delay: Optional[float] = 1.5  # 체결 지연 시간 (초, 기본: 1.5초)
    use_dynamic_slippage: Optional[bool] = True  # 동적 슬리피지 사용 (기본: True)
    use_tiered_commission: Optional[bool] = True  # 거래대금별 차등 수수료 (기본: True)


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    backtest_id: int
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
    created_at: datetime


# AutoML 관련
class AutoMLRequest(BaseModel):
    """AutoML 요청"""
    strategy_name: str
    symbol: str
    interval: str = "1d"
    start_date: datetime
    end_date: datetime
    method: str = Field(..., pattern="^(grid|random|genetic)$")
    parameter_space: Dict[str, Any]
    n_iterations: Optional[int] = 100
    population_size: Optional[int] = 20
    generations: Optional[int] = 10


class AutoMLResponse(BaseModel):
    """AutoML 응답"""
    automl_id: str
    method: str
    total_results: int
    best_parameters: List[Dict[str, Any]]
    created_at: datetime


# 인증 관련
class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserCreateRequest(BaseModel):
    """사용자 생성 요청"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """사용자 응답"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


# 전략 레지스트리 관련
class StrategyListResponse(BaseModel):
    """전략 목록 응답"""
    name: str
    description: str
    author: str
    version: str


class StrategyDetailResponse(BaseModel):
    """전략 상세 응답"""
    name: str
    description: str
    author: str
    version: str
    parameters: Dict[str, Any]
    class_name: str
    module: str


# 공통
class MessageResponse(BaseModel):
    """메시지 응답"""
    message: str
    success: bool = True
