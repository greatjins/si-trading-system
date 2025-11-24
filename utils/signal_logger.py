"""
신호 로깅 및 알림 유틸리티
"""
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from utils.types import OrderSignal, Position, OrderSide
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SignalType(Enum):
    """신호 타입"""
    ENTRY = "entry"  # 진입
    EXIT = "exit"  # 청산
    STOP_LOSS = "stop_loss"  # 손절
    TAKE_PROFIT = "take_profit"  # 익절
    TRAILING_STOP = "trailing_stop"  # 트레일링 스탑
    EMERGENCY = "emergency"  # 긴급 청산


class SignalLogger:
    """
    신호 로깅 및 외부 알림 관리
    
    매수/매도/청산 시점마다 상세한 로그를 남기고,
    선택적으로 외부 알림(Telegram, Slack 등)을 전송합니다.
    """
    
    def __init__(self, notification_hook: Optional[Callable] = None):
        """
        Args:
            notification_hook: 외부 알림 함수 (선택)
                시그니처: async def hook(message: str, level: str) -> None
        """
        self.notification_hook = notification_hook
        self.signal_history = []
    
    def log_entry_signal(
        self,
        strategy_name: str,
        signal: OrderSignal,
        reason: str,
        current_price: float,
        account_equity: float,
        indicators: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        진입 신호 로깅
        
        Args:
            strategy_name: 전략 이름
            signal: 주문 신호
            reason: 신호 발생 이유
            current_price: 현재가
            account_equity: 계좌 자산
            indicators: 기술적 지표 값 (선택)
        """
        side_text = "매수" if signal.side == OrderSide.BUY else "매도"
        
        message = (
            f"[{strategy_name}] {side_text} 진입 신호\n"
            f"종목: {signal.symbol}\n"
            f"수량: {signal.quantity:,}주\n"
            f"현재가: {current_price:,.0f}원\n"
            f"예상 금액: {signal.quantity * current_price:,.0f}원\n"
            f"계좌 자산: {account_equity:,.0f}원\n"
            f"신호 이유: {reason}"
        )
        
        if indicators:
            message += "\n지표 값:"
            for key, value in indicators.items():
                if isinstance(value, float):
                    message += f"\n  - {key}: {value:.2f}"
                else:
                    message += f"\n  - {key}: {value}"
        
        logger.info(message)
        
        # 신호 기록
        self._record_signal(SignalType.ENTRY, strategy_name, signal, reason, current_price, indicators)
        
        # 외부 알림
        if self.notification_hook:
            try:
                import asyncio
                asyncio.create_task(self.notification_hook(message, "info"))
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def log_exit_signal(
        self,
        strategy_name: str,
        signal: OrderSignal,
        reason: str,
        current_price: float,
        position: Position,
        signal_type: SignalType = SignalType.EXIT
    ) -> None:
        """
        청산 신호 로깅
        
        Args:
            strategy_name: 전략 이름
            signal: 주문 신호
            reason: 신호 발생 이유
            current_price: 현재가
            position: 현재 포지션
            signal_type: 신호 타입 (EXIT, STOP_LOSS, TAKE_PROFIT 등)
        """
        pnl = (current_price - position.avg_price) * signal.quantity
        pnl_pct = ((current_price - position.avg_price) / position.avg_price) * 100
        
        signal_type_text = {
            SignalType.EXIT: "청산",
            SignalType.STOP_LOSS: "손절",
            SignalType.TAKE_PROFIT: "익절",
            SignalType.TRAILING_STOP: "트레일링 스탑",
            SignalType.EMERGENCY: "긴급 청산"
        }.get(signal_type, "청산")
        
        message = (
            f"[{strategy_name}] {signal_type_text} 신호\n"
            f"종목: {signal.symbol}\n"
            f"수량: {signal.quantity:,}주\n"
            f"현재가: {current_price:,.0f}원\n"
            f"평균단가: {position.avg_price:,.0f}원\n"
            f"손익: {pnl:+,.0f}원 ({pnl_pct:+.2f}%)\n"
            f"신호 이유: {reason}"
        )
        
        # 손익에 따라 로그 레벨 조정
        if signal_type == SignalType.EMERGENCY:
            logger.critical(message)
        elif signal_type == SignalType.STOP_LOSS:
            logger.warning(message)
        elif pnl > 0:
            logger.info(message)
        else:
            logger.warning(message)
        
        # 신호 기록
        self._record_signal(signal_type, strategy_name, signal, reason, current_price, {
            'avg_price': position.avg_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        # 외부 알림
        if self.notification_hook:
            try:
                import asyncio
                level = "critical" if signal_type == SignalType.EMERGENCY else "warning" if pnl < 0 else "info"
                asyncio.create_task(self.notification_hook(message, level))
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def log_state(
        self,
        strategy_name: str,
        symbol: str,
        timestamp: datetime,
        state: str,
        indicators: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        전략 상태 로깅 (분석/시각화용)
        
        Args:
            strategy_name: 전략 이름
            symbol: 종목 코드
            timestamp: 타임스탬프
            state: 상태 (매수/매도/관망)
            indicators: 지표 값
        """
        record = {
            'timestamp': timestamp,
            'strategy': strategy_name,
            'symbol': symbol,
            'state': state,
            'indicators': indicators or {}
        }
        
        self.signal_history.append(record)
        
        logger.debug(
            f"[{strategy_name}] 상태: {state} | "
            f"종목: {symbol} | "
            f"시간: {timestamp}"
        )
    
    def _record_signal(
        self,
        signal_type: SignalType,
        strategy_name: str,
        signal: OrderSignal,
        reason: str,
        current_price: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """신호 기록 저장"""
        record = {
            'timestamp': datetime.now(),
            'signal_type': signal_type.value,
            'strategy': strategy_name,
            'symbol': signal.symbol,
            'side': signal.side.value,
            'quantity': signal.quantity,
            'price': current_price,
            'reason': reason,
            'metadata': metadata or {}
        }
        
        self.signal_history.append(record)
    
    def get_signal_history(self) -> list:
        """신호 기록 조회"""
        return self.signal_history.copy()
    
    def clear_history(self) -> None:
        """신호 기록 초기화"""
        self.signal_history.clear()


# 전역 SignalLogger 인스턴스
_global_signal_logger = SignalLogger()


def get_signal_logger() -> SignalLogger:
    """전역 SignalLogger 인스턴스 반환"""
    return _global_signal_logger


def set_notification_hook(hook: Callable) -> None:
    """외부 알림 hook 설정"""
    _global_signal_logger.notification_hook = hook
