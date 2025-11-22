"""
리스크 관리자
"""
from typing import List, Optional
from datetime import datetime, date

from utils.types import Account, Position, OrderSignal
from utils.logger import setup_logger
from utils.exceptions import RiskLimitError

logger = setup_logger(__name__)


class RiskManager:
    """
    리스크 관리
    
    - MDD (Maximum Drawdown) 추적 및 제한
    - 포지션 크기 제한
    - 일일 손실 한도
    - 긴급 정지
    """
    
    def __init__(
        self,
        max_mdd: float = 0.20,
        max_position_size: float = 0.10,
        max_daily_loss: float = 0.05,
        initial_capital: float = None
    ):
        """
        Args:
            max_mdd: 최대 MDD (기본: 20%)
            max_position_size: 최대 포지션 크기 (계좌 자산 대비, 기본: 10%)
            max_daily_loss: 최대 일일 손실 (기본: 5%)
            initial_capital: 초기 자본 (MDD 계산용)
        """
        self.max_mdd = max_mdd
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        
        # MDD 추적
        self.initial_capital = initial_capital
        self.peak_equity = initial_capital or 0.0
        self.current_mdd = 0.0
        
        # 일일 손실 추적
        self.daily_start_equity = initial_capital or 0.0
        self.current_date = date.today()
        self.daily_loss = 0.0
        
        # 긴급 정지 플래그
        self.emergency_stop = False
        
        logger.info(
            f"RiskManager initialized: "
            f"max_mdd={max_mdd:.1%}, "
            f"max_position_size={max_position_size:.1%}, "
            f"max_daily_loss={max_daily_loss:.1%}"
        )
    
    def check_risk_limits(self, account: Account) -> bool:
        """
        리스크 한도 확인
        
        Args:
            account: 계좌 정보
        
        Returns:
            리스크 한도 내에 있으면 True
        """
        # 긴급 정지 상태 확인
        if self.emergency_stop:
            logger.warning("Emergency stop is active")
            return False
        
        # MDD 확인
        current_mdd = self._calculate_current_mdd(account.equity)
        if current_mdd >= self.max_mdd:
            logger.error(f"MDD limit exceeded: {current_mdd:.2%} >= {self.max_mdd:.2%}")
            self.trigger_emergency_stop("MDD limit exceeded")
            return False
        
        # 일일 손실 확인
        daily_loss_pct = self._calculate_daily_loss(account.equity)
        if daily_loss_pct >= self.max_daily_loss:
            logger.error(f"Daily loss limit exceeded: {daily_loss_pct:.2%} >= {self.max_daily_loss:.2%}")
            return False
        
        return True
    
    def validate_order(
        self,
        signal: OrderSignal,
        account: Account,
        positions: List[Position]
    ) -> bool:
        """
        주문 검증
        
        Args:
            signal: 주문 신호
            account: 계좌 정보
            positions: 현재 포지션
        
        Returns:
            주문이 유효하면 True
        """
        # 긴급 정지 확인
        if self.emergency_stop:
            logger.warning(f"Order rejected: Emergency stop active")
            return False
        
        # 매수 주문인 경우 포지션 크기 확인
        if signal.side.value == "buy":
            order_value = signal.quantity * (signal.price or 0)
            position_ratio = order_value / account.equity if account.equity > 0 else 0
            
            if position_ratio > self.max_position_size:
                logger.warning(
                    f"Order rejected: Position size {position_ratio:.2%} "
                    f"exceeds limit {self.max_position_size:.2%}"
                )
                return False
        
        return True
    
    def update_equity(self, equity: float, timestamp: datetime = None) -> None:
        """
        자산 업데이트 및 MDD 계산
        
        Args:
            equity: 현재 자산
            timestamp: 타임스탬프
        """
        # 날짜 변경 확인
        current_date = (timestamp or datetime.now()).date()
        if current_date != self.current_date:
            self._reset_daily_tracking(equity)
            self.current_date = current_date
        
        # Peak 업데이트
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        # MDD 계산
        self.current_mdd = self._calculate_current_mdd(equity)
        
        # 일일 손실 계산
        self.daily_loss = self._calculate_daily_loss(equity)
    
    def _calculate_current_mdd(self, equity: float) -> float:
        """
        현재 MDD 계산
        
        Args:
            equity: 현재 자산
        
        Returns:
            MDD (0~1)
        """
        if self.peak_equity == 0:
            return 0.0
        
        drawdown = (self.peak_equity - equity) / self.peak_equity
        return max(0.0, drawdown)
    
    def _calculate_daily_loss(self, equity: float) -> float:
        """
        일일 손실 계산
        
        Args:
            equity: 현재 자산
        
        Returns:
            일일 손실 비율 (0~1)
        """
        if self.daily_start_equity == 0:
            return 0.0
        
        loss = (self.daily_start_equity - equity) / self.daily_start_equity
        return max(0.0, loss)
    
    def _reset_daily_tracking(self, equity: float) -> None:
        """일일 추적 리셋"""
        self.daily_start_equity = equity
        self.daily_loss = 0.0
        logger.info(f"Daily tracking reset: start_equity={equity:,.0f}")
    
    def trigger_emergency_stop(self, reason: str) -> None:
        """
        긴급 정지 트리거
        
        Args:
            reason: 정지 사유
        """
        self.emergency_stop = True
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        logger.critical(f"Current MDD: {self.current_mdd:.2%}")
        logger.critical(f"Peak equity: {self.peak_equity:,.0f}")
    
    def reset_emergency_stop(self) -> None:
        """긴급 정지 해제"""
        self.emergency_stop = False
        logger.info("Emergency stop reset")
    
    def get_risk_status(self) -> dict:
        """
        리스크 상태 조회
        
        Returns:
            리스크 상태 딕셔너리
        """
        return {
            "emergency_stop": self.emergency_stop,
            "current_mdd": self.current_mdd,
            "max_mdd": self.max_mdd,
            "daily_loss": self.daily_loss,
            "max_daily_loss": self.max_daily_loss,
            "peak_equity": self.peak_equity,
            "daily_start_equity": self.daily_start_equity
        }
