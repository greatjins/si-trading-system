# Requirements Document

## Introduction

백테스트 결과를 시각적으로 분석할 수 있는 기능을 제공합니다. 포트폴리오 백테스트에서 선별된 각 종목의 매매 시점과 수익률을 차트와 함께 확인할 수 있어야 합니다.

## Glossary

- **System**: 백테스트 시각화 시스템
- **User**: HTS 사용자 (트레이더)
- **Trade**: 매수 또는 매도 거래 기록
- **Position**: 특정 종목의 보유 포지션
- **Equity Curve**: 시간에 따른 자산 변화 곡선
- **Chart**: 가격 차트 (캔들스틱 + 매매 시점 표시)

## Requirements

### Requirement 1

**User Story:** As a trader, I want to see a list of all traded symbols with their performance metrics, so that I can quickly identify which stocks performed well or poorly.

#### Acceptance Criteria

1. WHEN a portfolio backtest completes THEN the System SHALL display a list of all traded symbols
2. WHEN displaying the symbol list THEN the System SHALL show symbol code, name, total return percentage, number of trades, and win rate for each symbol
3. WHEN a symbol has positive return THEN the System SHALL display it in green color
4. WHEN a symbol has negative return THEN the System SHALL display it in red color
5. WHEN the user clicks on a symbol THEN the System SHALL display detailed chart view for that symbol

### Requirement 2

**User Story:** As a trader, I want to see a price chart with buy/sell markers, so that I can visually analyze the strategy's entry and exit points.

#### Acceptance Criteria

1. WHEN a user selects a symbol from the list THEN the System SHALL display a candlestick chart for that symbol
2. WHEN displaying the chart THEN the System SHALL show OHLC data for the backtest period
3. WHEN a buy trade occurred THEN the System SHALL display an upward arrow marker at the entry price and timestamp
4. WHEN a sell trade occurred THEN the System SHALL display a downward arrow marker at the exit price and timestamp
5. WHEN the user hovers over a trade marker THEN the System SHALL display a tooltip with trade details (price, quantity, timestamp, P&L)

### Requirement 3

**User Story:** As a trader, I want to see detailed trade history for each symbol, so that I can analyze individual trade performance.

#### Acceptance Criteria

1. WHEN viewing a symbol's chart THEN the System SHALL display a trade history table below the chart
2. WHEN displaying trade history THEN the System SHALL show entry date, entry price, exit date, exit price, quantity, return percentage, and holding period for each trade
3. WHEN a trade is profitable THEN the System SHALL highlight the return in green
4. WHEN a trade is unprofitable THEN the System SHALL highlight the return in red
5. WHEN the user clicks on a trade row THEN the System SHALL highlight the corresponding markers on the chart

### Requirement 4

**User Story:** As a trader, I want to see the overall equity curve, so that I can understand the portfolio's performance over time.

#### Acceptance Criteria

1. WHEN viewing backtest results THEN the System SHALL display an equity curve chart at the top
2. WHEN displaying the equity curve THEN the System SHALL show portfolio value over time
3. WHEN displaying the equity curve THEN the System SHALL mark the maximum drawdown period
4. WHEN the user hovers over the equity curve THEN the System SHALL display date and portfolio value
5. WHEN the equity curve reaches a new high THEN the System SHALL visually indicate it

### Requirement 5

**User Story:** As a trader, I want to filter and sort the symbol list, so that I can focus on specific performance criteria.

#### Acceptance Criteria

1. WHEN viewing the symbol list THEN the System SHALL provide sort options for return, trades count, and win rate
2. WHEN the user clicks a column header THEN the System SHALL sort the list by that column
3. WHEN sorting by return THEN the System SHALL order from highest to lowest by default
4. WHEN the user clicks the same column header again THEN the System SHALL reverse the sort order
5. WHEN the user applies a filter THEN the System SHALL update the list to show only matching symbols

### Requirement 6

**User Story:** As a system developer, I want the backend to provide detailed trade data per symbol, so that the frontend can render charts and tables efficiently.

#### Acceptance Criteria

1. WHEN a backtest completes THEN the System SHALL store trades grouped by symbol
2. WHEN the frontend requests backtest results THEN the System SHALL return trades organized by symbol
3. WHEN returning trade data THEN the System SHALL include entry/exit timestamps, prices, quantities, and P&L
4. WHEN returning trade data THEN the System SHALL calculate per-symbol metrics (total return, win rate, trade count)
5. WHEN the frontend requests OHLC data for a symbol THEN the System SHALL return price data for the backtest period

### Requirement 7

**User Story:** As a trader, I want to compare multiple backtest runs, so that I can evaluate different strategy parameters.

#### Acceptance Criteria

1. WHEN viewing backtest history THEN the System SHALL display a list of previous backtest runs
2. WHEN the user selects multiple backtest runs THEN the System SHALL display their equity curves on the same chart
3. WHEN comparing backtests THEN the System SHALL show key metrics side by side
4. WHEN comparing backtests THEN the System SHALL highlight the best performing run
5. WHEN the user hovers over a comparison chart THEN the System SHALL show values for all selected runs
