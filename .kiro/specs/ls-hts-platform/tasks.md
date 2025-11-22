# 구현 계획

## 참고 프로젝트

이 프로젝트는 아래 ProgramGarden 오픈소스의 **구조(철학)만 참고**하며, 코드는 절대 복사하지 않습니다.

- **백엔드 참고**: `C:\Users\USER\Si-WebTrading\refer\programgarden-main`
  - 계층 분리 철학, Adapter 패턴 구조 참고
  - 코드 직접 복사 금지

- **VIEW 참고**: `C:\Users\USER\Si-WebTrading\refer\programgarden_dashboard-main`
  - 대시보드 UI 구조 참고
  - 코드 직접 복사 금지

---

## 5단계 개발 계획 개요

### Phase 1: LS Adapter 구현 (브로커 계층)
- BrokerBase 추상 클래스 + LSAdapter 완전 구현
- 데이터 수집 및 캐싱 계층
- 기본 타입 정의 및 유틸리티

### Phase 2: 백테스트 엔진 구현 (코어 계층)
- BaseStrategy 추상 클래스
- BacktestEngine (OHLC 루프 기반)
- 포지션 관리 및 메트릭 계산
- 데이터베이스 연동

### Phase 3: 전략 자동탐색 (AutoML)
- Grid Search / Random Search / Genetic Algorithm
- 멀티프로세싱 백테스트
- 결과 저장 및 최적 전략 선택

### Phase 4: 실시간 자동매매 엔진
- ExecutionEngine (WebSocket 기반)
- RiskManager (MDD, 포지션 크기 관리)
- 실시간 주문 실행 및 체결 처리

### Phase 5: FastAPI 모니터링 서버
- REST API (계좌, 전략, 백테스트, 주문)
- WebSocket API (실시간 시세)
- JWT 인증 및 Redis 캐싱

---

## Phase 1: LS Adapter 구현 (브로커 계층)

**목표**: LS증권 API를 BrokerBase 인터페이스로 추상화하고, 데이터 수집 및 캐싱 기능 구현

### 1.1 프로젝트 구조 및 기본 설정

- [x] 1.1.1 프로젝트 디렉토리 구조 생성
  - `broker/`, `core/`, `data/`, `api/`, `utils/`, `tests/` 폴더 생성
  - _요구사항: 10.4_

- [x] 1.1.2 Python 환경 설정
  - `pyproject.toml` 작성 (Python 3.10+, 의존성 관리)
  - 필수 패키지: `httpx`, `websockets`, `pydantic`, `redis`, `sqlalchemy`, `pytest`, `hypothesis`
  - _요구사항: 10.1_

- [x] 1.1.3 타입 정의 모듈 작성
  - `utils/types.py`: OHLC, Order, Position, Account, OrderSignal, OrderSide, OrderType 등
  - 모든 타입에 타입 힌트 및 docstring 추가
  - _요구사항: 10.2_

- [x] 1.1.4 유틸리티 모듈 작성
  - `utils/logger.py`: 구조화된 로깅 설정
  - `utils/config.py`: YAML 기반 설정 관리
  - `utils/exceptions.py`: 커스텀 예외 클래스 (BrokerError, AuthenticationError 등)
  - _요구사항: 10.1_

### 1.2 BrokerBase 추상 클래스 구현

- [x] 1.2.1 BrokerBase 인터페이스 정의
  - `broker/base.py`: 추상 메서드 정의
    - `get_ohlc()`, `get_current_price()`, `place_order()`, `cancel_order()`, `amend_order()`
    - `get_account()`, `get_positions()`, `get_open_orders()`, `stream_realtime()`
  - 모든 메서드에 타입 힌트 및 docstring 추가
  - _요구사항: 1.1, 1.2, 10.2_

- [x] 1.2.2 Mock 브로커 구현
  - `broker/mock/adapter.py`: 테스트용 MockBroker 클래스
  - 고정된 OHLC 데이터 반환
  - 주문 시뮬레이션 (메모리 기반)
  - _요구사항: 1.2_

- [ ] 1.2.3 속성 테스트: 브로커 어댑터 상호 교환성
  - `tests/test_broker_interchangeability.py`
  - **속성 1: 브로커 어댑터 상호 교환성**
  - **검증 대상: 요구사항 1.3**

