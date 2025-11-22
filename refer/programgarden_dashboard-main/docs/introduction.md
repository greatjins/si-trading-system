# ProgramGarden Dashboard 소개

## 1. 개요

**ProgramGarden Dashboard**는 파이썬 초보자도 쉽게 사용할 수 있는 해외 주식 대시보드 라이브러리입니다. 단 3줄의 코드만으로 전문적인 주식 트레이딩 대시보드를 구축할 수 있으며, NiceGUI 프레임워크를 기반으로 WTS(Web Trading System) 수준의 기능을 제공합니다.

문서 내용이 이해되지 않거나 개선이 필요한 부분을 발견하셨다면, 언제든지 *GitHub Issues* 또는 프로그램 동산 커뮤니티를 통해 의견을 남겨주세요. 여러분의 피드백은 프로젝트 발전에 큰 도움이 됩니다.

- 프로그램 동산 커뮤니티: https://cafe.naver.com/programgarden

## 2. 프로젝트 배경

이 프로젝트는 커뮤니티 **프로그램 동산**에서 제작되었으며, **LS증권의 공식 지원**을 받아 개발되었습니다. 주식 트레이딩에 관심이 있는 개발자들이 복잡한 UI 구현에 시간을 소비하지 않고, 핵심 트레이딩 로직에 집중할 수 있도록 설계되었습니다.

## 3. 핵심 특징

**ProgramGarden Dashboard**는 파이썬 초보자가 간단한 코드만으로 자신만의 웹 대시보드를 쉽게 만들 수 있도록 설계된 주식 대시보드 라이브러리입니다. 대시보드 생성, 컴포넌트 추가, 대시보드 실행의 세 단계만으로 다양한 유형의 대시보드를 손쉽게 구축할 수 있습니다. 각 컴포넌트에 대한 자세한 설명은 [컴포넌트](components/component.md) 문서를 참고하세요.

대시보드의 UI는 파이썬의 [NiceGUI](https://nicegui.io/) 프레임워크를 기반으로 구현되었습니다. NiceGUI는 [Tailwind CSS](https://tailwindcss.com/)와 [Quasar](https://quasar.dev/)를 활용하여 현대적인 UI 스타일과 다양한 기능을 제공합니다. 사용자는 내장된 UI 컴포넌트를 자유롭게 커스텀할 수 있으며, 앞으로 추가될 *Factory* 기능을 통해 자신만의 디자인을 손쉽게 적용할 수 있습니다. 이를 통해 더욱 다양한 스타일의 대시보드를 경험하실 수 있습니다.

데이터 소스는 LS증권 Open API를 기반으로, 정확한 증권 데이터와 고성능 WebSocket을 활용해 실시간 체결 및 호가 정보를 제공하는 최적화된 웹 대시보드를 구현할 수 있습니다. 앞으로도 대시보드에 필요한 다양한 컴포넌트를 지속적으로 추가할 예정이며, 사용자가 직접 커스텀 컴포넌트를 개발하고 커뮤니티에 공유함으로써 더욱 풍부한 기능의 대시보드를 손쉽게 확장할 수 있는 환경을 마련할 계획입니다.

## 4. 레이아웃 시스템

대시보드는 그리드 레이아웃 시스템을 기반으로 하며, 사용자는 각 컴포넌트의 위치와 크기만 지정하면 손쉽게 UI를 구성할 수 있습니다. 위치를 지정하지 않은 경우 **자동 배치 시스템**이 적용되어 컴포넌트가 적절한 위치에 자동으로 배치됩니다. 크기를 별도로 설정하지 않아도 컴포넌트별 기본값이 적용되어 최적화된 레이아웃을 제공합니다.

## 5. 간단한 사용법
단 세 줄의 코드만으로 손쉽게 나만의 대시보드를 만들 수 있습니다.

```python
from programgarden_dashboard import ProgramGardenDashboard

# 간단한 포트폴리오 모니터링
dashboard = ProgramGardenDashboard("나만의 대시보드")  # 대시보드 생성
dashboard.add_watchlist(["AAPL", "GOOGL", "TSLA", "MSFT"])  # 컴포넌트 자동 배치
dashboard.run()  # 대시보드 서버 실행
```

## 6. 다양한 컴포넌트 추가
```python
# 완전한 트레이딩 워크스테이션
dashboard = ProgramGardenDashboard("나만의 대시보드")

# 주요 종목 모니터링
dashboard.add_stock_card("AAPL", position=(0, 0, 2, 2))   # 0행 0열 2x2 크기
dashboard.add_stock_card("GOOGL", position=(0, 2, 2, 3))   # 0행 2열 2x3 크기
dashboard.add_stock_card("TSLA", position=(0, 4, 3, 2))   # 0행 4열 3x2 크기

# 호가창과 주문 패널
dashboard.add_order_book("AAPL", position=(3, 0, 2, 4))   # 3행 0열 2x4 크기
dashboard.add_order_panel("AAPL", position=(3, 7, 2, 3))  # 3행 7열 2x3 크기

# 포트폴리오 관리
dashboard.add_watchlist(symbols=["GOOGL", "TSLA", "NVDA"], position=(7, 0, 4, 6))  # 7행 0열 4x6 크기

# LS 계좌 잔고
dashboard.add_account(position=(7, 4, 4, 3))  # 7행 4열 4x3 크기

# 차트 분석
dashboard.add_trading_view_chart("AAPL", position=(10, 4, 6, 4))  # 10행 4열 6x4 크기

dashboard.run()
```

## 7. 기술적 우수성

**ProgramGarden Dashboard**는 빠른 초기 실행을 위해 프록시 패턴을 적용하여 컴포넌트 지연 로딩을 지원합니다. 자동 리소스 정리로 메모리 누수를 방지하며, 변경된 데이터만 선택적으로 UI를 갱신하는 조건부 업데이트 방식을 통해 효율적인 성능을 제공합니다.

모듈형 아키텍처를 기반으로 새로운 컴포넌트를 손쉽게 추가할 수 있고, 플러그형 데이터 소스를 통해 다양한 API와 연동이 가능합니다. position 매개변수를 활용하면 사용자가 원하는 대로 레이아웃을 자유롭게 구성할 수 있습니다.

안정성을 위해 포괄적인 예외 처리와 복구 메커니즘을 갖추고 있으며, 주 데이터 소스에 장애가 발생할 경우 Yahoo Finance 데이터로 자동 폴백되는 시스템을 제공합니다.

<br>

## 기여 방법
- GitHub Issues 리포팅
- 기능 제안 및 개선 사항
- 문서화 개선
- 커뮤니티 지원 활동

## 라이선스 및 지원

- **라이선스**: AGPL 3.0
- **Python 버전**: 3.9 이상
- **지원 플랫폼**: Windows
- **공식 지원**: LS증권 파트너십