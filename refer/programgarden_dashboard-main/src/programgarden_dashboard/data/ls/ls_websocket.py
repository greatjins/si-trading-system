"""
LS Open API WebSocket 관리 시스템

- GSC: 해외 주식 체결 데이터 (기본, 모든 컴포넌트)
- GSH: 해외 주식 호가 데이터 (OrderBook 전용)  
- AS0: 해외 주식 주문 데이터 (OrderPanel/Account 전용)
"""

from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import asyncio

from ...utils.logger import get_logger


class LSWebSocketProvider:
    """LS Open API 실시간 WebSocket 전용 데이터 제공자"""
    
    def __init__(self):
        """
        LS WebSocket 제공자 초기화
        
        LS 인스턴스는 Provider에서 중앙 관리되며 set_ls_instance()로 주입됨
        """
        
        # LS API 인스턴스 (Provider로부터 주입됨)
        self.ls_instance = None
        
        # WebSocket 클라이언트들 (실제 API 기반)
        self.gsc_client = None  # 체결 데이터 (기본, 모든 컴포넌트)
        self.gsh_client = None  # 호가 데이터 (OrderBook 전용)
        self.as0_client = None  # 주문 데이터 (OrderPanel/Account 전용)
        
        # 구독 상태 관리 (타입별)
        self.gsc_symbols: Set[str] = set()  # GSC 구독 심볼들 (모든 컴포넌트)
        self.gsh_symbols: Set[str] = set()  # GSH 구독 심볼들 (OrderBook만)
        
        # 연결 상태
        self.ls_connected = False

        # WebSocket 유지용 태스크
        self.websocket_task: Optional[asyncio.Task] = None
        
        # 콜백 함수들
        self.on_market_data: Optional[Callable] = None
        self.on_order_book_data: Optional[Callable] = None
        self.on_order_data: Optional[Callable] = None
        self.on_connection_status: Optional[Callable] = None
        
        # 로깅
        self.logger = get_logger('LSWebSocketProvider')
        
    def set_ls_instance(self, ls_instance) -> None:
        """
        Provider로부터 LS 인스턴스 주입받기
        
        Args:
            ls_instance: 로그인된 LS 인스턴스
        """

        self.ls_instance = ls_instance
        
    async def add_symbol_to_gsc(self, symbols: List[str]) -> bool:
        """
        GSC 심볼 구독
        
        Args:
            symbols: 구독할 주식 심볼들 리스트 (예: ["AAPL", "GOOGL"])
            
        Returns:
            구독 성공 여부
        """
        if not symbols:
            self.logger.warning("⚠️ 구독할 GSC 심볼이 없습니다.")
            return False
            
        if not self.gsc_client:
            self.logger.error("❌ GSC 클라이언트가 초기화되지 않음")
            return False
            
        try:
            prefixed_symbols = [f"82{symbol.upper()}" for symbol in symbols]
            
            # LS API 직접 호출
            self.gsc_client.add_gsc_symbols(prefixed_symbols)
            
            # 상태 업데이트
            self.gsc_symbols.update(symbol.upper() for symbol in symbols)
            
            self.logger.info(f"✅ GSC 심볼 구독 완료: {symbols} ({len(symbols)}개)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GSC 심볼 구독 실패: {symbols} - {e}")
            return False
    
    async def remove_symbol_from_gsc(self, symbols: List[str]) -> bool:
        """
        GSC 심볼 구독 해제 (통합 메서드)
        
        Args:
            symbols: 구독 해제할 심볼들 리스트
            
        Returns:
            해제 성공 여부
        """
        if not symbols:
            self.logger.warning("⚠️ 구독 해제할 GSC 심볼이 없습니다.")
            return False
            
        if not self.gsc_client:
            self.logger.error("❌ GSC 클라이언트가 초기화되지 않음")
            return False
            
        try:
            # ✅ Instructions 준수: 단순하고 직접적인 구현
            prefixed_symbols = [f"82{symbol.upper()}" for symbol in symbols]
            
            # LS API 직접 호출
            self.gsc_client.remove_gsc_symbols(prefixed_symbols)
            
            # 상태 업데이트
            for symbol in symbols:
                self.gsc_symbols.discard(symbol.upper())
            
            self.logger.info(f"🛑 GSC 심볼 구독 해제 완료: {symbols} ({len(symbols)}개)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GSC 심볼 구독 해제 실패: {symbols} - {e}")
            return False
            
    async def add_symbol_to_gsh(self, symbols: List[str]) -> bool:
        """
        GSH 심볼 구독 (통합 메서드)
        
        Args:
            symbols: 구독할 주식 심볼들 리스트 (OrderBook용)
            
        Returns:
            구독 성공 여부
        """
        if not symbols:
            self.logger.warning("⚠️ 구독할 GSH 심볼이 없습니다.")
            return False
            
        if not self.gsh_client:
            self.logger.error("❌ GSH 클라이언트가 초기화되지 않음")
            return False
            
        try:
            prefixed_symbols = [f"82{symbol.upper()}" for symbol in symbols]
            
            # LS API 직접 호출
            self.gsh_client.add_gsh_symbols(prefixed_symbols)
            
            # 상태 업데이트
            self.gsh_symbols.update(symbol.upper() for symbol in symbols)
            
            self.logger.info(f"✅ GSH 심볼 구독 완료: {symbols} ({len(symbols)}개)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GSH 심볼 구독 실패: {symbols} - {e}")
            return False
    
    async def remove_symbol_from_gsh(self, symbols: List[str]) -> bool:
        """
        GSH 심볼 구독 해제 (통합 메서드)
        
        Args:
            symbols: 구독 해제할 심볼들 리스트
            
        Returns:
            해제 성공 여부
        """
        if not symbols:
            self.logger.warning("⚠️ 구독 해제할 GSH 심볼이 없습니다.")
            return False
            
        if not self.gsh_client:
            self.logger.error("❌ GSH 클라이언트가 초기화되지 않음")
            return False
            
        try:
            prefixed_symbols = [f"82{symbol.upper()}" for symbol in symbols]
            
            # LS API 직접 호출
            self.gsh_client.remove_gsh_symbols(prefixed_symbols)
            
            # 상태 업데이트
            for symbol in symbols:
                self.gsh_symbols.discard(symbol.upper())
            
            self.logger.info(f"🛑 GSH 심볼 구독 해제 완료: {symbols} ({len(symbols)}개)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GSH 심볼 구독 해제 실패: {symbols} - {e}")
            return False
    
    
    # ========================================
    # LS WebSocket 클라이언트
    # ========================================
    
    async def setup_websocket_client(self) -> bool:
        try:
            client = self.ls_instance.overseas_stock().real()
            await client.connect()

            # AS0 클라이언트 설정 (주문 데이터)
            self.gsc_client = client.GSC()
            self.gsc_client.on_gsc_message(self._on_gsc_message)

            # GSH 클라이언트 설정 (호가 데이터)
            self.gsh_client = client.GSH()
            self.gsh_client.on_gsh_message(self._on_gsh_message)

            # AS0 클라이언트 설정 (주문 데이터)
            self.as0_client = client.AS0()
            self.as0_client.on_as0_message(self._on_as0_message)
            
            self.ls_connected = True
            self.on_connection_status('LS', True)
            self.logger.info("✅ WebSocket 클라이언트 설정 완료")

            return True

        except Exception as e:
            self.ls_connected = False
            self.on_connection_status('LS', False)
            self.logger.error(f"❌ WebSocket 클라이언트 설정 실패: {e}")

            return False

    # ========================================
    # 데이터 수신 콜백들
    # ========================================
    
    def set_callbacks(self, 
            on_market_data: Callable = None, 
            on_order_book_data: Callable = None, 
            on_order_data: Callable = None,
            on_connection_status: Callable = None
        ) -> None:
        """콜백 함수 설정"""

        self.on_market_data = on_market_data
        self.on_order_book_data = on_order_book_data
        self.on_order_data = on_order_data
        self.on_connection_status = on_connection_status

    def _on_gsc_message(self, message) -> None:
        """GSC 데이터 수신 콜백"""
        try:
            # 데이터 파싱 및 변환
            market_data = self._parse_gsc_message(message)
            
            # provider.py로 데이터 전달
            if self.on_market_data and market_data:
                symbol = market_data.get('symbol', 'UNKNOWN')
                self.on_market_data(symbol, market_data)
                
        except Exception as e:
            self.logger.error(f"❌ GSC 메시지 처리 실패: {e}")

    def _on_gsh_message(self, message) -> None:
        """GSH 데이터 수신 콜백"""
        try:
            # 데이터 파싱 및 변환
            order_book_data = self._parse_gsh_message(message)
            
            # provider.py로 데이터 전달
            if self.on_order_book_data and order_book_data:
                symbol = order_book_data.get('symbol', 'UNKNOWN')
                self.on_order_book_data(symbol, order_book_data)
                
        except Exception as e:
            self.logger.error(f"❌ GSH 메시지 처리 실패: {e}")
            
    def _on_as0_message(self, message) -> None:
        """AS0 데이터 수신 콜백"""
        try:
            # 데이터 파싱 및 변환
            order_data = self._parse_as0_message(message)
            
            # provider.py로 데이터 전달
            if self.on_order_data and order_data:
                symbol = order_data.get('symbol', 'UNKNOWN')
                self.on_order_data(symbol, order_data)

        except Exception as e:
            self.logger.error(f"❌ AS0 메시지 처리 실패: {e}")
    
    # ========================================
    # 데이터 파싱 메서드들
    # ========================================
    
    def _parse_gsc_message(self, message) -> Optional[Dict[str, Any]]:
        """GSC 메시지 파싱 - LS API 응답에서 실제 데이터 추출"""
        try:
            if not hasattr(message, 'body'):
                return None
                
            body = message.body

            if not hasattr(body, 'symbol'):
                return None
            
            # GSC 응답에서 모든 필드 추출 (provider.py의 기존 로직 적용)
            symbol = str(body.symbol)
            price = float(body.price)
            change = float(body.diff)
            change_percent = float(body.rate)
            volume = int(body.totq)
            open_price = float(body.open)
            high_price = float(body.high)
            low_price = float(body.low)
            
            # 52주 고가/저가
            high52_price = float(body.high52p)
            low52_price = float(body.low52p)

            # 거래대금 및 체결정보
            amount = int(body.amount)
            cgubun = str(body.cgubun)
            trdq = int(body.trdq)

            # Dashboard 컴포넌트에서 사용할 완전한 데이터 구조
            complete_data = {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": volume,
                "open": round(open_price, 2),
                "high": round(high_price, 2), 
                "low": round(low_price, 2),
                "high52": round(high52_price, 2),
                "low52": round(low52_price, 2),
                "amount": amount,
                "cgubun": cgubun,
                "trdq": trdq,
                "timestamp": datetime.now().isoformat(),
                "source": "LS Open API"
            }
            
            self.logger.debug(f"✅ LS GSC 실시간 데이터 파싱: {symbol} ${price} ({change_percent:+.2f}%)")
            return complete_data
            
        except Exception as e:
            self.logger.error(f"❌ GSC 메시지 파싱 실패: {e}")
            return None
            
    def _parse_gsh_message(self, message) -> Optional[Dict[str, Any]]:
        """GSH 메시지 파싱"""
        try:
            if not hasattr(message, 'body'):
                return None
            
            body = message.body

            if not hasattr(body, 'symbol'):
                return None

            # 심볼 및 시간 정보 추출
            symbol = str(body.symbol)
            loctime = str(body.loctime)  # 현지 시간 (HHMMSS)
            kortime = str(body.kortime)  # 한국 시간 (HHMMSS)
            
            # 매도 호가 10단계
            ask_prices = [float(getattr(body, f'offerho{i}', 0.0)) for i in range(1, 11)]
            ask_volumes = [int(getattr(body, f'offerrem{i}', 0)) for i in range(1, 11)]
            ask_counts = [int(getattr(body, f'offerno{i}', 0)) for i in range(1, 11)]

            # 매수 호가 10단계
            bid_prices = [float(getattr(body, f'bidho{i}', 0.0)) for i in range(1, 11)]
            bid_volumes = [int(getattr(body, f'bidrem{i}', 0)) for i in range(1, 11)]
            bid_counts = [int(getattr(body, f'bidno{i}', 0)) for i in range(1, 11)]

            # 총 데이터
            total_ask_volume = int(body.totofferrem)
            total_bid_volume = int(body.totbidrem)
            total_ask_count = int(body.totoffercnt)
            total_bid_count = int(body.totbidcnt)

            # Dashboard 컴포넌트에서 사용할 완전한 데이터 구조
            complete_data = {
                "symbol": symbol,
                "loctime": loctime,
                "kortime": kortime,
                "ask_prices": ask_prices,
                "ask_volumes": ask_volumes,
                "ask_counts": ask_counts,
                "bid_prices": bid_prices,
                "bid_volumes": bid_volumes,
                "bid_counts": bid_counts,
                "total_ask_volume": total_ask_volume,
                "total_bid_volume": total_bid_volume,
                "total_ask_count": total_ask_count,
                "total_bid_count": total_bid_count,
                "last_updated": datetime.now().isoformat(),
                "source": "LS Open API"
            }

            self.logger.debug(f"✅ LS GSH 실시간 데이터 파싱: {symbol}")
            return complete_data
            
        except Exception as e:
            self.logger.error(f"❌ GSH 메시지 파싱 실패: {e}")
            return None
            
    def _parse_as0_message(self, message) -> Optional[Dict[str, Any]]:
        """AS0 메시지 파싱"""
        try:
            # 실제 AS0 메시지 파싱 로직
            return {
                "type": "AS0",
                "order_id": "12345", # 실제 파싱 필요
                "status": "filled",  # 실제 파싱 필요
                "timestamp": "now"   # 실제 파싱 필요
            }
            
        except Exception as e:
            self.logger.error(f"❌ AS0 메시지 파싱 실패: {e}")
            return None
    
    # ========================================
    # 상태 관리 및 정리
    # ========================================
    
    def get_connection_status(self) -> Dict[str, Any]:
        """WebSocket 연결 상태 반환"""
        return {
            "ls_connected": self.ls_connected,
            "gsc_symbols": list(self.gsc_symbols),
            "gsh_symbols": list(self.gsh_symbols),
            "clients": {
                "gsc_active": self.gsc_client is not None,
                "gsh_active": self.gsh_client is not None,
                "as0_active": self.as0_client is not None
            }
        }

    async def cleanup(self) -> None:
        """
        WebSocket 리소스 완전 정리 (Instructions 준수)
        
        현재 상황에 맞는 최적화:
        - GSC/GSH/AS0 클라이언트별 구독 해제
        - WebSocket Task 정리  
        - 상태 초기화
        - 콜백 함수 정리
        """
        self.logger.info("🧹 LS WebSocket Provider 리소스 정리 시작...")
        
        try:
            # 1. WebSocket Task 정리
            if hasattr(self, 'websocket_task') and self.websocket_task:
                if not self.websocket_task.done():
                    self.websocket_task.cancel()
                    try:
                        await self.websocket_task
                    except asyncio.CancelledError:
                        self.logger.debug("🛑 WebSocket Task 취소 완료")
                self.websocket_task = None

            # 2. 각 클라이언트별 구독 해제 및 정리
            if self.gsc_client:
                try:
                    # GSC 구독 해제
                    if self.gsc_symbols:
                        prefixed_symbols = [f"82{symbol}" for symbol in self.gsc_symbols]
                        self.gsc_client.remove_gsc_symbols(prefixed_symbols)
                        self.logger.debug(f"🛑 GSC 구독 해제: {len(self.gsc_symbols)}개")
                    
                    # 콜백 해제
                    self.gsc_client.on_remove_gsc_message()
                    self.gsc_client = None
                except Exception as e:
                    self.logger.warning(f"⚠️ GSC 클라이언트 정리 중 오류: {e}")
                    self.gsc_client = None

            if self.gsh_client:
                try:
                    # GSH 구독 해제  
                    if self.gsh_symbols:
                        prefixed_symbols = [f"82{symbol}" for symbol in self.gsh_symbols]
                        self.gsh_client.remove_gsh_symbols(prefixed_symbols)
                        self.logger.debug(f"🛑 GSH 구독 해제: {len(self.gsh_symbols)}개")
                    
                    # 콜백 해제
                    self.gsh_client.on_remove_gsh_message(None)
                    self.gsh_client = None
                except Exception as e:
                    self.logger.warning(f"⚠️ GSH 클라이언트 정리 중 오류: {e}")
                    self.gsh_client = None

            if self.as0_client:
                try:
                    # AS0 콜백 해제
                    self.as0_client.on_remove_as0_message(None)
                    self.as0_client = None
                    self.logger.debug("🛑 AS0 클라이언트 정리 완료")
                except Exception as e:
                    self.logger.warning(f"⚠️ AS0 클라이언트 정리 중 오류: {e}")
                    self.as0_client = None

            # 3. 구독 상태 초기화
            self.gsc_symbols.clear()
            self.gsh_symbols.clear()
            self.ls_connected = False
            
            # 4. 콜백 함수 정리
            self.on_market_data = None
            self.on_order_book_data = None
            self.on_order_data = None
            self.on_connection_status = None

            # 5. LS 인스턴스 해제 (Provider에서 관리하므로 None만 할당)
            self.ls_instance = None
            
            self.logger.info("✅ LS WebSocket Provider 리소스 정리 완료")
            
        except Exception as e:
            self.logger.error(f"❌ WebSocket Provider 정리 중 오류 발생: {e}")
            # 강제 초기화
            self.gsc_client = self.gsh_client = self.as0_client = None
            self.gsc_symbols.clear()
            self.gsh_symbols.clear() 
            self.ls_connected = False
            self.logger.warning("⚠️ 강제 리소스 정리 완료")