### 1.3 LSAdapter 구현

- [x] 1.3.1 LS증권 API 클라이언트 기본 구조
  - `broker/ls/client.py`: httpx 기반 비동기 HTTP 클라이언트
  - OAuth 2.0 인증 로직 (토큰 발급/갱신/폐기)
  - 에러 처리 및 재시도 로직
  - _요구사항: 1.2, 1.5_
  - **완료일: 2025-11-21**

- [x] 1.3.2 OAuth 2.0 인증 구현
  - `broker/ls/oauth.py`: LSOAuth 클래스
  - 토큰 발급/갱신/폐기 API
  - 파일 기반 토큰 영속성 (LSTokenManager)
  - _요구사항: 1.2, 1.5_
  - **완료일: 2025-11-21**

- [x] 1.3.3 계좌 정보 조회 구현
  - `broker/ls/services/account.py`: 계좌 잔고, 보유종목 조회
  - `broker/ls/models/account.py`: LSAccount, LSPosition 모델
  - TR ID: t0424 (주식잔고2)
  - _요구사항: 1.2_
  - **완료일: 2025-11-21**

- [x] 1.3.4 주문 관련 기능 구현
  - `broker/ls/services/order.py`: 신규 주문, 정정, 취소
  - `broker/ls/models/order.py`: LSOrder 모델
  - TR ID: CSPAT00601 (주문), CSPAT00701 (정정), CSPAT00801 (취소)
  - _요구사항: 1.2_
  - **완료일: 2025-11-21**

- [ ] 1.3.5 시세 조회 구현 (구조만 완성, 실제 테스트 필요)
  - `broker/ls/services/market.py`: 현재가, 호가, OHLC 조회
  - `broker/ls/models/market.py`: LSQuote, LSOrderbook, LSOHLC 모델
  - TR ID: t1102 (현재가), t1101 (호가), t8410 (일봉), t8412 (분봉)
  - _요구사항: 1.2_
  - **상태: 구조 완성, 실제 API 호출 미검증**
  - **TODO:**
    - [ ] 메서드 이름 통일 (get_ohlc_daily → get_daily_ohlc)
    - [ ] LSAdapter에서 호출하는 메서드명 수정
    - [ ] to_ohlc() 타입 변환 메서드 구현
    - [ ] 실제 API 호출 테스트 및 TR ID 검증
    - [ ] 요청/응답 구조 검증
    - [ ] 에러 처리 강화

- [ ] 1.3.6 종목 검색 구현
  - `broker/ls/services/market.py`: search_symbol() 메서드
  - TR ID: t8436 (주식종목조회) 예상
  - _요구사항: 1.2_
  - **상태: 미구현 (TODO)**

- [ ] 1.3.7 WebSocket 실시간 데이터 구현
  - `broker/ls/realtime.py`: 실시간 체결, 호가 스트리밍
  - AsyncIterator 패턴 사용
  - _요구사항: 1.2, 5.1_
  - **상태: 미구현**

- [x] 1.3.8 LSAdapter 통합
  - `broker/ls/adapter.py`: BrokerBase를 상속하여 모든 메서드 구현
  - 계좌/주문/시세 서비스 통합
  - _요구사항: 1.2, 1.5_
  - **완료일: 2025-11-21**
  - **주의: 시세 조회 메서드 이름 불일치 문제 있음**

### 1.4 데이터 계층 구현

- [ ] 1.4.1 Redis 캐시 구현
  - `data/cache.py`: RedisCache 클래스
  - OHLC 데이터 캐싱 (키 생성, TTL 관리)
  - 실시간 가격 캐싱
  - _요구사항: 8.1, 8.2_

- [ ] 1.4.2 파일 저장소 구현
  - `data/storage.py`: FileStorage 클래스
  - OHLC 데이터 직렬화/역직렬화 (Parquet 또는 CSV)
  - 로컬 파일시스템 또는 MinIO 지원
  - _요구사항: 8.3_

- [ ] 1.4.3 데이터 수집기 구현
  - `data/collector.py`: DataCollector 클래스
  - 캐시 우선 검색 로직 (Redis → 파일 → 브로커)
  - 캐시 미스 시 브로커 호출 및 캐시 업데이트
  - _요구사항: 8.1, 8.5_

