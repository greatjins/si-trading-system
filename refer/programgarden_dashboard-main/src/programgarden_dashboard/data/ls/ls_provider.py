"""LS Open API 전용 데이터 제공자"""

from typing import Optional, Dict, List, Any
import asyncio

from .ls_tr import LSTRProvider
from .ls_websocket import LSWebSocketProvider
from ...utils.logger import get_logger

from programgarden_finance import LS


class LSProvider:
    """LS Open API 전용 데이터 제공자"""

    def __init__(self, app_key: Optional[str], app_secret: Optional[str]):
        # LS 전용 속성들
        self.app_key = app_key
        self.app_secret = app_secret
        self.ls_instance = None
        self.ls_login_status = False
        self.websocket_connected = False
        
        # LS 하위 Provider들
        self.ls_tr_provider = LSTRProvider()
        self.ls_websocket_provider = LSWebSocketProvider()
        
        # LS 연결 상태
        self.is_connected = False
        self.subscribed_symbols = set()
        
        # 콜백 시스템
        self.on_market_data = None
        self.on_order_book_data = None 
        self.on_order_data = None
        self.on_connection_status = None

        # 로깅 설정
        self.logger = get_logger('LSProvider')
    
    # ========================================
    # LS 중앙 집중식 초기화 및 공유 메서드
    # ========================================

    async def connect(self):
        """LS API 연결 (단순화)"""
        if self.ls_instance and self.ls_login_status:
            return True
        
        try:
            self.ls_instance = LS.get_instance()
            success = await self.ls_instance.async_login(
                appkey=self.app_key, 
                appsecretkey=self.app_secret
            )
            
            if success:
                self.ls_login_status = True
                self.is_connected = True
                
                # LS TR Provider에 LS 인스턴스 공유
                self.ls_tr_provider.set_ls_instance(self.ls_instance)
                
                # LS WebSocket Provider에 LS 인스턴스 공유
                self.ls_websocket_provider.set_ls_instance(self.ls_instance)

                self.logger.info("✅ LS API 연결 완료")
            
            return success
        
        except Exception as e:
            self.logger.error(f"❌ LS API 연결 실패: {e}")
            return False
    
    async def connect_websocket(self) -> bool:
        """WebSocket 연결"""
        if not self.ls_login_status:
            raise ValueError("LS API에 먼저 연결해주세요. connect() 호출 필요")
            
        try:
            self.logger.info("🔌 WebSocket 연결 시작...")
            
            # WebSocket 클라이언트만 설정
            success = await self.ls_websocket_provider.setup_websocket_client()
            
            if success:
                self.websocket_connected = True
                self.logger.info("✅ WebSocket 연결 완료")
            else:
                self.logger.info("❌ WebSocket 연결 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False
        
    # ========================================
    # LS WebSocket 구독 메서드들 (개선중)
    # ========================================

    async def subscribe_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        심볼 일괄 구독
        
        Args:
            symbols: 구독할 주식 심볼들 리스트 (예: ["AAPL", "GOOGL", "TSLA"])
            
        Returns:
            구독 결과 Dict {symbol: success_boolean}
        """
        if not symbols:
            self.logger.warning("⚠️ 구독할 심볼이 없습니다.")
            return {}

        # 중복 필터링
        symbols_upper = [symbol.upper() for symbol in symbols]
        new_symbols = [symbol for symbol in symbols_upper if symbol not in self.subscribed_symbols]
        
        if not new_symbols:
            return {symbol: True for symbol in symbols_upper}

        self.logger.info(f"🔔 일괄 구독 시작: {new_symbols} ({len(new_symbols)}개)")

        try:
            # 구독 시작
            success = await self.ls_websocket_provider.add_symbol_to_gsc(new_symbols)
            
            if success:
                # 성공한 심볼들 추가
                self.subscribed_symbols.update(new_symbols)
                self.logger.info(f"✅ LS WebSocket 일괄 구독 성공: {len(new_symbols)}개")
                return {symbol: True for symbol in symbols_upper}
            else:
                self.logger.warning("⚠️ LS WebSocket 일괄 구독 실패")
                return {symbol: False for symbol in symbols_upper}
                
        except Exception as e:
            self.logger.error(f"❌ LS WebSocket 일괄 구독 오류: {e}")
            return {symbol: False for symbol in symbols_upper}

    async def subscribe_symbol(self, symbol: str) -> bool:
        """
        개별 심볼 구독
        
        Args:
            symbol: 구독할 주식 심볼 (예: "AAPL")
            
        Returns:
            구독 성공 여부
        """

        results = await self.subscribe_symbols([symbol])
        return results.get(symbol.upper(), False)

    async def add_order_book_symbol(self, symbol: str) -> Dict[str, Dict[str, bool]]:
        """
        OrderBook용 심볼 추가 (GSC + GSH 동시 구독)
        Args:
            symbol: OrderBook 구독할 심볼
            
        Returns:
            결과 Dict {symbol: {"GSC": bool, "GSH": bool}}
        """
        if not symbol:
            return {}

        symbol_upper = symbol.upper()
        results = {}

        try:
            # 병렬로 GSC, GSH 동시 구독
            gsc_task = self.ls_websocket_provider.add_symbol_to_gsc([symbol_upper])
            gsh_task = self.ls_websocket_provider.add_symbol_to_gsh([symbol_upper])

            gsc_success, gsh_success = await asyncio.gather(gsc_task, gsh_task, return_exceptions=True)
            
            # 예외 처리
            if isinstance(gsc_success, Exception):
                self.logger.error(f"❌ GSC 구독 실패: {gsc_success}")
                gsc_success = False
            if isinstance(gsh_success, Exception):
                self.logger.error(f"❌ GSH 구독 실패: {gsh_success}")
                gsh_success = False

            # 결과 구성
            results[symbol_upper] = {
                "GSC": gsc_success,
                "GSH": gsh_success,
                "success": gsc_success and gsh_success
            }
                
            # 성공한 심볼들만 추가
            if gsc_success or gsh_success:
                self.subscribed_symbols.add(symbol_upper)
            
            return results

        except Exception as e:
            self.logger.error(f"❌ OrderBook 일괄 구독 오류: {e}")
            return {symbol: {"GSC": False, "GSH": False, "success": False} for symbol in symbol_upper}

    async def unsubscribe_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        심볼 일괄 구독 해제

        Args:
            symbols: 구독 해제할 심볼들 리스트
            
        Returns:
            해제 결과 Dict {symbol: success_boolean}
        """
        if not symbols:
            return {}

        symbols_upper = [symbol.upper() for symbol in symbols]
        subscribed_only = [symbol for symbol in symbols_upper if symbol in self.subscribed_symbols]

        if not subscribed_only:
            self.logger.info("📋 구독 해제할 심볼이 없습니다.")
            return {symbol: True for symbol in symbols_upper}

        try:
            # 리스트 전체를 한 번에 전달
            gsc_task = self.ls_websocket_provider.remove_symbol_from_gsc(subscribed_only)
            gsh_task = self.ls_websocket_provider.remove_symbol_from_gsh(subscribed_only)
            
            gsc_success, gsh_success = await asyncio.gather(gsc_task, gsh_task, return_exceptions=True)
            
            # 성공한 경우 구독 목록에서 제거
            if not isinstance(gsc_success, Exception) and gsc_success:
                for symbol in subscribed_only:
                    self.subscribed_symbols.discard(symbol)
                    
            success_count = len(subscribed_only) if gsc_success else 0
            self.logger.info(f"🛑 일괄 구독 해제: {success_count}개 성공")
            
            return {symbol: True for symbol in symbols_upper}

        except Exception as e:
            self.logger.error(f"❌ 일괄 구독 해제 오류: {e}")
            return {symbol: False for symbol in symbols_upper}
        
    async def unsubscribe_symbol(self, symbol: str) -> bool:
        """
        개별 심볼 구독 해제

        Args:
            symbol: 구독 해제할 주식 심볼 (예: "AAPL")

        Returns:
            구독 성공 여부
        """

        results = await self.unsubscribe_symbols([symbol])
        return results.get(symbol.upper(), False)

    async def remove_order_book_symbol(self, symbol: str) -> Dict[str, Dict[str, bool]]:
        """
        OrderBook용 심볼 제거 (GSC + GSH 동시 해제)

        Args:
            symbol: OrderBook 구독 해제할 심볼

        Returns:
            결과 Dict {symbol: {"GSC": bool, "GSH": bool}}
        """
        if not symbol:
            return {}

        symbol_upper = symbol.upper()
        results = {}

        try:
            # 병렬로 GSC, GSH 동시 해제
            gsc_task = self.ls_websocket_provider.remove_symbol_from_gsc(symbol_upper)
            gsh_task = self.ls_websocket_provider.remove_symbol_from_gsh(symbol_upper)

            gsc_success, gsh_success = await asyncio.gather(gsc_task, gsh_task, return_exceptions=True)
            
            # 예외 처리
            if isinstance(gsc_success, Exception):
                self.logger.error(f"❌ GSC 해제 실패: {gsc_success}")
                gsc_success = False
            if isinstance(gsh_success, Exception):
                self.logger.error(f"❌ GSH 해제 실패: {gsh_success}")
                gsh_success = False

            # 결과 구성
            results[symbol_upper] = {
                "GSC": gsc_success,
                "GSH": gsh_success,
                "success": gsc_success and gsh_success
            }
                
            # 성공한 심볼들만 제거
            if gsc_success or gsh_success:
                self.subscribed_symbols.discard(symbol_upper)
            
            return results

        except Exception as e:
            self.logger.error(f"❌ OrderBook 일괄 해제 오류: {e}")
            return {symbol: {"GSC": False, "GSH": False, "success": False} for symbol in symbol_upper}
    
    # ========================================
    # LS WebSocket 콜백 메서드들
    # ========================================

    def setup_callbacks(
        self,
        on_market_data=None,
        on_order_book_data=None,
        on_order_data=None,
        on_connection_status=None
    ):
        """
        람다 기반 직접 연결 콜백 설정 (50% 코드 단축)
        
        Instructions 준수:
        - "NiceGUI 네이티브": 커스텀 래퍼 메서드 제거
        - "초보자 친화적": 직관적인 직접 연결 방식
        - "하나씩 완벽하게": 명확한 단일 메서드로 완성
        """
        # 콜백 저장
        self.on_market_data = on_market_data
        self.on_order_book_data = on_order_book_data  
        self.on_order_data = on_order_data
        self.on_connection_status = on_connection_status
        
        # ✅ 람다 직접 연결: 중간 래퍼 메서드 4개 제거
        self.ls_websocket_provider.set_callbacks(
            on_market_data=lambda s, d: self._safe_callback('market_data', 
                lambda: self.on_market_data and self.on_market_data(s, d)),
            on_order_book_data=lambda s, d: self._safe_callback('order_book_data',
                lambda: self.on_order_book_data and self.on_order_book_data(s, d)),
            on_order_data=lambda t, d: self._safe_callback('order_data',
                lambda: self.on_order_data and self.on_order_data(t, d)),
            on_connection_status=lambda s, c: self._handle_connection_status_optimized(s, c)
        )
        
        self.logger.info("✅ LS Provider 콜백 시스템 설정 완료")
    
    def _safe_callback(self, callback_type: str, callback_func):
        """통합 에러 처리 헬퍼 (DRY 원칙)"""
        try:
            callback_func()
            self.logger.debug(f"📡 {callback_type} 콜백 처리 완료")
        except Exception as e:
            self.logger.error(f"❌ {callback_type} 콜백 처리 실패: {e}")
    
    def _handle_connection_status_optimized(self, source: str, connected: bool):
        """최적화된 연결 상태 처리 (상태 관리 포함)"""
        try:
            # 상태 업데이트
            self.is_connected = connected
            
            # 로깅
            status_msg = "✅ LS WebSocket 연결 성공" if connected else "⚠️ LS WebSocket 연결 실패"
            (self.logger.info if connected else self.logger.warning)(status_msg)
            
            # 외부 콜백 호출
            if self.on_connection_status:
                self.on_connection_status(source, connected)
                
        except Exception as e:
            self.logger.error(f"❌ 연결 상태 처리 실패: {e}")
    
    # ========================================
    # LS TR 조회 기능 메서드
    # ========================================
    
    async def fetch_account_data(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회 (LS TR COSOQ00201 API 사용) - 비동기 버전
        
        Returns:
            계좌 잔고 Dict
        """
        try:
            return await self.ls_tr_provider.fetch_account_data()
        except Exception as e:
            self.logger.error(f"계좌 잔고 조회 실패: {e}")
            return {"error": str(e)}
    
    # ========================================
    # LS 상태 조회 기능 메서드
    # ========================================
    
    def get_connection_status(self) -> bool:
        """현재 LS WebSocket 연결 상태 반환"""

        return self.is_connected