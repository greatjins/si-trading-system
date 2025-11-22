"""Yahoo Finance 전용 데이터 제공자"""

from typing import List

from .yahoo_tr import YahooTRProvider
from .yahoo_websocket import YahooWebSocketProvider
from ...utils.logger import get_logger

class YahooProvider:
    """Yahoo Finance 전용 데이터 제공자"""
    
    def __init__(self):
        """초기화 메서드"""
                
        # LS 전용 속성들
        self.ls_instance = None
        self.ls_login_status = False
        self.websocket_connected = False
        
        # LS 하위 Provider들
        self.yahoo_tr_provider = YahooTRProvider()
        self.yahoo_websocket_provider = YahooWebSocketProvider()
        
        # LS 연결 상태
        self.is_connected = False
        self.subscribed_symbols = set()
        
        # 콜백 시스템
        self.on_market_data = None
        self.on_connection_status = None

        # 로깅 설정
        self.logger = get_logger('YahooProvider')
    
    async def connect(self):
        """Yahoo Finance 연결 함수"""
        return True

    async def connect_websocket(self):
        """Yahoo Finance WebSocket 연결 함수"""
        return True
    
    def subscribe_symbols(self, symbols: List[str]):
        """Yahoo Finance 전용 심볼 구독"""
    
    def unsubscribe_symbols(self, symbols: List[str]):
        """Yahoo Finance 전용 심볼 구독 해제"""
    
    def setup_callbacks(self, 
        on_market_data = None,
        on_connection_status = None
    ):
        """Yahoo Finance 전용 콜백 설정"""
    
    def get_connection_status(self) -> bool:
        """현재 Yahoo WebSocket 연결 상태 반환"""
        
        return self.is_connected