- [ ] 1.4.4 속성 테스트: 캐시 우선 데이터 검색
  - `tests/test_cache_priority.py`
  - **속성 16: 캐시 우선 데이터 검색**
  - **검증 대상: 요구사항 8.1**

- [ ] 1.4.5 속성 테스트: 실시간 가격 캐시 TTL
  - `tests/test_cache_ttl.py`
  - **속성 17: 실시간 가격 캐시 TTL**
  - **검증 대상: 요구사항 8.2**

- [ ] 1.4.6 속성 테스트: 과거 데이터 저장소 영속성
  - `tests/test_storage_persistence.py`
  - **속성 18: 과거 데이터 저장소 영속성**
  - **검증 대상: 요구사항 8.3**

- [ ] 1.4.7 속성 테스트: 오래된 캐시 새로고침
  - `tests/test_cache_refresh.py`
  - **속성 19: 오래된 캐시 새로고침**
  - **검증 대상: 요구사항 8.5**

### 1.5 Phase 1 체크포인트

- [ ] 1.5.1 통합 테스트 실행
  - LSAdapter로 OHLC 데이터 조회 테스트
  - 캐시 동작 검증
  - Mock 브로커와 LSAdapter 상호 교환성 테스트

- [ ] 1.5.2 문서화
  - Phase 1 README 작성 (설치, 설정, 사용 예제)
  - API 문서 생성

---

## Phase 2: 백테스트 엔진 구현 (코어 계층)

**목표**: OHLC 데이터 기반 백테스트 엔진 구현, 전략 추상화, 포지션 관리 및 성과 메트릭 계산

### 2.1 BaseStrategy 추상 클래스 구현

- [ ] 2.1.1 BaseStrategy 인터페이스 정의
  - `core/strategy/base.py`: 추상 메서드 정의
    - `on_bar()`: 새로운 바마다 호출, 주문 신호 반환
    - `on_fill()`: 주문 체결 시 호출
  - 전략 파라미터 관리 (`self.params`)
  - _요구사항: 3.1, 3.2, 3.5_

- [ ] 2.1.2 예제 전략 구현 (테스트용)
  - `core/strategy/examples/ma_cross.py`: 이동평균 교차 전략
  - 골든크로스/데드크로스 로직
  - _요구사항: 3.1, 3.2_

- [ ] 2.1.3 속성 테스트: 전략 컨텍스트 완전성
  - `tests/test_strategy_context.py`
  - **속성 7: 전략 컨텍스트 완전성**
  - **검증 대상: 요구사항 3.4**

### 2.2 포지션 관리 구현

- [ ] 2.2.1 Position Manager 클래스
  - `core/backtest/position.py`: 포지션 추적 및 관리
  - 진입, 청산, 피라미딩 로직
  - 미실현/실현 손익 계산
  - _요구사항: 2.3_

- [ ] 2.2.2 Trade Log 클래스
  - `core/backtest/trade_log.py`: 거래 내역 기록
  - 진입/청산 시간, 가격, 수량, 손익 저장
  - _요구사항: 2.1_

### 2.3 백테스트 엔진 구현

- [ ] 2.3.1 BacktestEngine 기본 구조
  - `core/backtest/engine.py`: BacktestEngine 클래스
  - OHLC 데이터 시간순 반복 로직
  - 전략 호출 및 주문 신호 처리
  - _요구사항: 2.1_

- [ ] 2.3.2 주문 실행 시뮬레이션
  - 수수료 및 슬리피지 적용
  - 시장가/지정가 주문 처리
  - _요구사항: 2.1_

- [ ] 2.3.3 ATR 트레일링 스탑 구현
  - `core/backtest/indicators.py`: ATR 계산
  - 동적 손절 수준 조정 로직
  - _요구사항: 2.4_

- [ ] 2.3.4 속성 테스트: 시간순 거래 실행
  - `tests/test_chronological_execution.py`
  - **속성 2: 시간순 거래 실행**
  - **검증 대상: 요구사항 2.1**

