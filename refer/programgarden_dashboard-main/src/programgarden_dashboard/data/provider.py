"""
데이터 제공자 - LS Open API 및 Yahoo Finance 통합
"""

from typing import Dict, List, Optional, Callable, Any

from .ls.ls_provider import LSProvider
from .yahoo.yahoo_provider import YahooProvider
from ..utils.logger import get_logger


class DataProvider:
    """LS Open API 및 Yahoo Finance 통합 데이터 제공자"""

    def __init__(self, app_key: Optional[str] = None, app_secret: Optional[str] = None):
        """
        데이터 제공자 초기화
       
        Args:
            app_key: LS Open API 앱키
            app_secret: LS Open API 시크릿키
        """

        # LS Provider
        self.ls_provider = LSProvider(app_key, app_secret)

        # Yahoo Provider
        self.yahoo_provider = YahooProvider()
        
        # 통합 상태 관리
        self.current_source = None
        self.subscribed_symbols = set()
        
        # 통합 콜백 시스템
        self.on_market_data: Optional[Callable] = None
        self.on_order_book_data: Optional[Callable] = None
        self.on_order_data: Optional[Callable] = None
        self.on_connection_status: Optional[Callable] = None
        
        # 로깅 설정
        self.logger = get_logger('DataProvider')
    
    # ========================================
    # LS 및 YahooFinance 연결 관리
    # ========================================

    async def connect(self):
        """LS/YahooFinance 연결 함수"""
        # LS Provider 연결 시도
        success = await self.ls_provider.connect()
        if success:
            self.current_source = "LS"
            return success

        # Yahoo Provider 연결 시도
        success = await self.yahoo_provider.connect()
        if success:
            self.current_source = "Yahoo"
            return success
        
        self.logger.error(f"❌ 모든 연결 실패")
        return False

    async def connect_websocket(self):
        """LS/YahooFinance WebSocket 연결 함수"""
        # LS Provider WebSocket 연결 시도
        try:
            success = await self.ls_provider.connect_websocket()
            if success:
                self.current_source = "LS"
                return success
        except Exception as e:
            self.logger.warning(f"LS WebSocket 연결 실패 → Yahoo 폴백: {e}")

        # Yahoo Provider WebSocket 연결 시도
        try:
            success = await self.yahoo_provider.connect_websocket()
            if success:
                self.current_source = "Yahoo"
                return success
        except Exception as e:
            self.logger.error(f"❌ 모든 WebSocket 연결 실패: {e}")
            return False

    # ========================================
    # Dashboard 콜백 설정
    # ========================================

    def setup_dashboard_integration(
            self, 
            on_price_update=None, 
            on_order_book_update=None, 
            on_order_update=None, 
            on_connection_status=None) -> None:
        """Dashboard 콜백 설정"""

        # LS Provider에게 콜백 위임
        self.ls_provider.setup_callbacks(
            on_market_data=on_price_update,
            on_order_book_data=on_order_book_update,
            on_order_data=on_order_update,
            on_connection_status=on_connection_status
        )

        # Yahoo Provider에게 콜백 위임
        self.yahoo_provider.setup_callbacks(
            on_market_data=on_price_update,
            on_connection_status=on_connection_status
        )
        
        self.logger.info("✅ Dashboard 통합 콜백 설정 완료")
    
    # ========================================
    # 통합 구독 메서드들
    # ========================================

    async def subscribe_symbols(self, symbols: List[str]):
        """통합 구독 진입점"""

        # 1. LS Provider 우선 시도
        try:
            await self.ls_provider.subscribe_symbols(symbols)
            return
        except Exception as e:
            self.logger.warning(f"LS 구독 실패 → Yahoo 폴백: {e}")
            
        # 2. Yahoo Provider 폴백
        try:
            await self.yahoo_provider.subscribe_symbols(symbols)
            return
        except Exception as e:
            self.logger.error(f"Yahoo 구독 실패: {e}")
            
        # 3. 모든 연결 실패
        await self._handle_all_connections_failed_batch(symbols)
    
    async def subscribe_order_book_symbol(self, symbol: str):
        """호가 잔량 구독 진입점"""

        try:
            await self.ls_provider.add_order_book_symbol(symbol)
        except Exception as e:
            self.logger.warning(f"호가 잔량 구독 불가 (LS 연결 없음): {symbol}")

    async def unsubscribe_symbols(self, symbols: List[str]):
        """통합 구독 해제 진입점"""

        # 1. LS Provider 우선 시도
        if self.ls_provider.get_connection_status():
            await self.ls_provider.unsubscribe_symbols(symbols)
        
        # 2. Yahoo Provider 폴백
        if self.yahoo_provider.get_connection_status():
            await self.yahoo_provider.unsubscribe_symbols(symbols)
        
        # 3. 전체 구독에서 제거
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol)
        
    async def unsubscribe_order_book_symbol(self, symbol: str):
        """호가 잔량 구독 해제 진입점"""

        if self.ls_provider.get_connection_status():
            await self.ls_provider.remove_order_book_symbol(symbol)
        else:
            self.logger.warning(f"호가 잔량 구독 해제 불가 (LS 연결 없음): {symbol}")
    
    # ========================================
    # 폴백 메서드
    # ========================================
            
    async def _handle_all_connections_failed_batch(self, symbols: List[str]):
        """모든 연결 실패 시 일괄 처리"""

        self.logger.error(f"❌ 모든 WebSocket 연결 실패: {symbols}")
        
        if self.on_connection_status:
            self.on_connection_status("disconnected", "All failed")
            
        # 구독에서 일괄 제거
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol)
    
    # ========================================
    # 데이터 요청 메서드들
    # ========================================
    
    async def fetch_account_data(self) -> Dict[str, Any]:
        """계좌 데이터 요청"""
        if self.current_source == "LS" and self.ls_provider.is_connected:
            return await self.ls_provider.fetch_account_data()
        else:
            self.logger.warning("계좌 데이터 소스 없음")
            return {}