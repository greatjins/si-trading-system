from ...utils.logger import get_logger


class YahooTRProvider:
    def __init__(self):
        """초기화 메서드"""
        self.logger = get_logger('YahooTRProvider')