- [ ] 2.3.5 속성 테스트: 피라미딩 포지션 누적
  - `tests/test_pyramiding.py`
  - **속성 4: 피라미딩 포지션 누적**
  - **검증 대상: 요구사항 2.3**

- [ ] 2.3.6 속성 테스트: ATR 트레일링 스탑 동적 조정
  - `tests/test_atr_trailing.py`
  - **속성 5: ATR 트레일링 스탑 동적 조정**
  - **검증 대상: 요구사항 2.4**

### 2.4 백테스트 메트릭 계산

- [ ] 2.4.1 Metrics 클래스 구현
  - `core/backtest/metrics.py`: 성과 지표 계산
  - MDD, 승률, 손익비, 샤프 비율, 총 수익률
  - 자산 곡선 생성
  - _요구사항: 2.2_

- [ ] 2.4.2 속성 테스트: 백테스트 메트릭 완전성
  - `tests/test_metrics_completeness.py`
  - **속성 3: 백테스트 메트릭 완전성**
  - **검증 대상: 요구사항 2.2**

### 2.5 데이터베이스 연동

- [ ] 2.5.1 데이터베이스 모델 정의
  - `data/models.py`: SQLAlchemy 모델
  - BacktestResult, Trade, StrategyConfig 테이블
  - _요구사항: 8.4_

- [ ] 2.5.2 Repository 패턴 구현
  - `data/repository.py`: 백테스트 결과 저장/조회
  - SQLite (개발) / PostgreSQL (프로덕션) 지원
  - _요구사항: 2.5, 8.4_

- [ ] 2.5.3 속성 테스트: 백테스트 결과 영속성 왕복
  - `tests/test_result_persistence.py`
  - **속성 6: 백테스트 결과 영속성 왕복**
  - **검증 대상: 요구사항 2.5**

### 2.6 Phase 2 체크포인트

- [ ] 2.6.1 통합 테스트 실행
  - 전체 백테스트 워크플로우 테스트
  - 예제 전략으로 백테스트 실행
  - 메트릭 계산 검증

- [ ] 2.6.2 문서화
  - 백테스트 엔진 사용 가이드
  - 전략 작성 가이드

---

## Phase 3: 전략 자동탐색 (AutoML)

**목표**: 파라미터 최적화를 위한 자동 탐색 시스템 구현 (Grid Search, Random Search, Genetic Algorithm)

### 3.1 AutoML 기본 구조

- [ ] 3.1.1 파라미터 공간 정의
  - `core/automl/parameter_space.py`: 파라미터 범위 및 타입 정의
  - 연속형/이산형 파라미터 지원
  - _요구사항: 4.1_

- [ ] 3.1.2 Evaluator 클래스
  - `core/automl/evaluator.py`: 백테스트 실행 및 메트릭 평가
  - 사용자 정의 최적화 메트릭 (Sharpe, MDD, 손익비 등)
  - _요구사항: 4.3_

### 3.2 Grid Search 구현

- [ ] 3.2.1 Grid Search 엔진
  - `core/automl/grid_search.py`: 모든 파라미터 조합 생성
  - 멀티프로세싱으로 병렬 백테스트 실행
  - _요구사항: 4.1, 4.2_

- [ ] 3.2.2 속성 테스트: 파라미터 탐색 완전성
  - `tests/test_grid_search_completeness.py`
  - **속성 8: 파라미터 탐색 완전성**
  - **검증 대상: 요구사항 4.2**

### 3.3 Random Search 구현

- [ ] 3.3.1 Random Search 엔진
  - `core/automl/random_search.py`: 랜덤 파라미터 샘플링
  - 지정된 반복 횟수만큼 백테스트
  - _요구사항: 4.1_

### 3.4 Genetic Algorithm 구현

- [ ] 3.4.1 Genetic Algorithm 엔진
  - `core/automl/genetic.py`: 유전 알고리즘 구현
  - 초기 모집단 생성
  - 선택, 교차, 돌연변이 연산
  - 적합도 평가 (백테스트 메트릭)
  - _요구사항: 4.1_

### 3.5 결과 관리 및 저장

- [ ] 3.5.1 결과 순위화
  - `core/automl/ranker.py`: 사용자 정의 메트릭으로 정렬
  - 상위 N개 전략 선택
  - _요구사항: 4.3_

