# LS HTS 플랫폼 프론트엔드

React + TypeScript + Vite 기반 HTS 대시보드

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Zustand** - 상태 관리
- **Axios** - HTTP 클라이언트
- **React Router** - 라우팅
- **TradingView Lightweight Charts** - 차트 라이브러리
- **WebSocket** - 실시간 통신

## 프로젝트 구조

```
src/
├── app/                    # 앱 전역 레이어
│   ├── store/             # Zustand 전역 상태
│   ├── router/            # React Router
│   └── providers/         # Context Providers
├── modules/               # 도메인 모듈
│   ├── chart/            # 차트 모듈
│   ├── trading/          # 트레이딩 모듈
│   └── account/          # 계좌 모듈
├── services/             # 네트워크 레이어
│   ├── http.ts          # Axios 인스턴스
│   ├── websocket.ts     # WebSocket 클라이언트
│   └── endpoints.ts     # API 엔드포인트
├── hooks/                # 재사용 훅
├── utils/                # 유틸리티 함수
├── constants/            # 상수
├── types/                # 타입 정의
└── pages/                # 페이지 컴포넌트
```

## 설치 및 실행

```bash
# 의존성 설치
npm install --legacy-peer-deps

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 프리뷰
npm run preview
```

## 환경 변수

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 주요 기능

### 1. 실시간 차트
- TradingView Lightweight Charts 사용
- 캔들스틱 차트
- 다양한 시간 간격 (1분, 5분, 15분, 30분, 1시간, 1일)
- WebSocket 실시간 업데이트

### 2. 주문 관리
- 시장가/지정가 주문
- 매수/매도
- 주문 내역 조회
- 주문 취소

### 3. 계좌 정보
- 예수금, 총 자산, 증거금 조회
- 실시간 업데이트

### 4. 인증
- JWT 기반 인증
- 자동 토큰 갱신
- Protected Routes

## 개발 가이드

### 새 모듈 추가

1. `src/modules/` 아래에 모듈 폴더 생성
2. `components/`, `hooks/`, `services/` 구조로 구성
3. 필요시 `app/store/`에 상태 추가

### API 호출

```typescript
import { httpClient } from '@/services/http';
import { ENDPOINTS } from '@/services/endpoints';

const response = await httpClient.get(ENDPOINTS.PRICE.CURRENT('005930'));
```

### WebSocket 사용

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

const { subscribe, unsubscribe, sendMessage } = useWebSocket();

subscribe('price:005930', (message) => {
  console.log(message);
});
```

### 상태 관리

```typescript
import { useChartStore } from '@/app/store/chartStore';

const { symbol, setSymbol } = useChartStore();
```

## 빌드 및 배포

```bash
# 프로덕션 빌드
npm run build

# dist/ 폴더가 생성됨
# Nginx, Apache 등으로 서빙
```

## 라이센스

MIT
