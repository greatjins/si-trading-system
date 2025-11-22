"""
ProgramGarden Dashboard
============================

파이썬 초보자를 위한 3줄로 완성할 수 있는 해외 주식 대시보드 라이브러리

Basic Usage (3줄 사용법):
```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard(
    app_key="your_ls_key", 
    app_secret="your_ls_secret"
)
dashboard.add_stock_card("AAPL")
dashboard.run()
```

Features:
- NiceGUI 기반 12열 그리드 시스템
- LS Open API 메인, Yahoo Finance WebSocket 폴백
- 실시간 해외 주식 데이터
- 초보자 친화적 API 설계
"""

from .dashboard import ProgramGardenDashboard
from .components.stock_card import StockCard
from .components.watchlist import Watchlist
from .components.account import Account
from .components.trading_view_chart import TradingViewChart
from .components.order_panel import OrderPanel
from .components.order_book import OrderBook
from .data.provider import DataProvider
from .utils.data_formatter import DataFormatter
from .utils.logger import DashboardLogger, LogLevel, set_log_level, disable_logging, enable_logging

# 로그 시스템 자동 초기화 (WARNING 레벨)
DashboardLogger.initialize(level=LogLevel.WARNING)

__all__ = [
    "ProgramGardenDashboard",
    "StockCard",
    "Watchlist",
    "Account",
    "TradingViewChart",
    "OrderPanel",
    "OrderBook",
    "DataProvider",
    "DataFormatter",
    # 로그 관련
    "LogLevel",
    "set_log_level", 
    "disable_logging",
    "enable_logging"
]