- [ ] 3.5.2 파라미터 저장
  - 최적 전략 파라미터를 JSON으로 저장
  - 데이터베이스에 최적화 결과 저장
  - _요구사항: 4.4_

- [ ] 3.5.3 속성 테스트: 최적화 결과 순위화
  - `tests/test_optimization_ranking.py`
  - **속성 9: 최적화 결과 순위화**
  - **검증 대상: 요구사항 4.3**

- [ ] 3.5.4 속성 테스트: 파라미터 영속성 왕복
  - `tests/test_parameter_persistence.py`
  - **속성 10: 파라미터 영속성 왕복**
  - **검증 대상: 요구사항 4.4**

### 3.6 과적합 방지

- [ ] 3.6.1 훈련-테스트 분할
  - `core/automl/validation.py`: 데이터 분할 로직
  - 훈련 기간과 테스트 기간 분리
  - _요구사항: 4.5_

- [ ] 3.6.2 워크포워드 검증
  - 롤링 윈도우 방식 검증
  - _요구사항: 4.5_

### 3.7 AutoML Manager 통합

- [ ] 3.7.1 AutoMLEngine 클래스
  - `core/automl/engine.py`: 모든 탐색 방법 통합
  - 탐색 방법 선택 인터페이스
  - 진행 상황 추적 및 로깅
  - _요구사항: 4.1, 4.2_

### 3.8 Phase 3 체크포인트

- [ ] 3.8.1 통합 테스트 실행
  - Grid Search로 파라미터 최적화 테스트
  - Random Search 및 Genetic Algorithm 테스트
  - 결과 저장 및 조회 검증

- [ ] 3.8.2 문서화
  - AutoML 사용 가이드
  - 파라미터 공간 정의 가이드

---

## Phase 4: 실시간 자동매매 엔진

**목표**: WebSocket 기반 실시간 데이터 수신 및 전략 실행, 리스크 관리 시스템 구현

### 4.1 RiskManager 구현

- [ ] 4.1.1 RiskManager 클래스 기본 구조
  - `core/risk/manager.py`: 리스크 관리 클래스
  - MDD 계산 및 추적
  - 포지션 크기 검증
  - 일일 손실 한도 검증
  - _요구사항: 9.1, 9.2, 9.3, 9.4_

- [ ] 4.1.2 MDD 계산 로직
  - 자산 곡선 기반 실시간 MDD 계산
  - 고점 추적 및 낙폭 계산
  - _요구사항: 9.4_

- [ ] 4.1.3 긴급 정지 메커니즘
  - MDD 임계값 초과 시 전략 중단
  - 모든 포지션 청산 로직
  - _요구사항: 9.2, 5.5_

- [ ] 4.1.4 손절/익절 관리
  - 포지션 개설 시 손절/익절 주문 자동 생성
  - _요구사항: 9.5_

- [ ] 4.1.5 속성 테스트: 포지션 크기 한도 강제
  - `tests/test_position_size_limit.py`
  - **속성 20: 포지션 크기 한도 강제**
  - **검증 대상: 요구사항 9.1**

- [ ] 4.1.6 속성 테스트: MDD 임계값 긴급 트리거
  - `tests/test_mdd_emergency.py`
  - **속성 21: MDD 임계값 긴급 트리거**
  - **검증 대상: 요구사항 9.2**

- [ ] 4.1.7 속성 테스트: 일일 손실 한도 주문 방지
  - `tests/test_daily_loss_limit.py`
  - **속성 22: 일일 손실 한도 주문 방지**
  - **검증 대상: 요구사항 9.3**

- [ ] 4.1.8 속성 테스트: MDD 계산 정확성
  - `tests/test_mdd_calculation.py`
  - **속성 23: MDD 계산 정확성**
  - **검증 대상: 요구사항 9.4**

- [ ] 4.1.9 속성 테스트: 손절 및 익절 강제
  - `tests/test_stop_loss_take_profit.py`
  - **속성 24: 손절 및 익절 강제**
  - **검증 대상: 요구사항 9.5**

### 4.2 ExecutionEngine 구현

