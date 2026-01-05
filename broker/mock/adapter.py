"""
테스트 및 개발용 Mock 브로커
"""
import asyncio
from typing import List, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
import random
from uuid import uuid4

from broker.base import BrokerBase
from utils.types import OHLC, Order, Position, Account, OrderStatus
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MockBroker(BrokerBase):
    """
    테스트용 Mock 브로커
    
    실제 API 호출 없이 시뮬레이션된 데이터를 반환합니다.
    """
    
    def __init__(self, initial_balance: float = 10_000_000.0):
        """
        Args:
            initial_balance: 초기 잔액 (기본: 1천만원)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.base_prices: Dict[str, float] = {}
        
        logger.info(f"MockBroker initialized with balance: {initial_balance:,.0f}")
    
    async def get_ohlc(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLC]:
        """Mock OHLC 데이터 생성"""
        logger.info(f"Fetching OHLC for {symbol}, interval={interval}")
        
        # 시간 간격 파싱
        interval_minutes = self._parse_interval(interval)
        
        # 데이터 생성
        ohlc_list: List[OHLC] = []
        current_time = start_date
        base_price = self._get_base_price(symbol)
        
        while current_time <= end_date:
            # 랜덤 가격 변동 (±2%)
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            high_price = open_price * (1 + random.uniform(0, 0.03))
            low_price = open_price * (1 - random.uniform(0, 0.03))
            close_price = open_price * (1 + random.uniform(-0.02, 0.02))
            volume = random.randint(100000, 1000000)
            
            ohlc_list.append(OHLC(
                symbol=symbol,
                timestamp=current_time,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume
            ))
            
            base_price = close_price
            current_time += timedelta(minutes=interval_minutes)
        
        logger.info(f"Generated {len(ohlc_list)} OHLC bars")
        return ohlc_list

    
    def _parse_interval(self, interval: str) -> int:
        """시간 간격을 분 단위로 변환"""
        if interval == "1d":
            return 1440  # 1일 = 1440분
        elif interval.endswith("m"):
            return int(interval[:-1])
        else:
            raise ValueError(f"Unsupported interval: {interval}")
    
    def _get_base_price(self, symbol: str) -> float:
        """종목의 기준 가격 반환"""
        if symbol not in self.base_prices:
            # 랜덤 기준 가격 생성 (10,000 ~ 100,000원)
            self.base_prices[symbol] = random.uniform(10000, 100000)
        return self.base_prices[symbol]
    
    async def get_current_price(self, symbol: str) -> float:
        """현재가 반환 (기준가 ±1% 변동)"""
        base_price = self._get_base_price(symbol)
        current_price = base_price * (1 + random.uniform(-0.01, 0.01))
        return round(current_price, 2)
    
    async def place_order(self, order: Order) -> str:
        """주문 제출 시뮬레이션"""
        order_id = str(uuid4())
        order.order_id = order_id
        order.status = OrderStatus.SUBMITTED
        
        self.orders[order_id] = order
        logger.info(f"Order placed: {order_id}, {order.side.value} {order.quantity} {order.symbol}")
        
        # 즉시 체결 시뮬레이션 (비동기)
        asyncio.create_task(self._simulate_fill(order_id))
        
        return order_id
    
    async def _simulate_fill(self, order_id: str) -> None:
        """주문 체결 시뮬레이션"""
        await asyncio.sleep(0.1)  # 0.1초 후 체결
        
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        order.filled_quantity = order.quantity
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now()
        
        logger.info(f"Order filled: {order_id}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.is_active():
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            logger.info(f"Order cancelled: {order_id}")
            return True
        
        return False
    
    async def amend_order(
        self,
        order_id: str,
        new_price: float,
        new_quantity: int
    ) -> bool:
        """주문 수정"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.is_active():
            order.price = new_price
            order.quantity = new_quantity
            order.updated_at = datetime.now()
            logger.info(f"Order amended: {order_id}")
            return True
        
        return False

    
    async def get_account(self) -> Account:
        """계좌 정보 반환"""
        equity = self.balance
        
        # 포지션 평가액 추가
        for position in self.positions.values():
            equity += position.total_value()
        
        return Account(
            account_id="MOCK_ACCOUNT",
            balance=self.balance,
            equity=equity,
            margin_used=0.0,
            margin_available=self.balance
        )
    
    async def get_positions(self) -> List[Position]:
        """보유 포지션 반환"""
        return list(self.positions.values())
    
    async def get_open_orders(self) -> List[Order]:
        """미체결 주문 반환"""
        return [order for order in self.orders.values() if order.is_active()]
    
    async def get_orders(self) -> List[Order]:
        """모든 주문 내역 반환 (체결/미체결 포함)"""
        return list(self.orders.values())
    
    async def stream_realtime(
        self,
        symbols: List[str]
    ) -> AsyncIterator[Dict[str, Any]]:
        """실시간 가격 스트리밍 시뮬레이션"""
        logger.info(f"Starting realtime stream for {symbols}")
        
        try:
            while True:
                for symbol in symbols:
                    price = await self.get_current_price(symbol)
                    
                    yield {
                        "symbol": symbol,
                        "price": price,
                        "volume": random.randint(1000, 10000),
                        "timestamp": datetime.now()
                    }
                
                await asyncio.sleep(1)  # 1초마다 업데이트
        except asyncio.CancelledError:
            logger.info("Realtime stream cancelled")
