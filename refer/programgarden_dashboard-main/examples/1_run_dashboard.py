"""
빈 대시보드를 실행하는 예제입니다.

라이브러리를 사용하기 위해 라이브러리 설치가 필요합니다.
> pip install programgarden-dashboard
"""

from programgarden_dashboard import ProgramGardenDashboard


def _run_dashboard():
    # 대시보드 생성
    dashboard = ProgramGardenDashboard()

    # 대시보드 실행
    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()