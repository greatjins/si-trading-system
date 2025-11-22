# ProgramGarden Dashboard Components

## 1. 컴포넌트란?

컴포넌트는 레고 블록처럼 다양한 디자인과 프로그래밍 요소를 조합해 하나의 기능을 수행하는 독립적이고 재사용 가능한 단위입니다. 프론트엔드에서는 버튼, 검색창, 이미지 슬라이더 등 다양한 요소가 컴포넌트로 불립니다. 그러나 이 문서에서는 UI의 세부 요소가 아닌, 대시보드의 주요 기능을 담당하는 주식 관련 컴포넌트(예: `StockCard`)를 중심으로 설명합니다.

## 2. 컴포넌트의 종류

**ProgramGarden Dashboard**에서 제공하는 컴포넌트는 다음과 같습니다.

### [StockCard](components/stock-card.md)

단일 종목의 OHLCV(시가, 고가, 저가, 종가, 거래량)와 실시간 가격 변동을 카드 형태로 표시합니다.

### [Watchlist](components/watchlist.md)

여러 종목의 실시간 가격과 변동률을 테이블로 감시할 수 있는 컴포넌트입니다.

### [TradingViewChart](components/trading-view-chart.md)

TradingView의 강력한 차트 엔진을 활용하여 실시간 가격, 거래량, 다양한 기술적 지표(이동평균선, RSI 등)를 시각적으로 제공합니다.

### [Account](components/account.md)

LS 증권 API로부터 수신한 잔고 및 계좌 정보를 테이블 형태로 보여줍니다.

### [OrderPanel](components/order-panel.md)

LS Open API를 기반으로 매수, 매도, 정정, 취소 등 주식 주문을 처리하는 패널입니다.

### [OrderBook](components/order-book.md)

LS Open API를 통해 실시간으로 호가(매수/매도 가격대 및 잔량)를 시각적으로 표시합니다.

## 3. 컴포넌트 추가 개발 계획

사용자가 더욱 전문화된 대시보드를 사용할 수 있도록 실제 매매에 필요한 컴포넌트들을 지속적으로 추가할 예정입니다.

## 4. 커스텀 컴포넌트

기본 제공 컴포넌트가 부족하다면 직접 개발해보는 것도 가능합니다. 커스텀 컴포넌트 개발 및 공유를 위한 환경을 구축 중이며, 앞으로 나만의 컴포넌트를 개발하고 커뮤니티에 공유해 다양한 대시보드 경험을 제공할 수 있습니다.