"""
Account 컴포넌트를 추가하는 예제입니다.
"""

from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()


def _run_dashboard():
    dashboard = ProgramGardenDashboard(
        title="Account 추가 예제",
        app_key=os.getenv("APPKEY", ""),
        app_secret=os.getenv("APPSECRET", ""),
    )

    # 자동 배치로 Account 추가
    dashboard.add_account()

    # 지정 위치에 Account 추가
    dashboard.add_account(position=(2, 0, 4, 3))

    # 계좌 새로고침 주기 설정 (30초, 기본 10초)
    # LS Open API의 최소 주기는 1초입니다.
    dashboard.add_account(refresh_interval=30)

    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()