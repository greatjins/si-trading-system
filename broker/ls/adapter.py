"""
LS증권 브로커 어댑터
"""
from typing import List, Dict, Any, AsyncIterator
from datetime import datetime

from broker.base import BrokerBase
from broker.ls.client import LSClient
from broker.ls.realtime import LSRealtimeService
from utils.types import OHLC, Order, Position, Account
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class LSAdapter(BrokerBase):
    """
    LS증권 브로커 어댑터
    
    BrokerBase 인터페이스를 구현하여 LS증권 API를 추상화합니다.
    """
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        account_id: str = None,
        paper_trading: bool = None
    ):
        """
        Args:
            api_key: API 키 (None이면 config에서 로드)
            api_secret: API 시크릿 (None이면 config에서 로드)
            account_id: 계좌번호 (None이면 config에서 로드)
            paper_trading: 모의투자 여부 (None이면 config에서 로드)
        """
        # 설정에서 로드
        self.api_key = api_key or config.get("ls.appkey") or config.get("broker.api_key")
        self.api_secret = api_secret or config.get("ls.appsecretkey") or config.get("broker.api_secret")
        self.account_id = account_id or config.get("ls.account_id") or config.get("broker.account_id")
        self.paper_trading = paper_trading if paper_trading is not None else config.get("ls.paper_trading", False)
        
        if not all([self.api_key, self.api_secret, self.account_id]):
            raise ValueError("API credentials not provided")
        
        # 클라이언트 초기화
        self.client = LSClient(
            appkey=self.api_key,
            appsecretkey=self.api_secret,
            account_id=self.account_id,
            paper_trading=self.paper_trading
        )
        
        # 서비스 초기화
        from broker.ls.services import LSAccountService, LSOrderService, LSMarketService
        
        self.account_service = LSAccountService(self.client)
        self.order_service = LSOrderService(self.client)
        self.market_service = LSMarketService(self.client)
        self.realtime_service = None  # TODO: 실시간 서비스 구현
        
        mode = "모의투자" if self.paper_trading else "실거래"
        logger.info(f"LSAdapter initialized for account: {self.account_id} ({mode})")
    
    async def __aenter__(self) -> "LSAdapter":
        """비동기 컨텍스트 매니저 진입"""
        await self.client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """비동기 컨텍스트 매니저 종료"""
        await self.client.close()
    
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
            interval: 시간 간격 ("1d", "1m", "5m", "10m", "30m", "60m")
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            OHLC 데이터 리스트
        """
        logger.info(f"Getting OHLC: {symbol}, {interval}")
        
        if interval == "1d":
            ohlc_list = await self.market_service.get_daily_ohlc(symbol, start_date, end_date)
        elif interval.endswith("m"):
            minutes = int(interval[:-1])
            # 분봉은 개수 기반 조회이므로 적절한 개수 계산
            days_diff = (end_date - start_date).days
            count = min(days_diff * 390 // minutes, 500)  # 하루 390분 (9:00-15:30)
            ohlc_list = await self.market_service.get_minute_ohlc(symbol, minutes, count)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        return ohlc_list
    
    async def get_account(self) -> Account:
        """
        계좌 정보 조회
        
        Returns:
            계좌 정보
        """
        logger.info(f"Getting account: {self.account_id}")
        
        ls_account = await self.account_service.get_account_balance(self.account_id)
        return self.account_service.to_account(ls_account)
    
    async def get_positions(self) -> List[Position]:
        """
        보유 포지션 조회
        
        Returns:
            포지션 리스트
        """
        logger.info(f"Getting positions: {self.account_id}")
        
        ls_positions = await self.account_service.get_positions(self.account_id)
        return [self.account_service.to_position(pos) for pos in ls_positions]
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "market",
        price: float = None
    ) -> str:
        """
        주문 실행
        
        Args:
            symbol: 종목 코드
            side: 매수/매도 ("buy" or "sell")
            quantity: 주문 수량
            order_type: 주문 유형 ("market" or "limit")
            price: 주문 가격 (지정가인 경우)
        
        Returns:
            주문 번호
        """
        from broker.ls.models.order import OrderSide, OrderType
        
        logger.info(f"Placing order: {side} {quantity} {symbol} @ {price or 'MARKET'}")
        
        # 문자열을 Enum으로 변환
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_type_enum = OrderType.MARKET if order_type.lower() == "market" else OrderType.LIMIT
        
        order_id = await self.order_service.place_order(
            account_id=self.account_id,
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            order_type=order_type_enum,
            price=price
        )
        
        return order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        주문 취소
        
        Args:
            order_id: 주문 번호
        
        Returns:
            취소 성공 여부
        """
        logger.info(f"Cancelling order: {order_id}")
        
        return await self.order_service.cancel_order(self.account_id, order_id)

    
    async def get_current_price(self, symbol: str) -> float:
        """
        현재 시장 가격 가져오기
        
        Args:
            symbol: 종목 코드
        
        Returns:
            현재가
        """
        logger.info(f"Getting current price: {symbol}")
        
        # TODO: 실제 현재가 조회 API 호출
        # 임시로 OHLC의 최근 종가 반환
        ohlc_data = await self.get_ohlc(
            symbol=symbol,
            interval="1d",
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        if ohlc_data:
            return ohlc_data[-1].close
        
        return 0.0
    
    async def place_order(self, order: Order) -> str:
        """
        새 주문 제출
        
        Args:
            order: 주문 정보
        
        Returns:
            주문 ID
        """
        logger.info(f"Placing order: {order.symbol}")
        
        order_id = await self.order_service.place_order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type,
            price=order.price
        )
        
        return order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        기존 주문 취소
        
        Args:
            order_id: 주문 ID
        
        Returns:
            취소 성공 여부
        """
        logger.info(f"Cancelling order: {order_id}")
        
        # TODO: 주문 정보 조회하여 symbol, quantity 가져오기
        # 임시로 빈 값 전달
        return await self.order_service.cancel_order(order_id, "", 0)
    
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
        logger.info(f"Amending order: {order_id}")
        
        # TODO: 주문 정보 조회하여 symbol 가져오기
        return await self.order_service.amend_order(order_id, "", new_price, new_quantity)
    
    async def get_account(self) -> Account:
        """
        계좌 정보 가져오기
        
        Returns:
            계좌 정보
        """
        logger.info("Getting account info")
        ls_account = await self.account_service.get_account_balance(self.account_id)
        return self.account_service.to_account(ls_account)
    
    async def get_positions(self) -> List[Position]:
        """
        모든 보유 포지션 가져오기
        
        Returns:
            포지션 리스트
        """
        logger.info("Getting positions")
        ls_positions = await self.account_service.get_positions(self.account_id)
        return [self.account_service.to_position(pos) for pos in ls_positions]
    
    async def get_open_orders(self) -> List[Order]:
        """
        모든 미체결 주문 가져오기
        
        Returns:
            미체결 주문 리스트
        """
        logger.info("Getting open orders")
        return await self.account_service.get_open_orders()
    
    async def stream_realtime(
        self,
        symbols: List[str]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        WebSocket을 통한 실시간 가격 업데이트 스트리밍
        
        Args:
            symbols: 구독할 종목 코드 리스트
        
        Yields:
            실시간 가격 업데이트
        """
        logger.info(f"Starting realtime stream for {symbols}")
        
        # Realtime 서비스 초기화
        if self.realtime_service is None:
            self.realtime_service = LSRealtimeService(
                api_key=self.api_key,
                access_token=self.client.access_token
            )
        
        async for data in self.realtime_service.stream(symbols):
            yield data
