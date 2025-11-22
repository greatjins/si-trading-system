"""
통합 대시보드 예제입니다.
"""

from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()


def _run_dashboard():
    dashboard = ProgramGardenDashboard(
        title="👑 프로그램 동산 웹 대시보드 라이브러리 (WTS)",
        app_key=os.getenv("APPKEY", ""),
        app_secret=os.getenv("APPSECRET", ""),
    )
    
    # 12열 기준 첫 행 자동 배치
    dashboard.add_stock_card('TSLA')
    dashboard.add_stock_card('AAPL')
    dashboard.add_stock_card('AMZN')
    dashboard.add_stock_card('GOOGL')
    dashboard.add_watchlist(["MSFT", "NFLX", "NVDA", "META", "IBM"], key="내 감시 목록")

    # 12열 기준 두 번째 행 자동 배치
    dashboard.add_trading_view_chart("AAPL")
    dashboard.add_order_book("AAPL")
    dashboard.add_account()

    # 12열 기준 세 번째 행 자동 배치
    dashboard.add_trading_view_chart("TSLA")
    dashboard.add_order_panel("TSLA")

    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()