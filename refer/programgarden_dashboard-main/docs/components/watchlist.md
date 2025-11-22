# Reference for Watchlist

## `Watchlist` 추가하기

`Watchlist`는 `.add_watchlist()` 메서드를 통해 추가할 수 있습니다.

## 속성

`.add_watchlist()` 메서드는 아래의 속성을 가집니다.

| 속성명       | 설명                                         | 필수/선택  |
| ----------- | -------------------------------------------- | ---------- |
| symbols     | 종목 심볼 리스트                               | 선택       |
| position    | (row, col, width, height) 위치 튜플           | 선택       |
| key         | Watchlist 식별자 (영구 저장용)                  | 선택       |

`symbols`에는 여러 종목 심볼을 리스트로 입력할 수 있으며, `position`은 컴포넌트의 위치와 크기를 지정합니다.

`key`를 입력하지 않으면, `symbols`에 입력된 종목만 Watchlist에 등록되고 대시보드 종료 시 저장되지 않습니다. 반면, `key`를 지정하면 해당 `key`로 저장된 종목 리스트가 있을 경우 이를 불러와 등록하며, 저장된 데이터가 없으면 `symbols`에 입력된 종목들이 등록됩니다. 또한, `key`가 지정된 경우 대시보드 종료 시 Watchlist의 종목 리스트가 로컬에 저장되고, 동일한 `key`로 Watchlist를 생성하면 저장된 리스트를 자동으로 불러옵니다.

## 사용 예제 코드

```python
# AAPL, TSLA, MSFT 종목, 자동 배치, key 미지정
dashboard.add_watchlist(["AAPL", "TSLA", "MSFT"])

# AAPL, TSLA, MSFT 종목, 2행 3열 4x3 크기, key 미지정
dashboard.add_watchlist(["AAPL", "TSLA", "MSFT"], position=(2, 3, 4, 3))

# AAPL, TSLA, MSFT 종목, 2행 3열 4x3 크기, key 지정
dashboard.add_watchlist(["AAPL", "TSLA", "MSFT"], position=(2, 3, 4, 3), key="대장주")
```