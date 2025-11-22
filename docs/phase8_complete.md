# Phase 8: 전략 레지스트리 구현 완료

## 개요
전략 동적 로딩 및 관리를 위한 레지스트리 시스템을 구현하여 플러그인 아키텍처를 완성했습니다.

## 구현 내용

### 1. 전략 레지스트리 구조
```
core/strategy/
├── base.py                # BaseStrategy 추상 클래스
├── registry.py            # StrategyRegistry (싱글톤)
└── examples/
    └── ma_cross.py        # MACrossStrategy (메타데이터 포함)

api/routes/
└── strategies.py          # 전략 관리 API
```

### 2. 주요 컴포넌트

#### StrategyRegistry (싱글톤)
- **전략 등록**: 수동/자동 등록
- **전략 조회**: 이름으로 클래스 조회
- **메타데이터 관리**: 설명, 버전, 파라미터 정의
- **인스턴스 생성**: 파라미터 기반 인스턴스 생성
- **자동 탐색**: 패키지 내 전략 자동 발견

#### StrategyMetadata
- **이름**: 전략 고유 이름
- **설명**: 전략 설명
- **작성자**: 개발자 정보
- **버전**: 버전 관리
- **파라미터**: 파라미터 정의 (타입, 기본값, 범위)

#### @strategy 데코레이터
- **선언적 등록**: 클래스 데코레이터로 간편 등록
- **메타데이터 정의**: 데코레이터 인자로 메타데이터 설정

### 3. 전략 등록 방법

#### 방법 1: 데코레이터 사용 (권장)
```python
from core.strategy.base import BaseStrategy
from core.strategy.registry import strategy

@strategy(
    name="MomentumStrategy",
    description="모멘텀 기반 전략",
    author="John Doe",
    version="1.0.0",
    parameters={
        "lookback": {
            "type": "int",
            "default": 20,
            "min": 5,
            "max": 100,
            "description": "룩백 기간"
        },
        "threshold": {
            "type": "float",
            "default": 0.02,
            "min": 0.0,
            "max": 0.1,
            "description": "임계값"
        }
    }
)
class MomentumStrategy(BaseStrategy):
    def __init__(self, params: dict):
        super().__init__(params)
        self.lookback = self.get_param("lookback", 20)
        self.threshold = self.get_param("threshold", 0.02)
    
    def on_bar(self, bars, positions, account):
        # 전략 로직
        return []
```

#### 방법 2: 수동 등록
```python
from core.strategy.registry import StrategyRegistry

StrategyRegistry.register(
    name="MyStrategy",
    strategy_class=MyStrategy,
    description="내 전략",
    author="Me",
    version="1.0.0",
    parameters={...}
)
```

#### 방법 3: 자동 탐색
```python
from core.strategy.registry import StrategyRegistry

# 패키지 내 모든 전략 자동 등록
StrategyRegistry.auto_discover("core.strategy.examples")
```

### 4. 전략 사용 방법

#### 전략 목록 조회
```python
strategies = StrategyRegistry.list_strategies()
# ['MACrossStrategy', 'MomentumStrategy', ...]
```

#### 전략 메타데이터 조회
```python
metadata = StrategyRegistry.get_metadata("MACrossStrategy")
print(metadata.name)         # "MACrossStrategy"
print(metadata.version)      # "1.0.0"
print(metadata.parameters)   # {...}
```

#### 전략 인스턴스 생성
```python
strategy = StrategyRegistry.create_instance(
    "MACrossStrategy",
    symbol="005930",
    short_period=5,
    long_period=20,
    position_size=0.1
)
```

### 5. API 엔드포인트

#### 전략 관리 API (`/api/strategies`)

**전략 목록 조회**
```
GET /api/strategies/list
```

**응답**
```json
[
  {
    "name": "MACrossStrategy",
    "description": "이동평균 교차 전략",
    "author": "LS HTS Team",
    "version": "1.0.0"
  }
]
```

**전략 상세 정보**
```
GET /api/strategies/{strategy_name}
```

**응답**
```json
{
  "name": "MACrossStrategy",
  "description": "이동평균 교차 전략",
  "author": "LS HTS Team",
  "version": "1.0.0",
  "parameters": {
    "symbol": {
      "type": "str",
      "default": "005930",
      "description": "종목 코드"
    },
    "short_period": {
      "type": "int",
      "default": 5,
      "min": 2,
      "max": 50,
      "description": "단기 이동평균 기간"
    },
    "long_period": {
      "type": "int",
      "default": 20,
      "min": 10,
      "max": 200,
      "description": "장기 이동평균 기간"
    },
    "position_size": {
      "type": "float",
      "default": 0.1,
      "min": 0.01,
      "max": 1.0,
      "description": "포지션 크기"
    }
  },
  "class_name": "MACrossStrategy",
  "module": "core.strategy.examples.ma_cross"
}
```

**전략 재탐색**
```
POST /api/strategies/discover
```

**전략 재로드**
```
POST /api/strategies/reload
```

### 6. 전략 메타데이터 정의

#### 파라미터 타입
- **int**: 정수
- **float**: 실수
- **str**: 문자열
- **bool**: 불리언
- **list**: 리스트
- **dict**: 딕셔너리

