# HTS
국내주식 자동매매 시스템 - React + FastAPI

## 빠른 시작

### Windows

**방법 1: PowerShell 스크립트**
```powershell
.\start.ps1
```

**방법 2: CMD 배치 파일**
```cmd
start.bat
```

**방법 3: npm (concurrently 설치 필요)**
```bash
npm install
npm start
```

### 수동 실행

**터미널 1 - 백엔드**
```bash
uvicorn api.main:app --reload
```

**터미널 2 - 프론트엔드**
```bash
cd frontend
npm run dev
```

## 접속

### 로컬 개발 (같은 PC)
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 다른 PC에서 접근 (로컬 네트워크)

**1. 서버 PC의 IP 주소 확인**
```bash
# Windows
ipconfig

# 예시 출력: IPv4 주소 . . . . . . . . : 192.168.0.100
```

**2. 방화벽 설정 (Windows)**
- 제어판 → Windows Defender 방화벽 → 고급 설정
- 인바운드 규칙 → 새 규칙
- 포트: 3000, 8000 허용

**3. 접속 (환경변수 설정 불필요!)**
- **프론트엔드**: http://192.168.0.100:3000
- **백엔드 API**: http://192.168.0.100:8000

> 💡 **상대주소 사용**: 프론트엔드가 자동으로 현재 호스트의 백엔드에 연결됩니다.

### Tailscale 외부 접근 (자동 감지!)

**설정 불필요!** 자동으로 현재 호스트를 감지합니다.

**1. Tailscale IP 확인**
```bash
tailscale ip -4
# 예: 100.x.x.x
```

**2. 외부에서 접속**
- **프론트엔드**: http://100.x.x.x:3000

> 💡 **자동 감지 방식**:
> - `localhost` 접속 → Vite 프록시 사용 (상대주소)
> - Tailscale IP 접속 → 자동으로 `100.x.x.x:8000` 연결
> - 환경변수 설정이나 재기동 불필요!

**강제 지정이 필요한 경우만:**
```bash
# frontend/.env.local 파일 수정
VITE_API_URL=http://100.x.x.x:8000
VITE_WS_URL=ws://100.x.x.x:8000
```

## 로그인

- **사용자명**: `testuser`
- **비밀번호**: `testpass`

## 주요 기능

- ✅ TradingView Lightweight Charts
- ✅ 실시간 WebSocket 가격 스트리밍
- ✅ 주문 관리 (매수/매도)
- ✅ 계좌 정보
- ✅ 종목 변경 (005930, 000660)
- ✅ 시간 간격 변경 (1분~1일)

## 기술 스택

### 백엔드
- Python 3.11+
- FastAPI
- SQLAlchemy
- WebSocket
- JWT 인증

### 프론트엔드
- React 18
- TypeScript
- Vite
- Zustand (상태 관리)
- TradingView Lightweight Charts
- Axios

## 프로젝트 구조

```
Si-WebTrading/
├── api/                    # FastAPI 백엔드
│   ├── routes/            # API 라우트
│   ├── auth/              # 인증
│   └── websocket/         # WebSocket
├── broker/                # 브로커 어댑터
│   ├── base.py           # 추상 클래스
│   ├── ls/               # LS증권 어댑터
│   └── mock/             # Mock 브로커
├── core/                  # 핵심 로직
│   ├── strategy/         # 전략
│   ├── backtest/         # 백테스트
│   └── execution/        # 실행 엔진
├── data/                  # 데이터 저장소
├── frontend/              # React 프론트엔드
│   └── src/
│       ├── app/          # 전역 상태/라우터
│       ├── modules/      # 도메인 모듈
│       ├── services/     # API/WebSocket
│       └── pages/        # 페이지
├── scripts/               # 유틸리티 스크립트
├── start.ps1             # 시작 스크립트 (PowerShell)
└── start.bat             # 시작 스크립트 (CMD)
```

## 개발 가이드

### 테스트 사용자 생성
```bash
npm run create-user
```

### 테스트 데이터 생성
```bash
npm run create-data
```

### 백엔드 테스트
```bash
pytest tests/
```

### 프론트엔드 빌드
```bash
cd frontend
npm run build
```

## 환경 변수

### 백엔드 (config.yaml)
```yaml
server:
  host: "0.0.0.0"
  port: 8000

database:
  type: "sqlite"
  path: "data/hts.db"

storage:
  path: "data/ohlc"
```

### 프론트엔드 (frontend/.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 문서

- [프론트엔드 빠른 시작](docs/frontend_quickstart.md)
- [프론트엔드 아키텍처](docs/frontend_architecture.md)
- [LS증권 페이퍼 트레이딩](docs/ls_paper_trading.md)

## 라이센스

MIT
