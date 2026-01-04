"""
리스크 관리자
"""
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from collections import defaultdict

from utils.types import Account, Position, OrderSignal
from utils.logger import setup_logger
from utils.exceptions import RiskLimitError
from utils.config import config

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
        initial_capital: float = None,
        max_slippage: float = None,
        max_daily_trades_per_symbol: int = None
    ):
        """
        Args:
            max_mdd: 최대 MDD (기본: 20%)
            max_position_size: 최대 포지션 크기 (계좌 자산 대비, 기본: 10%)
            max_daily_loss: 최대 일일 손실 (기본: 5%)
            initial_capital: 초기 자본 (MDD 계산용)
            max_slippage: 최대 허용 슬리피지 비율 (기본: config에서 로드, 없으면 0.5%)
            max_daily_trades_per_symbol: 종목당 일일 최대 거래 횟수 (기본: config에서 로드, 없으면 10회)
        """
        self.max_mdd = max_mdd
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        
        # 슬리피지 제어
        self.max_slippage = max_slippage or config.get("risk.max_slippage", 0.005)  # 기본 0.5%
        
        # 일일 거래 횟수 제한
        self.max_daily_trades_per_symbol = max_daily_trades_per_symbol or config.get("risk.max_daily_trades_per_symbol", 10)
        
        # MDD 추적
        self.initial_capital = initial_capital
        self.peak_equity = initial_capital or 0.0
        self.current_mdd = 0.0
        
        # 일일 손실 추적
        self.daily_start_equity = initial_capital or 0.0
        self.current_date = date.today()
        self.daily_loss = 0.0
        
        # 일일 거래 횟수 추적: {symbol: {date: count}}
        self.daily_trade_counts: Dict[str, Dict[date, int]] = defaultdict(lambda: defaultdict(int))
        
        # 긴급 정지 플래그
        self.emergency_stop = False
        
        logger.info(
            f"RiskManager initialized: "
            f"max_mdd={max_mdd:.1%}, "
            f"max_position_size={max_position_size:.1%}, "
            f"max_daily_loss={max_daily_loss:.1%}, "
            f"max_slippage={self.max_slippage:.1%}, "
            f"max_daily_trades_per_symbol={self.max_daily_trades_per_symbol}"
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
        positions: List[Position],
        current_price: Optional[float] = None
    ) -> bool:
        """
        주문 검증
        
        Args:
            signal: 주문 신호
            account: 계좌 정보
            positions: 현재 포지션
            current_price: 현재 시장 가격 (슬리피지 체크용, None이면 체크 스킵)
        
        Returns:
            주문이 유효하면 True
        """
        # 긴급 정지 확인
        if self.emergency_stop:
            logger.warning(f"Order rejected: Emergency stop active")
            return False
        
        # 일일 거래 횟수 제한 확인
        if not self._check_daily_trade_limit(signal.symbol):
            logger.warning(
                f"Order rejected: Daily trade limit exceeded for {signal.symbol} "
                f"(max: {self.max_daily_trades_per_symbol} trades/day)"
            )
            return False
        
        # 슬리피지 체크 (현재가가 제공된 경우)
        if current_price is not None and signal.price is not None:
            if not self._check_slippage(signal, current_price):
                logger.warning(
                    f"Order rejected: Slippage exceeds limit for {signal.symbol} "
                    f"(max: {self.max_slippage:.2%})"
                )
                return False
        
        # 매수 주문인 경우 포지션 크기 확인
        if signal.side.value == "buy":
            order_value = signal.quantity * (signal.price or current_price or 0)
            if order_value > 0 and account.equity > 0:
                position_ratio = order_value / account.equity
                
                if position_ratio > self.max_position_size:
                    logger.warning(
                        f"Order rejected: Position size {position_ratio:.2%} "
                        f"exceeds limit {self.max_position_size:.2%}"
                    )
                    return False
        
        return True
    
    def _check_slippage(self, signal: OrderSignal, current_price: float) -> bool:
        """
        슬리피지 체크
        
        Args:
            signal: 주문 신호
            current_price: 현재 시장 가격
        
        Returns:
            슬리피지가 허용 범위 내이면 True
        """
        if signal.price is None:
            # 시장가 주문은 슬리피지 체크 스킵 (실제 체결가로 확인 불가)
            return True
        
        if current_price <= 0:
            logger.warning("Invalid current price for slippage check")
            return True
        
        # 슬리피지 계산: |주문가격 - 현재가| / 현재가
        price_diff = abs(signal.price - current_price)
        slippage_ratio = price_diff / current_price
        
        if slippage_ratio > self.max_slippage:
            logger.warning(
                f"Slippage check failed: {slippage_ratio:.2%} > {self.max_slippage:.2%} "
                f"(order_price={signal.price:,.0f}, current_price={current_price:,.0f})"
            )
            return False
        
        logger.debug(
            f"Slippage check passed: {slippage_ratio:.2%} <= {self.max_slippage:.2%} "
            f"(order_price={signal.price:,.0f}, current_price={current_price:,.0f})"
        )
        return True
    
    def _check_daily_trade_limit(self, symbol: str) -> bool:
        """
        일일 거래 횟수 제한 확인
        
        Args:
            symbol: 종목 코드
        
        Returns:
            거래 횟수 제한 내에 있으면 True
        """
        today = date.today()
        
        # 날짜가 변경되었으면 오래된 데이터 정리
        if today != self.current_date:
            self._cleanup_old_trade_counts(today)
        
        # 오늘의 거래 횟수 확인
        today_count = self.daily_trade_counts[symbol][today]
        
        if today_count >= self.max_daily_trades_per_symbol:
            logger.warning(
                f"Daily trade limit reached for {symbol}: "
                f"{today_count}/{self.max_daily_trades_per_symbol} trades today"
            )
            return False
        
        return True
    
    def record_trade(self, symbol: str, trade_date: Optional[date] = None) -> None:
        """
        거래 발생 기록 (주문 체결 시 호출)
        
        Args:
            symbol: 종목 코드
            trade_date: 거래 날짜 (None이면 오늘)
        """
        if trade_date is None:
            trade_date = date.today()
        
        self.daily_trade_counts[symbol][trade_date] += 1
        
        logger.debug(
            f"Trade recorded for {symbol}: "
            f"{self.daily_trade_counts[symbol][trade_date]}/{self.max_daily_trades_per_symbol} trades today"
        )
    
    def _cleanup_old_trade_counts(self, current_date: date) -> None:
        """
        오래된 거래 횟수 데이터 정리
        
        Args:
            current_date: 현재 날짜
        """
        # 30일 이상 오래된 데이터 삭제
        cutoff_date = current_date - timedelta(days=30)
        
        for symbol in list(self.daily_trade_counts.keys()):
            for trade_date in list(self.daily_trade_counts[symbol].keys()):
                if trade_date < cutoff_date:
                    del self.daily_trade_counts[symbol][trade_date]
            
            # 빈 딕셔너리 제거
            if not self.daily_trade_counts[symbol]:
                del self.daily_trade_counts[symbol]
    
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
        
        # 오래된 거래 횟수 데이터 정리
        self._cleanup_old_trade_counts(self.current_date)
        
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
        # 오늘의 거래 횟수 집계
        today = date.today()
        today_trade_counts = {
            symbol: counts[today]
            for symbol, counts in self.daily_trade_counts.items()
            if today in counts
        }
        
        return {
            "emergency_stop": self.emergency_stop,
            "current_mdd": self.current_mdd,
            "max_mdd": self.max_mdd,
            "daily_loss": self.daily_loss,
            "max_daily_loss": self.max_daily_loss,
            "peak_equity": self.peak_equity,
            "daily_start_equity": self.daily_start_equity,
            "max_slippage": self.max_slippage,
            "max_daily_trades_per_symbol": self.max_daily_trades_per_symbol,
            "today_trade_counts": today_trade_counts
        }