- [ ] 4.2.1 ExecutionEngine 기본 구조
  - `core/execution/engine.py`: 실행 엔진 클래스
  - WebSocket 연결 관리
  - 전략 인스턴스 관리
  - _요구사항: 5.1_

- [ ] 4.2.2 실시간 가격 업데이트 처리
  - 브로커로부터 WebSocket 데이터 수신
  - 전략 on_bar 메서드 호출
  - _요구사항: 5.2_

- [ ] 4.2.3 주문 검증 및 제출
  - RiskManager를 통한 주문 검증
  - 브로커 어댑터를 통한 주문 제출
  - 주문 실패 시 에러 처리
  - _요구사항: 5.3_

- [ ] 4.2.4 체결 이벤트 처리
  - 체결 알림 수신
  - 포지션 및 계좌 상태 업데이트
  - 전략 on_fill 콜백 호출
  - _요구사항: 5.4_

- [ ] 4.2.5 엔진 시작/중단 로직
  - 전략 시작 및 중단 메서드
  - 긴급 정지 처리
  - _요구사항: 5.5_

- [ ] 4.2.6 속성 테스트: 가격 업데이트 전략 호출
  - `tests/test_price_update_strategy_call.py`
  - **속성 11: 가격 업데이트 전략 호출**
  - **검증 대상: 요구사항 5.2**

- [ ] 4.2.7 속성 테스트: 리스크 한도 주문 거부
  - `tests/test_risk_limit_rejection.py`
  - **속성 12: 리스크 한도 주문 거부**
  - **검증 대상: 요구사항 5.3**

- [ ] 4.2.8 속성 테스트: 체결 이벤트 상태 동기화
  - `tests/test_fill_event_sync.py`
  - **속성 13: 체결 이벤트 상태 동기화**
  - **검증 대상: 요구사항 5.4**

- [ ] 4.2.9 속성 테스트: MDD 긴급 정지
  - `tests/test_mdd_emergency_stop.py`
  - **속성 14: MDD 긴급 정지**
  - **검증 대상: 요구사항 5.5**

### 4.3 전략 상태 관리

- [ ] 4.3.1 StrategyManager 클래스
  - `core/execution/strategy_manager.py`: 여러 전략 동시 실행 관리
  - 전략 시작/중단/재시작
  - 전략별 성과 추적
  - _요구사항: 5.1_

### 4.4 Phase 4 체크포인트

- [ ] 4.4.1 통합 테스트 실행
  - Mock 브로커로 실시간 거래 시뮬레이션
  - 리스크 한도 검증 테스트
  - 긴급 정지 시나리오 테스트

- [ ] 4.4.2 문서화
  - 실행 엔진 사용 가이드
  - 리스크 관리 설정 가이드

---

## Phase 5: FastAPI 모니터링 서버

**목표**: REST API 및 WebSocket 기반 모니터링 서버 구현, JWT 인증, Redis 캐싱

### 5.1 FastAPI 애플리케이션 설정

- [ ] 5.1.1 FastAPI 앱 초기화
  - `api/main.py`: FastAPI 앱 생성
  - CORS 설정
  - 미들웨어 설정 (로깅, 에러 처리)
  - _요구사항: 6.1_

- [ ] 5.1.2 에러 핸들러
  - `api/exceptions.py`: 전역 예외 처리
  - 표준화된 에러 응답 포맷
  - _요구사항: 6.1_

- [ ] 5.1.3 Pydantic 모델 정의
  - `api/schemas.py`: 요청/응답 스키마
  - AccountResponse, PositionResponse, OrderRequest 등
  - _요구사항: 6.1_

### 5.2 인증 및 보안

- [ ] 5.2.1 JWT 인증 구현
  - `api/auth.py`: JWT 토큰 생성 및 검증
  - 로그인 엔드포인트
  - _요구사항: 6.1_

- [ ] 5.2.2 권한 관리
  - 역할 기반 접근 제어 (RBAC)
  - 인증 데코레이터
  - _요구사항: 6.1_

### 5.3 계좌 및 포지션 API

- [ ] 5.3.1 계좌 라우터
  - `api/routes/account.py`
  - GET `/api/account/summary` - 계좌 요약 정보
  - GET `/api/account/balance` - 잔액 조회
  - _요구사항: 6.1_

