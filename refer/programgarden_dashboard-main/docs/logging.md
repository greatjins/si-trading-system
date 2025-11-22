# 로그 설정 가이드

ProgramGarden Dashboard는 통합 로그 시스템을 제공합니다.

## 기본 설정

기본적으로 **WARNING 레벨 이상만** 출력됩니다:

```python
from programgarden_dashboard import ProgramGardenDashboard

# 기본 사용 - WARNING 이상만 출력
dashboard = ProgramGardenDashboard()
dashboard.add_stock_card("AAPL")
dashboard.run()
```

## 로그 레벨 변경

```python
from programgarden_dashboard import ProgramGardenDashboard, LogLevel, set_log_level  # 추가

# INFO 레벨로 변경 (더 자세한 로그)
set_log_level(LogLevel.INFO)

# DEBUG 레벨로 변경 (모든 로그)
set_log_level(LogLevel.DEBUG)

# ERROR 레벨로 변경 (에러만)
set_log_level(LogLevel.ERROR)

dashboard = ProgramGardenDashboard()
```

## 로그 완전 비활성화

```python
from programgarden_dashboard import ProgramGardenDashboard, disable_logging  # 추가

# 모든 로그 비활성화
disable_logging()

dashboard = ProgramGardenDashboard()
```

## 로그 다시 활성화

```python
from programgarden_dashboard import enable_logging, set_log_level, LogLevel  # 추가

# 로그 다시 활성화
enable_logging()
set_log_level(LogLevel.WARNING)  # 레벨 재설정 필요
```

## 로그 레벨 설명

| 레벨 | 설명 | 사용 시기 |
|------|------|----------|
| `LogLevel.CRITICAL` | 심각한 오류만 | 프로덕션 (최소 로그) |
| `LogLevel.ERROR` | 에러 메시지만 | 프로덕션 (오류 추적) |
| `LogLevel.WARNING` | 경고 이상 | **기본값** (권장) |
| `LogLevel.INFO` | 정보성 메시지 | 개발/디버깅 |
| `LogLevel.DEBUG` | 모든 세부사항 | 상세 디버깅 |

## 권장 사용법

### **프로덕션 환경**
```python
from programgarden_dashboard import set_log_level, LogLevel

# 에러만 출력
set_log_level(LogLevel.ERROR)
```

### **개발 환경**
```python
# 기본 설정 사용 (WARNING 이상)
# 또는 정보성 메시지 포함
set_log_level(LogLevel.INFO)
```

### **디버깅 시**
```python
# 모든 로그 출력
set_log_level(LogLevel.DEBUG)
```

## 로그 출력 형태

```
[programgarden_dashboard.DataProvider] WARNING: LS API 연결 실패, Yahoo로 폴백
[programgarden_dashboard.StockCard.AAPL] ERROR: 데이터 업데이트 실패
[programgarden_dashboard.LSProvider] INFO: WebSocket 연결 완료
```

## 고급 사용법

특정 컴포넌트만 별도 로그 레벨 설정은 지원하지 않습니다. 
라이브러리 전체의 일관된 로그 관리를 위해 통합된 레벨을 사용합니다.

애플리케이션별 로그가 필요한 경우, 표준 Python logging을 따로 사용하세요:

```python
import logging

# 애플리케이션 로그 (별도)
app_logger = logging.getLogger('my_app')
app_logger.setLevel(logging.DEBUG)

# ProgramGarden Dashboard 로그 (통합)
from programgarden_dashboard import set_log_level, LogLevel
set_log_level(LogLevel.WARNING)
```