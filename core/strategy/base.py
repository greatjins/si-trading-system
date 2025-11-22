"""
전략 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from utils.types import OHLC, Position, Account, OrderSignal, Order
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """
    모든 트레이딩 전략의 기본 클래스
    
    전략은 브로커 API를 직접 호출하지 않고,
    엔진으로부터 데이터를 받아 주문 신호만 반환합니다.
    
    이를 통해 전략 코드가 브로커 구현으로부터 완전히 분리됩니다.
    """
    
    def __init__(self, params: Dict[str, Any]):
        """
        Args:
            params: 전략 파라미터 딕셔너리
        """
        self.params = params
        self.name = self.__class__.__name__
        
        logger.info(f"Strategy initialized: {self.name}")
        logger.debug(f"Parameters: {params}")
    
    @abstractmethod
    def on_bar(
        self,
        bars: List[OHLC],
        positions: List[Position],
        account: Account
    ) -> List[OrderSignal]:
        """
        새로운 바마다 호출됨 (백테스트) 또는 가격 업데이트마다 호출됨 (실시간)
        
        Args:
            bars: 과거 OHLC 바 리스트 (가장 최근이 마지막)
            positions: 현재 보유 포지션 리스트
            account: 현재 계좌 상태
        
        Returns:
            주문 신호 리스트 (매수/매도/청산)
        
        Note:
            - 전략은 브로커 API를 직접 호출하지 않습니다
            - 엔진이 제공한 데이터만 사용합니다
            - 주문 신호만 반환하며, 실제 주문은 엔진이 처리합니다
        """
        pass
    
    @abstractmethod
    def on_fill(self, order: Order, position: Position) -> None:
        """
        주문이 체결될 때 호출됨
        
        Args:
            order: 체결된 주문
            position: 업데이트된 포지션
        
        Note:
            전략 상태 업데이트나 로깅에 사용
        """
        pass
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """
        파라미터 조회
        
        Args:
            key: 파라미터 키
            default: 기본값
        
        Returns:
            파라미터 값
        """
        return self.params.get(key, default)
    
    def set_param(self, key: str, value: Any) -> None:
        """
        파라미터 설정
        
        Args:
            key: 파라미터 키
            value: 파라미터 값
        """
        self.params[key] = value
    
    def get_position(self, symbol: str, positions: List[Position]) -> Optional[Position]:
        """
        특정 종목의 포지션 조회
        
        Args:
            symbol: 종목코드
            positions: 포지션 리스트
        
        Returns:
            포지션 (없으면 None)
        """
        for position in positions:
            if position.symbol == symbol:
                return position
        return None
    
    def has_position(self, symbol: str, positions: List[Position]) -> bool:
        """
        특정 종목의 포지션 보유 여부
        
        Args:
            symbol: 종목코드
            positions: 포지션 리스트
        
        Returns:
            보유 여부
        """
        return self.get_position(symbol, positions) is not None
    
    def __repr__(self) -> str:
        return f"{self.name}({self.params})"
