# Reference for Account

## `Account` 추가하기

`Account`는 `.add_account()` 메서드를 통해 추가할 수 있습니다.

## 속성

`.add_account()` 메서드는 다음과 같은 속성을 지원합니다.

| 속성명            | 설명                                         | 필수/선택  |
| ---------------- | -------------------------------------------- | --------- |
| refresh_interval | 계좌 정보의 자동 새로고침 주기(초 단위)           | 선택       |
| position         | (row, col, width, height) 형태의 위치 지정     | 선택       |

> `Account` 컴포넌트는 LS Open API 연동 시에만 사용할 수 있습니다.

`refresh_interval`은 계좌 정보를 몇 초마다 새로고침할지 설정하며, 기본값은 10초입니다. LS Open API의 정책상 1초에 1회 조회가 최대이므로, 서버 과부하를 방지하기 위해 충분한 간격을 두는 것이 좋습니다.

`position`은 컴포넌트의 배치 위치와 크기를 지정하는 튜플입니다.

## 사용 예제 코드

```python
# 조회 간격 미지정, 자동 배치
dashboard.add_account()

# 조회 간격 3초, 자동 배치
dashboard.add_account(refresh_interval=3)

# 조회 간격 5초, 3행 1열 4x3 크기
dashboard.add_account(refresh_interval=5, position=(3, 1, 4, 3))
```