- [ ] 5.3.2 포지션 라우터
  - `api/routes/positions.py`
  - GET `/api/positions` - 보유 포지션 목록
  - GET `/api/positions/{symbol}` - 특정 종목 포지션
  - _요구사항: 6.1_

- [ ] 5.3.3 주문 라우터
  - `api/routes/orders.py`
  - GET `/api/orders` - 미체결 주문 목록
  - POST `/api/orders` - 수동 주문 제출
  - DELETE `/api/orders/{order_id}` - 주문 취소
  - _요구사항: 6.4_

- [ ] 5.3.4 속성 테스트: 수동 주문 브로커 위임
  - `tests/test_manual_order_delegation.py`
  - **속성 15: 수동 주문 브로커 위임**
  - **검증 대상: 요구사항 6.4**

### 5.4 전략 관리 API

- [ ] 5.4.1 전략 라우터
  - `api/routes/strategy.py`
  - GET `/api/strategy/list` - 활성 전략 목록
  - POST `/api/strategy/start` - 전략 시작
  - POST `/api/strategy/stop` - 전략 중단
  - GET `/api/strategy/{id}/logs` - 전략 로그 조회
  - _요구사항: 6.2_

### 5.5 백테스트 API

- [ ] 5.5.1 백테스트 라우터
  - `api/routes/backtest.py`
  - POST `/api/backtest/run` - 백테스트 실행 요청
  - GET `/api/backtest/{id}` - 백테스트 결과 조회
  - GET `/api/backtest` - 백테스트 목록 조회
  - _요구사항: 6.3_

- [ ] 5.5.2 비동기 백테스트 실행
  - Celery 또는 백그라운드 태스크로 백테스트 실행
  - 진행 상황 추적
  - _요구사항: 6.3_

### 5.6 AutoML API

- [ ] 5.6.1 AutoML 라우터
  - `api/routes/automl.py`
  - POST `/api/automl/run` - 파라미터 최적화 실행
  - GET `/api/automl/{id}` - 최적화 결과 조회
  - GET `/api/automl/{id}/top` - 상위 N개 전략 조회
  - _요구사항: 4.3_

### 5.7 실시간 데이터 API

- [ ] 5.7.1 실시간 가격 라우터
  - `api/routes/price.py`
  - GET `/api/price/{symbol}` - 현재가 조회
  - _요구사항: 6.5_

- [ ] 5.7.2 WebSocket 엔드포인트
  - `api/websocket.py`
  - `/ws/realtime` - 실시간 가격 스트리밍
  - `/ws/strategy/{id}` - 전략 상태 실시간 업데이트
  - 클라이언트 연결 관리
  - _요구사항: 6.5_

### 5.8 Redis 캐싱 통합

- [ ] 5.8.1 API 응답 캐싱
  - `api/cache.py`: Redis 기반 응답 캐싱
  - 계좌 정보, 포지션, 가격 데이터 캐싱
  - TTL 관리
  - _요구사항: 8.2_

### 5.9 Service 및 Repository 패턴

- [ ] 5.9.1 Service 계층
  - `api/services/`: 비즈니스 로직 분리
  - AccountService, StrategyService, BacktestService
  - _요구사항: 6.1_

- [ ] 5.9.2 Repository 계층
  - `api/repositories/`: 데이터 접근 계층
  - 데이터베이스 쿼리 추상화
  - _요구사항: 6.1_

### 5.10 Phase 5 체크포인트

- [ ] 5.10.1 통합 테스트 실행
  - 모든 API 엔드포인트 테스트
  - WebSocket 연결 테스트
  - 인증 및 권한 테스트

- [ ] 5.10.2 API 문서화
  - Swagger/OpenAPI 자동 생성
  - 엔드포인트 사용 예제

- [ ] 5.10.3 성능 테스트
  - API 응답 시간 측정
  - 동시 요청 처리 테스트

---

## 추가 작업 (선택적)

### 추가 브로커 어댑터 구현

- [ ] A.1 KiwoomAdapter 구현
  - `broker/kiwoom/adapter.py`: 키움증권 OpenAPI 연동
  - 모든 BrokerBase 메서드 구현
  - _요구사항: 1.2, 1.5_

