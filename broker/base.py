"""
모든 브로커 어댑터의 추상 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator
from datetime import datetime

from utils.types import OHLC, Order, Position, Account


class BrokerBase(ABC):
    """
    모든 증권사 Adapter가 구현해야 하는 인터페이스
    
    이 추상 클래스를 상속하여 각 증권사별 Adapter를 구현합니다.
    전략 코드는 이 인터페이스에만 의존하므로, 브로커 교체 시에도
    전략 코드 수정이 필요 없습니다.
    """
    
    @abstractmethod
    async def get_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """
        과거 OHLC 데이터 가져오기
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격 ("1d", "1m", "5m", "10m", "30m")
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            OHLC 데이터 리스트 (시간순 정렬)
        """
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """
        현재 시장 가격 가져오기
        
        Args:
            symbol: 종목 코드
        
        Returns:
            현재가
        """
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> str:
        """
        새 주문 제출
        
        Args:
            order: 주문 정보
        
        Returns:
            주문 ID
        """
        pass

    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        기존 주문 취소
        
        Args:
            order_id: 주문 ID
        
        Returns:
            취소 성공 여부
        """
        pass
    
    @abstractmethod
    async def amend_order(
        self,
        order_id: str,
        new_price: float,
        new_quantity: int
    ) -> bool:
        """
        기존 주문 수정
        
        Args:
            order_id: 주문 ID
            new_price: 새로운 가격
            new_quantity: 새로운 수량
        
        Returns:
            수정 성공 여부
        """
        pass
    
    @abstractmethod
    async def get_account(self) -> Account:
        """
        계좌 정보 가져오기
        
        Returns:
            계좌 정보 (잔액, 자산 등)
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        모든 보유 포지션 가져오기
        
        Returns:
            포지션 리스트
        """
        pass
    
    @abstractmethod
    async def get_open_orders(self) -> List[Order]:
        """
        모든 미체결 주문 가져오기
        
        Returns:
            미체결 주문 리스트
        """
        pass
    
    @abstractmethod
    async def stream_realtime(
        self,
        symbols: List[str]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        WebSocket을 통한 실시간 가격 업데이트 스트리밍
        
        Args:
            symbols: 구독할 종목 코드 리스트
        
        Yields:
            실시간 가격 업데이트 딕셔너리
            {
                "symbol": str,
                "price": float,
                "volume": int,
                "timestamp": datetime
            }
        """
        pass
