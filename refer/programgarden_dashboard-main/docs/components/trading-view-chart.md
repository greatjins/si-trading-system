# Reference for TradingViewChart

## `TradingViewChart` 추가하기

`TradingViewChart`는 `.add_trading_view_chart()` 메서드를 통해 추가할 수 있습니다.

## 속성

`.add_trading_view_chart()` 메서드는 다음과 같은 속성을 지원합니다.

| 속성명      | 설명                                         | 필수/선택  |
| ----------- | ------------------------------------------- | ---------- |
| symbol      | 종목 심볼                                    | 필수       |
| position    | (row, col, width, height) 위치 튜플          | 선택       |

`symbol`에는 표시할 종목의 심볼을 입력하며, `position`에는 컴포넌트의 위치(행, 열)와 크기(가로, 세로)를 튜플로 지정합니다.

## 사용 예제 코드

```python
# AAPL 종목, 자동 배치
dashboard.add_trading_view_chart("AAPL")

# AAPL 종목, 0행 0열 6x4 크기
dashboard.add_trading_view_chart("AAPL", position=(0, 0, 6, 4))
```