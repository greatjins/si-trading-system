# ProgramGarden Dashboard

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![NiceGUI](https://img.shields.io/badge/NiceGUI-2.24+-purple.svg)](https://nicegui.io/)
[![Release](https://img.shields.io/github/v/tag/programgarden/programgarden_dashboard?label=release&sort=semver&logo=github)](https://github.com/programgarden/programgarden_dashboard/releases)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](./LICENSE)
[![Company: LS](https://img.shields.io/badge/지원되는_증권사-LS증권-008FC7.svg)]()

![programgarden 그리고 ls](docs/images/programgarden_ls.png)

## 👏 오픈소스 개발 진행 상황
- 해외 주식 주문 관련 기능 추가 예정
- 해외 선물 주문 관련 기능 추가 예정

> **⚠️ 경고**: ProgramGarden Dashboard는 현재 **테스트 버전**이므로 오류를 계속 확인하고 있습니다. 따라서 정식 버전이 출시되기 전까지는 일부 기능들이 제한되어 있습니다. 오픈소스 사용 시 발생하는 문제에 대한 책임은 사용자에게 있으며, 라이선스를 반드시 확인해 주세요. [라이선스 보기](https://github.com/programgarden/programgarden_dashboard/blob/main/LICENSE)

<br>

## 📌 소개
**ProgramGarden Dashboard**는 주식 트레이더를 위한 간편한 시각화 대시보드 오픈소스입니다.
커뮤니티 '프로그램 동산'에서 제작되었으며, **LS증권의 지원**으로 개발되었습니다.

이 프로젝트는 UI 제작의 러닝 커브를 낮춰 초보 개발자도 손쉽게 사용할 수 있도록 설계되었습니다.

`NiceGUI`를 기반으로 설계되었으며, WTS 수준으로도 활용 가능한 대시보드입니다.

<br>

## ✨ 간단한 사용법

- **ProgramGarden Dashboard** 설치
```python
pip install programgarden-dashboard
```

<br>

- **단 3줄로 투자 대시보드 완성**

```python
# 기본 사용법 (Yahoo Finance 데이터)
from programgarden_dashboard import ProgramGardenDashboard

dashboard = ProgramGardenDashboard("내 투자 대시보드")
dashboard.add_stock_card("AAPL")
dashboard.run()
```

<br>

## 📚 Gitbook 문서

https://programgarden-dashboard.gitbook.io/docs

<br>

## 🌍 관련된 콘텐츠

- 자동화매매 라이브러리: [https://github.com/programgarden/programgarden.git](https://github.com/programgarden/programgarden.git)
- 공식사이트: https://programgarden.com
- 프로그램 동산 유튜브: https://youtube.com/@programgarden
- 시스템 트레이더 커뮤니티: https://cafe.naver.com/programgarden
- LS증권 유튜브: https://www.youtube.com/@lssec
- 비즈니스 문의: coding@programgarden.com

<br>

## 👥 운영진

* **프로그램 동산** – DSL 개발 담당 [LinkedIn](https://www.linkedin.com/in/masterjyj/)
* **라쿠너리 동산** – 시각화, WTS 개발 담당 [LinkedIn](https://www.linkedin.com/in/rakunary)
* **클라우드 동산** – AI & 서버 개발 담당 [LinkedIn](https://www.linkedin.com/in/philip-sung-jae-cho/)
* **디자인 동산** – 콘텐츠와 디자인 담당 [LinkedIn](https://www.linkedin.com/in/jina-jang-4561b717a/)