#### 파라미터 속성
```python
{
    "parameter_name": {
        "type": "int",              # 타입
        "default": 20,              # 기본값
        "min": 5,                   # 최소값 (선택)
        "max": 100,                 # 최대값 (선택)
        "description": "설명",      # 설명
        "required": False           # 필수 여부 (선택)
    }
}
```

### 7. 플러그인 아키텍처

#### 전략 디렉토리 구조
```
core/strategy/
├── base.py
├── registry.py
├── examples/              # 기본 제공 전략
│   ├── ma_cross.py
│   └── momentum.py
└── custom/                # 사용자 정의 전략
    ├── my_strategy.py
    └── advanced_strategy.py
```

#### 사용자 정의 전략 추가
1. `core/strategy/custom/` 디렉토리에 전략 파일 생성
2. `@strategy` 데코레이터로 메타데이터 정의
3. 서버 재시작 또는 `/api/strategies/reload` 호출

### 8. 테스트 실행

```bash
# 서버 시작
python -m uvicorn api.main:app --reload

# 다른 터미널에서 테스트
python examples/test_strategy_registry.py
```

### 9. 예상 출력

```
=== Strategy List ===
Status: 200
Total Strategies: 1

- MACrossStrategy (v1.0.0)
  Author: LS HTS Team
  Description: 이동평균 교차 전략 - 골든크로스/데드크로스 기반 매매

=== Strategy Detail: MACrossStrategy ===
Status: 200
Name: MACrossStrategy
Version: 1.0.0
Author: LS HTS Team
Class: MACrossStrategy
Module: core.strategy.examples.ma_cross

Parameters:
  - symbol:
      Type: str
      Default: 005930
      Description: 종목 코드
  - short_period:
      Type: int
      Default: 5
      Range: [2, 50]
      Description: 단기 이동평균 기간
  - long_period:
      Type: int
      Default: 20
      Range: [10, 200]
      Description: 장기 이동평균 기간
  - position_size:
      Type: float
      Default: 0.1
      Range: [0.01, 1.0]
      Description: 포지션 크기

=== Strategy Registry Usage ===
Registered Strategies: ['MACrossStrategy']

Strategy: MACrossStrategy
  Version: 1.0.0
  Author: LS HTS Team
  Parameters: ['symbol', 'short_period', 'long_period', 'position_size']

Creating instance of MACrossStrategy...
Strategy instance created: MACrossStrategy
Parameters: {'symbol': '005930', 'short_period': 5, 'long_period': 20, 'position_size': 0.1}
```

### 10. 통합 사용 예제

#### 백테스트에서 사용
```python
from core.strategy.registry import StrategyRegistry
from core.backtest.engine import BacktestEngine

# 전략 인스턴스 생성
strategy = StrategyRegistry.create_instance(
    "MACrossStrategy",
    symbol="005930",
    short_period=5,
    long_period=20
)

# 백테스트 실행
engine = BacktestEngine(initial_capital=10_000_000)
result = engine.run(strategy, data)
```

#### 실시간 실행에서 사용
```python
from core.strategy.registry import StrategyRegistry
from core.execution.engine import ExecutionEngine

# 전략 인스턴스 생성
strategy = StrategyRegistry.create_instance(
    "MACrossStrategy",
    symbol="005930",
    short_period=5,
    long_period=20
)

# 실시간 실행
engine = ExecutionEngine(broker=broker, strategy=strategy)
await engine.start()
```

#### API에서 사용
```python
# 전략 시작 API
@router.post("/start")
async def start_strategy(request: StrategyStartRequest):
    # 레지스트리에서 전략 생성
    strategy = StrategyRegistry.create_instance(
        request.strategy_name,
        **request.parameters
    )
    
    # 실행 엔진 시작
    engine = ExecutionEngine(broker=broker, strategy=strategy)
    await engine.start()
```

### 11. 향후 개선 사항

#### 전략 마켓플레이스
- 전략 공유 플랫폼
- 전략 평가 및 리뷰
- 전략 구매/판매

#### 전략 버전 관리
- Git 기반 버전 관리
- 전략 히스토리 추적
- 롤백 기능

#### 전략 검증
- 파라미터 유효성 검사
- 전략 코드 정적 분석
- 보안 검사

#### 전략 성능 추적
- 전략별 성과 기록
- 실시간 성과 모니터링
- 성과 비교 대시보드

## 결론

Phase 8에서 전략 레지스트리 시스템을 성공적으로 구현했습니다. 동적 로딩, 메타데이터 관리, 플러그인 아키텍처를 통해 확장 가능하고 유지보수가 쉬운 전략 관리 시스템을 완성했습니다.

## 전체 Phase 완료!

Phase 1~8까지 모든 핵심 기능이 완료되었습니다:
- ✅ Phase 1: 브로커 계층
- ✅ Phase 2: 백테스트 엔진
- ✅ Phase 3: AutoML
- ✅ Phase 4: 실시간 실행 엔진
- ✅ Phase 5: FastAPI 서버
- ✅ Phase 6: 인증 시스템
- ✅ Phase 7: WebSocket 실시간 통신
- ✅ Phase 8: 전략 레지스트리

**LS증권 개인화 HTS 플랫폼의 백엔드 시스템이 완성되었습니다!**
