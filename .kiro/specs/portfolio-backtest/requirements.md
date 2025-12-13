# Requirements Document

## Introduction

포트폴리오 백테스트 시스템은 전략이 매일 종목 유니버스를 동적으로 선택하고, 여러 종목을 동시에 매매할 수 있도록 하는 기능입니다. 현재 단일 종목 백테스트만 지원하는 시스템을 확장하여, 실전 트레이딩과 동일한 방식으로 포트폴리오를 관리합니다.

## Glossary

- **Portfolio**: 여러 종목을 동시에 보유하는 투자 조합
- **Universe**: 전략이 선택 가능한 종목 집합
- **Rebalancing**: 포트폴리오 구성을 재조정하는 행위
- **Strategy**: 매매 규칙을 정의한 알고리즘
- **BacktestEngine**: 과거 데이터로 전략을 시뮬레이션하는 엔진
- **Position**: 특정 종목의 보유 수량과 평균 단가

## Requirements

### Requirement 1

**User Story:** As a 트레이더, I want 전략이 매일 종목을 선택하도록, so that 실전과 동일한 방식으로 백테스트할 수 있다

#### Acceptance Criteria

1. WHEN 백테스트가 시작되면 THEN the BacktestEngine SHALL 전략의 종목 선택 메서드를 호출한다
2. WHEN 매 거래일마다 THEN the Strategy SHALL 현재 시장 상황에 맞는 종목 리스트를 반환한다
3. WHEN 종목 선택 조건이 변경되면 THEN the Strategy SHALL 새로운 종목 리스트를 반환한다
4. WHEN 종목 리스트가 비어있으면 THEN the BacktestEngine SHALL 현금 보유 상태를 유지한다
5. WHEN 종목 선택에 실패하면 THEN the BacktestEngine SHALL 에러를 기록하고 계속 진행한다

### Requirement 2

**User Story:** As a 트레이더, I want 여러 종목을 동시에 매매하도록, so that 분산 투자 전략을 테스트할 수 있다

#### Acceptance Criteria

1. WHEN 전략이 여러 종목에 대한 매수 신호를 생성하면 THEN the BacktestEngine SHALL 모든 신호를 처리한다
2. WHEN 자본이 부족하면 THEN the BacktestEngine SHALL 우선순위에 따라 일부 신호만 처리한다
3. WHEN 포지션 한도를 초과하면 THEN the BacktestEngine SHALL 신규 매수를 거부한다
4. WHEN 여러 종목을 보유 중이면 THEN the BacktestEngine SHALL 각 종목의 손익을 독립적으로 계산한다
5. WHEN 포트폴리오 가치를 조회하면 THEN the BacktestEngine SHALL 모든 포지션의 합계를 반환한다

### Requirement 3

**User Story:** As a 트레이더, I want 포트폴리오를 리밸런싱하도록, so that 목표 비중을 유지할 수 있다

#### Acceptance Criteria

1. WHEN 리밸런싱 주기가 도래하면 THEN the Strategy SHALL 목표 포트폴리오를 계산한다
2. WHEN 현재 포트폴리오와 목표가 다르면 THEN the Strategy SHALL 매수/매도 신호를 생성한다
3. WHEN 종목이 유니버스에서 제외되면 THEN the Strategy SHALL 해당 종목을 청산한다
4. WHEN 신규 종목이 추가되면 THEN the Strategy SHALL 목표 비중만큼 매수한다
5. WHEN 리밸런싱 비용이 임계값을 초과하면 THEN the Strategy SHALL 리밸런싱을 건너뛸 수 있다

### Requirement 4

**User Story:** As a 트레이더, I want 종목 선택 조건을 설정하도록, so that 다양한 전략을 테스트할 수 있다

#### Acceptance Criteria

1. WHEN 전략을 생성하면 THEN the Strategy SHALL 종목 선택 조건을 파라미터로 받는다
2. WHEN 재무 조건을 설정하면 THEN the Strategy SHALL PER, PBR, ROE 등으로 필터링한다
3. WHEN 기술적 조건을 설정하면 THEN the Strategy SHALL 이동평균, 거래량 등으로 필터링한다
4. WHEN 시장 조건을 설정하면 THEN the Strategy SHALL KOSPI/KOSDAQ, 시가총액 등으로 필터링한다
5. WHEN 최대 종목 수를 설정하면 THEN the Strategy SHALL 상위 N개만 선택한다

### Requirement 5

**User Story:** As a 트레이더, I want 백테스트 결과를 분석하도록, so that 전략의 성과를 평가할 수 있다

#### Acceptance Criteria

1. WHEN 백테스트가 완료되면 THEN the BacktestEngine SHALL 총 수익률을 계산한다
2. WHEN 백테스트가 완료되면 THEN the BacktestEngine SHALL MDD를 계산한다
3. WHEN 백테스트가 완료되면 THEN the BacktestEngine SHALL 샤프 비율을 계산한다
4. WHEN 백테스트가 완료되면 THEN the BacktestEngine SHALL 종목별 수익률을 기록한다
5. WHEN 백테스트가 완료되면 THEN the BacktestEngine SHALL 리밸런싱 이력을 기록한다

### Requirement 6

**User Story:** As a 개발자, I want 전략 인터페이스를 확장하도록, so that 기존 코드를 최소한으로 수정할 수 있다

#### Acceptance Criteria

1. WHEN 새로운 메서드를 추가하면 THEN the BaseStrategy SHALL 하위 호환성을 유지한다
2. WHEN 기존 전략을 실행하면 THEN the BacktestEngine SHALL 단일 종목 모드로 동작한다
3. WHEN 포트폴리오 전략을 실행하면 THEN the BacktestEngine SHALL 멀티 종목 모드로 동작한다
4. WHEN 전략이 종목 선택 메서드를 구현하지 않으면 THEN the BacktestEngine SHALL 기본 동작을 수행한다
5. WHEN 전략 타입을 확인하면 THEN the BacktestEngine SHALL 적절한 모드를 선택한다

### Requirement 7

**User Story:** As a 트레이더, I want 데이터 접근을 최적화하도록, so that 백테스트 속도를 향상시킬 수 있다

#### Acceptance Criteria

1. WHEN 여러 종목 데이터를 로드하면 THEN the DataRepository SHALL 배치로 조회한다
2. WHEN 동일한 데이터를 재사용하면 THEN the DataRepository SHALL 캐시에서 반환한다
3. WHEN 메모리가 부족하면 THEN the DataRepository SHALL 오래된 캐시를 제거한다
4. WHEN 데이터가 없으면 THEN the DataRepository SHALL 빈 결과를 반환한다
5. WHEN 데이터 로드에 실패하면 THEN the DataRepository SHALL 에러를 기록하고 계속 진행한다

### Requirement 8

**User Story:** As a 트레이더, I want 실시간 트레이딩과 동일한 구조로, so that 백테스트 결과를 실전에 적용할 수 있다

#### Acceptance Criteria

1. WHEN 백테스트 전략을 작성하면 THEN the Strategy SHALL 실시간 트레이딩에서도 동작한다
2. WHEN 종목 선택 로직을 구현하면 THEN the Strategy SHALL 백테스트와 실전에서 동일하게 동작한다
3. WHEN 매매 신호를 생성하면 THEN the Strategy SHALL 브로커 API와 독립적으로 동작한다
4. WHEN 포지션을 관리하면 THEN the PositionManager SHALL 백테스트와 실전에서 동일한 인터페이스를 제공한다
5. WHEN 계좌 정보를 조회하면 THEN the Account SHALL 백테스트와 실전에서 동일한 형식을 반환한다
