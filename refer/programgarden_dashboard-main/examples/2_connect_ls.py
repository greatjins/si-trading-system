"""
대시보드에 LS Open API를 연결하는 예제입니다.

이 기능을 사용하기 위해 다음 라이브러리 설치가 필요합니다.
> pip install python-dotenv

프로젝트에 `.env` 파일을 생성하고, 다음과 같이 LS Open API 키를 설정하세요:

```
APPKEY=your_app_key
APPSECRET=your_app_secret
```

예시:
```
APPKEY="fas58DHy23j4k5l6m7n8o9p0qrs1t2u3v"
APPSECRET="zXyWvUtSrQpOnMlKjIhGfEdCbA9876543"
```
"""

from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv  # 추가
import os  # 추가

# .env 파일 로드
load_dotenv()


def _run_dashboard():
    dashboard = ProgramGardenDashboard(
        title="LS Open API 연결 예제",  # 대시보드 제목 추가
        app_key=os.getenv("APPKEY", ""),  # LS Open API APPKEY 추가
        app_secret=os.getenv("APPSECRET", ""),  # LS Open API APPSECRET 추가
    )
    dashboard.run()


if __name__ == "__main__":
    _run_dashboard()