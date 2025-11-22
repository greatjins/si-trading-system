"""
Watchlist 컴포넌트를 추가하는 예제입니다.
"""

from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()


def _run_dashboard():
    dashboard = ProgramGardenDashboard(
        title="Watchlist 추가 예제",
        app_key=os.getenv("APPKEY", ""),
        app_secret=os.getenv("APPSECRET", ""),
    )

    # 자동 배치로 Watchlist 추가
    dashboard.add_watchlist(["AAPL", "GOOGL"])

    # 지정 위치에 Watchlist 추가
    dashboard.add_watchlist(["TSLA, MSFT"], position=(2, 0, 4, 3))

    # key 지정하여 Watchlist 추가
    # key 지정 시 종목 리스트가 로컬에 저장되고
    # 다음 대시보드 실행 시 자동으로 로컬에 저장된 종목 리스트 불러옵니다.
    dashboard.add_watchlist(
        ["AMZN", "NFLX", "META"],
        key="my_watchlist",
    )

    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()