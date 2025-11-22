"""
OrderPanel 컴포넌트를 추가하는 예제입니다.

OrderPanel 컴포넌트는 아직 구현 중입니다.
"""

from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()


def _run_dashboard():
    dashboard = ProgramGardenDashboard(
        title="OrderPanel 추가 예제",
        app_key=os.getenv("APPKEY", ""),
        app_secret=os.getenv("APPSECRET", ""),
    )

    # 자동 배치로 OrderPanel 추가
    dashboard.add_order_panel('AAPL')

    # 지정 위치에 OrderPanel 추가
    dashboard.add_order_panel('TSLA', position=(0, 2, 2, 3))

    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()