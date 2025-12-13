# LS증권 개인화 HTS - 프로젝트 구조

## 📁 디렉토리 구조

```
Si-WebTrading/
├── 📂 api/                     # FastAPI 백엔드 서버
├── 📂 broker/                  # 증권사 Adapter Layer
├── 📂 core/                    # 핵심 비즈니스 로직
├── 📂 data/                    # 데이터 저장소
├── 📂 frontend/                # React 프론트엔드
├── 📂 tests/                   # 테스트 코드
│   ├── 📂 integration/         # 통합 테스트
│   └── 📂 debug/              # 디버그 테스트
├── 📂 scripts/                 # 유틸리티 스크립트
│   └── 📂 maintenance/        # 유지보수 스크립트
├── 📂 utils/                   # 공통 유틸리티
├── 📂 docs/                    # 문서
├── 📂 examples/               # 예제 코드
└── 📂 deploy/                 # 배포 설정
```

## 🏗️ 아키텍처 원칙

### 1. 모듈 분리 (Separation of Concerns)
- **broker/**: 증권사 API Adapter (LS, Kiwoom, 한국투자 등)
- **core/**: 전략, 백테스트, 리얼트레이딩 엔진
- **api/**: REST API 서버
- **frontend/**: 웹 UI

### 2. 느슨한 결합 (Loose Coupling)
- BrokerBase 추상 클래스 기반 Adapter 패턴
- 의존성 역전 원칙 (DIP) 적용
- 인터페이스 분리 원칙 (ISP) 준수

### 3. 확장 가능한 구조
- 플러그인 형태의 증권사 Adapter
- 전략 자동탐색 (AutoML) 워크플로우
- 모듈별 독립적 배포 가능

## 🧪 테스트 구조

### tests/integration/
- 시스템 전체 통합 테스트
- API 엔드포인트 테스트
- 백테스트 엔진 테스트
- UI 기능 테스트

### tests/debug/
- 개발 중 디버깅용 테스트
- 성능 테스트
- 데이터 검증 테스트

## 🔧 스크립트 구조

### scripts/maintenance/
- 데이터베이스 마이그레이션
- 데이터 정리/수정
- 시스템 점검
- 전략 등록/수정

### scripts/
- 데이터 수집
- 백테스트 실행
- 시스템 초기화
- 개발 도구

## 🚀 실행 방법

### 개발 환경
```bash
# 백엔드 서버
python -m uvicorn api.main:app --reload

# 프론트엔드
cd frontend && npm run dev

# 데이터베이스
./start_postgres.ps1
```

### 테스트 실행
```bash
# 전체 테스트
pytest tests/

# 통합 테스트만
pytest tests/integration/

# 특정 테스트
pytest tests/integration/test_backtest_api.py
```

## 📋 주요 특징

1. **국내주식 중심**: 코스피/코스닥 전용 최적화
2. **멀티 브로커**: LS증권 기본, Kiwoom/한국투자 플러그인
3. **낮은 MDD**: 리스크 관리 중심 전략 개발
4. **AutoML**: 전략 자동탐색 및 최적화
5. **실시간**: 백테스트 + 실거래 통합 환경

## 🔒 보안 원칙

- 전략 코드에 API 연결 코드 분리
- 토큰 기반 인증 (JWT)
- 세션 관리 및 타임아웃
- 민감 정보 암호화 저장