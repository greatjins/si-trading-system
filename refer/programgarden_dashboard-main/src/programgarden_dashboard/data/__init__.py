"""
Data 패키지 - ProgramGarden Dashboard 데이터 제공자 모듈

NiceGUI 기반 해외 주식 대시보드의 데이터 레이어
- LS Open API: 메인 데이터 소스 (해외 주식 실시간)
- Yahoo Finance: 폴백 데이터 소스
- 통합 DataProvider: Dashboard와의 단일 인터페이스
"""

# 메인 데이터 제공자
from .provider import DataProvider

# LS Open API 모듈들
from .ls import (
    LSProvider,
    LSWebSocketProvider,
    LSTRProvider
)

# Yahoo Finance 모듈들
from .yahoo import (
    YahooProvider,
    YahooWebSocketProvider,
    YahooTRProvider
)

__all__ = [
    # 메인 인터페이스
    "DataProvider",
    
    # LS Open API
    "LSProvider",
    "LSWebSocketProvider",
    "LSTRProvider",
    
    # Yahoo Finance
    "YahooProvider", 
    "YahooWebSocketProvider",
    "YahooTRProvider"
]