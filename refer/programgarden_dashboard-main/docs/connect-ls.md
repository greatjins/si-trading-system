# LS Open API와 연동하기

## LS Open API 신청하기

1. [LS Open API](https://openapi.ls-sec.co.kr/intro) 사이트에 접속합니다.

2. `API 사용신청` 버튼을 클릭하면 로그인 화면으로 이동합니다.

3. LS 증권에 로그인한 뒤, `사용등록/해지` 메뉴에서 `Open API` 신청을 진행합니다. 만약 `Xing API`를 신청하지 않았다면, 먼저 `Xing API` 사용등록을 완료한 후 `Open API`를 신청하세요.

4. 사용등록이 완료되면 앱키와 시크릿키가 발급됩니다.

5. 프로젝트 폴더에 `.env` 파일을 생성하고 아래와 같이 입력합니다.

```
APPKEY="발급받은 앱키를 입력하세요."
APPSECRET="발급받은 시크릿키를 입력하세요."
```

앱키와 시크릿키는 반드시 쌍따옴표(")와 함께 입력해야 합니다.

```
# 입력 예시
APPKEY="FJ32fddE3..."
APPSECRET="AFJnf92Nv..."
```

프로젝트에는 다음과 같은 파일이 준비됩니다.

```
test_pgd.py
.env
```

이제 `test_pgd.py` 파일을 열어 LS Open API 연동 코드를 추가합니다.

```python
from programgarden_dashboard import ProgramGardenDashboard
from dotenv import load_dotenv  # 추가
import os  # 추가

load_dotenv()  # 추가

dashboard = ProgramGardenDashboard(
    app_key=os.getenv("APPKEY", ""),  # 추가
    app_secret=os.getenv("APPSECRET", ""),  # 추가
)
dashboard.add_stock_card("AAPL")
dashboard.run()
```

각 코드의 역할은 다음과 같습니다.

```python
from dotenv import load_dotenv  # .env 파일에서 환경변수 로드
import os  # 환경변수 접근을 위한 라이브러리

load_dotenv()  # .env 파일의 값을 환경변수로 불러옴
```

`load_dotenv`로 `.env` 파일의 값을 불러오고, `os.getenv`로 환경변수를 읽어옵니다. 만약 `.env`에 값이 없으면 빈 문자열을 사용합니다.

```python
dashboard = ProgramGardenDashboard(
    app_key=os.getenv("APPKEY", ""),
    app_secret=os.getenv("APPSECRET", ""),
)
```

이제 대시보드를 실행하면 다음과 같은 로그가 출력됩니다.

```
🚀 ProgramGarden Dashboard 초기화 완료
NiceGUI ready to go on http://127.0.0.1:8080
Sending real request: {'header': {'token': '...', 'tr_type': '3'}, 'body': {'tr_cd': 'GSC', 'tr_key': '82TSLA            '}}, <websockets.asyncio.client.ClientConnection object at 0x0000018253E89ED0>
```

`Sending real request: ...` 로그는 LS Open API와 정상적으로 연동되어 실시간 데이터 요청이 이루어졌음을 의미합니다. 설정이 완료되었다면, 다양한 컴포넌트 활용 방법도 함께 확인해보세요.
