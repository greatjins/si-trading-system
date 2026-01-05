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
        self.realtime_service = None  # 지연 초기화 (토큰 필요)
        
        # FileStorage 인스턴스 (캐싱용)
        from data.storage import FileStorage
        self.storage = FileStorage()
        
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
        과거 OHLC 데이터 가져오기 (Parquet 캐싱 지원)
        
        캐싱 전략:
        1. Parquet 파일에서 로드 시도
        2. 없거나 불완전하면 API 호출
        3. API 데이터를 Parquet에 저장
        
        Args:
            symbol: 종목 코드
            interval: 시간 간격 ("1d", "1m", "5m", "10m", "30m", "60m")
            start_date: 시작 날짜
            end_date: 종료 날짜
        
        Returns:
            OHLC 데이터 리스트
        """
        logger.info(f"Getting OHLC: {symbol}, {interval} ({start_date.date()} ~ {end_date.date()})")
        
        # Parquet 캐시 확인
        cached_data = await self.storage.load_ohlc(symbol, interval, start_date, end_date)
        
        if cached_data:
            logger.info(f"✓ Loaded {len(cached_data)} bars from Parquet cache")
            return cached_data
        
        # 캐시에 없으면 API 호출
        logger.info("Cache miss - fetching from API...")
        
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
        
        # API 데이터를 Parquet에 저장
        if ohlc_list:
            await self.storage.save_ohlc(symbol, interval, ohlc_list)
            logger.info(f"✓ Saved {len(ohlc_list)} bars to Parquet cache")
        
        return ohlc_list
    
    async def get_account(self) -> Account:
        """
        계좌 정보 조회
        
        Returns:
            계좌 정보
        """
        logger.info(f"Getting account: {self.account_id}")
        
        # account_id는 계좌번호, account_password는 config에서 가져옴
        from utils.config import config
        account_password = config.get("ls.account_password", "")
        
        ls_account = await self.account_service.get_account_balance(self.account_id, account_password)
        return self.account_service.to_account(ls_account)
    
    async def get_positions(self) -> List[Position]:
        """
        보유 포지션 조회
        
        Returns:
            포지션 리스트
        """
        logger.info(f"Getting positions: {self.account_id}")
        
        # account_id는 계좌번호, account_password는 config에서 가져옴
        from utils.config import config
        account_password = config.get("ls.account_password", "")
        
        ls_positions = await self.account_service.get_positions(self.account_id, account_password)
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
        
        # Enum을 문자열로 변환
        side_str = order.side.value if hasattr(order.side, 'value') else str(order.side)
        order_type_str = order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type)
        
        # mbr_no 가져오기 (Order 객체의 metadata에서 또는 기본값)
        mbr_no = "KRX"  # 기본값
        if hasattr(order, 'metadata') and order.metadata and 'mbr_no' in order.metadata:
            mbr_no = order.metadata['mbr_no']
        
        order_id = await self.order_service.place_order(
            account_id=self.account_id,
            symbol=order.symbol,
            side=side_str,
            quantity=order.quantity,
            order_type=order_type_str,
            price=order.price,
            mbr_no=mbr_no
        )
        
        return order_id
    
    async def get_orders(self) -> List[Order]:
        """
        모든 주문 내역 조회 (체결/미체결 포함)
        
        Returns:
            주문 리스트
        """
        from utils.types import OrderSide, OrderType, OrderStatus
        
        logger.info("Getting all orders")
        
        # LSOrderService에서 주문 내역 가져오기
        ls_orders = await self.order_service.get_orders(self.account_id)
        
        # LSOrder를 Order로 변환
        orders = []
        for ls_order in ls_orders:
            # side 변환 (문자열 또는 Enum -> OrderSide)
            side_str = ls_order.side.value if hasattr(ls_order.side, 'value') else str(ls_order.side)
            side = OrderSide.BUY if side_str.lower() == "buy" else OrderSide.SELL
            
            # order_type 변환 (문자열 또는 Enum -> OrderType)
            order_type_str = ls_order.order_type.value if hasattr(ls_order.order_type, 'value') else str(ls_order.order_type)
            order_type = OrderType.MARKET if order_type_str.lower() == "market" else OrderType.LIMIT
            
            # status 변환 (문자열 -> OrderStatus)
            status_str = ls_order.status.value if hasattr(ls_order.status, 'value') else str(ls_order.status)
            
            # 체결 완료 여부 확인
            if ls_order.filled_quantity >= ls_order.quantity and ls_order.filled_quantity > 0:
                status = OrderStatus.FILLED
            elif ls_order.filled_quantity > 0:
                status = OrderStatus.PARTIAL_FILLED
            else:
                # 상태 문자열 매핑
                status_map = {
                    "pending": OrderStatus.PENDING,
                    "submitted": OrderStatus.SUBMITTED,
                    "partial": OrderStatus.PARTIAL_FILLED,
                    "filled": OrderStatus.FILLED,
                    "cancelled": OrderStatus.CANCELLED,
                    "rejected": OrderStatus.REJECTED,
                }
                status = status_map.get(status_str.lower(), OrderStatus.PENDING)
            
            order = Order(
                order_id=ls_order.order_id,
                symbol=ls_order.symbol,
                side=side,
                order_type=order_type,
                quantity=ls_order.quantity,
                price=ls_order.price,
                filled_quantity=ls_order.filled_quantity,
                status=status,
                created_at=ls_order.order_time or ls_order.created_at or datetime.now()
            )
            orders.append(order)
        
        return orders
    
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
        
        LS증권 WebSocket을 통해 실시간 주식체결(S3_) 데이터를 수신하고,
        전략 엔진으로 전달할 수 있는 형식으로 변환합니다.
        
        Args:
            symbols: 구독할 종목 코드 리스트
        
        Yields:
            실시간 가격 업데이트 딕셔너리
            {
                'symbol': str,      # 종목코드
                'price': float,     # 현재가
                'volume': int,      # 체결량
                'timestamp': datetime  # 체결시간
            }
        """
        logger.info(f"Starting realtime stream for {symbols}")
        
        # 클라이언트 연결 확인
        if not self.client.is_connected:
            await self.client.connect()
        
        # 유효한 토큰 획득
        access_token = await self.client._get_valid_token()
        
        # Realtime 서비스 초기화 (토큰 필요)
        if self.realtime_service is None:
            self.realtime_service = LSRealtimeService(
                api_key=self.api_key,
                access_token=access_token,
                paper_trading=self.paper_trading
            )
        else:
            # 토큰 갱신
            self.realtime_service.access_token = access_token
        
        # 실시간 데이터 스트리밍
        try:
            async for data in self.realtime_service.stream(symbols):
                # 데이터를 전략 엔진으로 전달
                yield data
        except Exception as e:
            logger.error(f"Error in realtime stream: {e}", exc_info=True)
            raise
