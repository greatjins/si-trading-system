from ...utils.logger import get_logger

class YahooWebSocketProvider:
    """Yahoo Finance WebSocket 데이터 제공자"""
    def __init__(self):
        """초기화 메서드"""
        self.logger = get_logger('YahooWebSocketProvider')