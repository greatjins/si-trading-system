# ProgramGarden Dashboard 기본 사용법

## 1. ProgramGarden Dashboard 설치하기

사용 중인 IDE(예: VS Code)에서 터미널을 열고 아래 명령어를 입력하세요.

```
pip install programgarden-dashboard
```

설치가 완료되면 `test_pgd.py` 파일을 생성하고 다음 코드를 입력합니다.

```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard()
```

코드를 실행했을 때 터미널에 아래와 같은 메시지가 출력되면 설치가 정상적으로 완료된 것입니다.

```
🚀 ProgramGarden Dashboard 초기화 완료
```

이제 **ProgramGarden Dashboard**의 자세한 사용법을 알아보겠습니다!

## 2. 웹 대시보드 실행하기

`test_pgd.py` 파일에 아래와 같이 코드를 한 줄 추가해보세요.

```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard()
dashboard.run()  # 추가
```

코드를 실행하면 다음과 같은 로그가 출력됩니다.

```
🚀 ProgramGarden Dashboard 초기화 완료
NiceGUI ready to go on http://127.0.0.1:8080
2025-09-27 21:35:06,993 - src.programgarden_dashboard.data.ls.ls_provider - ERROR - ❌ LS API 연결 실패: ('appkey 또는 secretkey가 존재하지 않습니다.', 'APPKEY_NOT_FOUND')
2025-09-27 21:35:06,993 - src.programgarden_dashboard.data.provider - WARNING - LS WebSocket 연결 실패 → Yahoo 폴백: LS API에 먼저 연결해주세요. connect() 호출 필요
```

이제 여러분만의 대시보드가 자동으로 웹 브라우저에 열리게 될 것입니다. 앞으로 원하는 대로 하나씩 꾸며가며 나만의 주식 대시보드를 구축할 수 있습니다. 더 자세한 설명이나 가이드가 필요하다면, 우측 상단의 원형 테두리 물음표(`?`) 아이콘을 클릭해 사용자 가이드 페이지에서 단계별로 학습할 수 있습니다.

## 3. 컴포넌트 추가하기

- ### 자동 배치

이제 비어 있는 대시보드를 하나씩 채워봅시다. 먼저 단일 종목 정보를 보여주는 주식 카드(`StockCard`) 컴포넌트를 추가해볼까요? `test_pgd.py` 파일에 아래와 같이 코드를 한 줄 추가하면 됩니다.

```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard()
dashboard.add_stock_card("AAPL")  # 추가
dashboard.run()
```

`dashboard.`를 입력하면 사용할 수 있는 다양한 메서드 목록이 나타납니다. 그중 `add_stock_card()` 메서드를 사용해 `StockCard` 컴포넌트를 추가할 수 있습니다. 예제에서는 `"AAPL"`을 입력했는데, 이는 미국의 대표 기업 애플의 정보를 보기 위함입니다. 코드를 실행하면 대시보드에 작은 사이즈의 `StockCard`가 생성된 것을 확인할 수 있습니다.

- ### 원하는 위치에 배치

컴포넌트의 위치가 불편하다면 원하는 위치에 배치할 수 있습니다. 코드를 아래와 같이 수정해보세요.

```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard()
dashboard.add_stock_card("AAPL", position=(1, 5, 2, 3))  # 수정
dashboard.run()
```

실행하면 대시보드 중앙에 컴포넌트가 생성되고, 사이즈도 2×3의 직사각형 모양이 됩니다. `position`의 앞 두 값은 행과 열, 뒤 두 값은 가로와 세로 크기를 의미합니다(행과 열의 시작은 0). 이제 원하는 위치에 컴포넌트를 자유롭게 배치할 수 있습니다.

- ### 위치가 겹치는 경우

컴포넌트를 추가하다 보면 위치가 겹치는 상황이 발생할 수 있습니다. 이 경우 그리드 레이아웃 시스템이 자동으로 겹치는 컴포넌트를 감지해 적절한 위치에 배치합니다.

- ### 더 많은 컴포넌트 배치하기

더 많은 컴포넌트를 배치하고 싶다면 같은 코드를 여러 번 반복해서 작성하면 됩니다.

```python
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard()
dashboard.add_stock_card("AAPL")  # 수정
dashboard.add_stock_card("TSLA")  # 추가
dashboard.add_stock_card("MSFT")  # 추가
dashboard.add_stock_card("AMZN")  # 추가
dashboard.add_stock_card("NFLX")  # 추가
dashboard.run()
```

예제 코드에서는 모두 종목만 입력하고 `position`을 입력하지 않았습니다. 그래도 괜찮습니다. 그리드 레이아웃 시스템이 자동으로 위치를 정해줄 테니까요.

## 4. 대시보드 속성

대시보드에는 4가지 주요 속성이 있습니다: `title`, `appkey`, `appsecret`, `user_guide`. 이 중 `appkey`와 `appsecret`은 [LS 증권 연동하기](connect-ls.md) 문서에서 자세히 다루므로, 여기서는 `title`과 `user_guide`에 대해 설명합니다.

| 속성명      | 설명                                         | 필수/선택 |
| ----------- | ------------------------------------------- | --------- |
| title       | 대시보드의 상단과 브라우저 탭에 표시될 제목      | 선택      |
| user_guide  | 사용자 가이드 버튼 표시 여부                    | 선택      |

`title`은 대시보드 상단과 웹 브라우저 탭에 표시되는 제목을 지정합니다.

`user_guide`는 대시보드에 사용자 가이드 페이지로 이동할 수 있는 버튼을 표시할지 여부를 설정합니다.

## 5. 대시보드 실행 속성

대시보드를 실행하는 `run` 메서드에는 여러가지 속성이 있습니다.

| 속성명   | 타입   | 기본값         | 설명                                      |
| -------- | ------ | -------------- | ----------------------------------------- |
| favicon  | str    | `''`           | 브라우저 탭에 표시될 파비콘 이미지 경로      |
| host     | str    | `'127.0.0.1'`  | 대시보드 서버가 바인딩될 호스트 주소         |
| port     | int    | `8080`         | 대시보드 서버가 사용할 포트 번호             |
| show     | bool   | `True`         | 실행 시 웹 브라우저 자동 오픈 여부           |
| reload   | bool   | `False`        | 코드 변경 시 자동 리로드 활성화 여부         |

`favicon`은 웹 브라우저 탭에 표시될 파비콘(작은 아이콘) 이미지의 경로를 지정합니다.

`host`는 대시보드 서버가 바인딩될 IP 주소를 지정합니다. 기본값은 `'127.0.0.1'`로 로컬 환경에서만 접근할 수 있습니다. 외부 네트워크에서도 접속 가능하게 하려면 `'0.0.0.0'`으로 설정하세요.

`port`는 대시보드 서버가 사용할 포트 번호를 지정합니다. 기본값은 8080입니다.

`show`는 대시보드 실행 시 웹 브라우저를 자동으로 열지 여부를 결정합니다. 기본값은 True입니다.

`reload`는 코드 변경 시 대시보드가 자동으로 리로드(새로고침)될지 여부를 설정합니다. 기본값은 False입니다.