- [ ] A.2 KoreaInvestmentAdapter 구현
  - `broker/korea_invest/adapter.py`: 한국투자증권 API 연동
  - 모든 BrokerBase 메서드 구현
  - _요구사항: 1.2, 1.5_

### 대시보드 UI (React/Next.js)

- [ ] B.1 프론트엔드 프로젝트 설정
  - React 또는 Next.js 프로젝트 생성
  - API 클라이언트 설정

- [ ] B.2 계좌 대시보드
  - 계좌 요약, 포지션, 주문 현황 표시
  - 실시간 업데이트 (WebSocket)

- [ ] B.3 전략 관리 UI
  - 전략 시작/중단 버튼
  - 전략 성과 차트

- [ ] B.4 백테스트 UI
  - 백테스트 실행 폼
  - 결과 차트 및 메트릭 표시

- [ ] B.5 AutoML UI
  - 파라미터 공간 설정
  - 최적화 진행 상황 표시
  - 상위 전략 비교

### 고급 전략 예제

- [ ] C.1 ATR 기반 변동성 돌파 전략
  - `core/strategy/examples/atr_breakout.py`
  - ATR 트레일링 스탑 활용
  - 피라미딩 로직 포함
  - _요구사항: 2.3, 2.4_

- [ ] C.2 볼린저 밴드 평균회귀 전략
  - `core/strategy/examples/bollinger_mean_reversion.py`
  - 과매수/과매도 구간 진입

- [ ] C.3 멀티 타임프레임 전략
  - 여러 시간대 데이터 활용
  - 상위 타임프레임 트렌드 필터링

### 배포 및 인프라

- [ ] D.1 Docker 컨테이너화
  - Dockerfile 작성 (API 서버, 백테스트 워커)
  - docker-compose.yml (전체 스택)

- [ ] D.2 CI/CD 파이프라인
  - GitHub Actions 또는 GitLab CI
  - 자동 테스트 및 배포

- [ ] D.3 모니터링 및 로깅
  - Prometheus + Grafana 설정
  - 구조화된 로깅 (JSON)

- [ ] D.4 알림 시스템
  - 리스크 한도 초과 시 알림
  - 시스템 에러 알림
  - Slack/Discord/Email 통합

---

## 최종 체크리스트

### 코드 품질

- [ ] 모든 함수/메서드에 타입 힌트 추가
- [ ] 모든 공개 API에 docstring 작성
- [ ] mypy 타입 체크 통과
- [ ] black + isort 코드 포맷팅 적용
- [ ] ruff 린팅 통과

### 테스트

- [ ] 단위 테스트 커버리지 > 80%
- [ ] 모든 속성 테스트 통과 (Hypothesis)
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 통과

### 문서화

- [ ] README.md 작성 (프로젝트 개요, 설치, 사용법)
- [ ] API 문서 생성 (Swagger/OpenAPI)
- [ ] 아키텍처 다이어그램 업데이트
- [ ] 전략 작성 가이드
- [ ] 배포 가이드

### 보안

- [ ] API 키 환경변수로 관리
- [ ] JWT 인증 구현
- [ ] HTTPS 설정 (프로덕션)
- [ ] Rate limiting 적용
- [ ] SQL Injection 방지 (ORM 사용)

---

## 개발 순서 요약

1. **Phase 1 (2-3주)**: 브로커 계층 + 데이터 계층 → LSAdapter 완성
2. **Phase 2 (2-3주)**: 백테스트 엔진 → 전략 실행 및 메트릭 계산
3. **Phase 3 (1-2주)**: AutoML → 파라미터 최적화
4. **Phase 4 (2-3주)**: 실시간 엔진 + 리스크 관리 → 실전 매매 준비
5. **Phase 5 (2-3주)**: FastAPI 서버 → 모니터링 및 제어 인터페이스

**총 예상 기간**: 9-14주 (약 2-3개월)

---

## 참고사항

- 각 Phase 완료 후 체크포인트에서 사용자 확인 필요
- 테스트 주도 개발(TDD) 권장
- 속성 테스트는 각 기능 구현 직후 작성
- ProgramGarden 코드는 절대 복사하지 않고 구조만 참고
- 모든 코드는 새로 작성하며 국내주식 HTS에 최적화

