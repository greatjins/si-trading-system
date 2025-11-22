# 프론트엔드 아키텍처

## 개요

LS HTS 플랫폼의 프론트엔드는 React + TypeScript + Vite 기반으로 구축되었으며, 모듈화된 구조로 설계되었습니다.

## 기술 스택

| 기술 | 용도 | 선택 이유 |
|------|------|-----------|
| React 18 | UI 라이브러리 | 컴포넌트 기반, 풍부한 생태계 |
| TypeScript | 타입 시스템 | 타입 안전성, 개발 생산성 |
| Vite | 빌드 도구 | 빠른 HMR, 최적화된 빌드 |
| Zustand | 상태 관리 | 간단한 API, 보일러플레이트 최소화 |
| Axios | HTTP 클라이언트 | 인터셉터, 자동 재시도 |
| React Router | 라우팅 | SPA 라우팅 표준 |
| TradingView Lightweight Charts | 차트 | 무료, 고성능, 실시간 지원 |

## 프로젝트 구조

```
frontend/
├── src/
│   ├── app/                         # 앱 전역 레이어
│   │   ├── store/                   # Zustand 전역 상태
│   │   │   ├── accountStore.ts      # 계좌 상태
│   │   │   ├── orderStore.ts        # 주문 상태
│   │   │   └── chartStore.ts        # 차트 상태
│   │   ├── router/                  # React Router
│   │   │   └── index.tsx            # 라우트 정의
│   │   └── providers/               # Context Providers
│   │       └── AppProvider.tsx      # 앱 루트 Provider
│   │
│   ├── modules/                     # 도메인 모듈화
│   │   ├── chart/                   # 차트 모듈
│   │   │   ├── components/
│   │   │   │   ├── CandlestickChart.tsx
│   │   │   │   └── ChartControls.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useChart.ts
│   │   │   └── services/
│   │   │       └── chartApi.ts
│   │   ├── trading/                 # 트레이딩 모듈
│   │   │   ├── components/
│   │   │   │   ├── OrderPanel.tsx
│   │   │   │   └── OrderHistory.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useOrder.ts
│   │   │   └── services/
│   │   │       └── orderApi.ts
│   │   └── account/                 # 계좌 모듈
│   │       ├── components/
│   │       │   └── AccountInfo.tsx
│   │       └── services/
│   │           └── accountApi.ts
│   │
│   ├── services/                    # 글로벌 네트워크 레이어
│   │   ├── http.ts                  # Axios 인스턴스
│   │   ├── websocket.ts             # WebSocket 클라이언트
│   │   └── endpoints.ts             # API URL 정리
│   │
│   ├── hooks/                       # 재사용 훅 (도메인 X)
│   │   └── useWebSocket.ts
│   │
│   ├── constants/                   # 공용 상수
│   │   ├── ws-events.ts
│   │   ├── order-types.ts
│   │   └── chart-constants.ts
│   │
│   ├── utils/                       # 유틸리티 함수
│   │   ├── formatters.ts
│   │   └── time.ts
│   │
│   ├── types/                       # 공용 타입
│   │   └── index.ts
│   │
│   ├── pages/                       # 라우팅 화면
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── public/
├── package.json
└── vite.config.ts
```

## 아키텍처 원칙

### 1. 모듈화 (Modular Architecture)

각 도메인(chart, trading, account)은 독립적인 모듈로 구성:
- **components/**: UI 컴포넌트
- **hooks/**: 비즈니스 로직 훅
- **services/**: API 호출 로직

**장점:**
- 도메인별 응집도 향상
- 코드 재사용성
- 테스트 용이성
- 팀 협업 시 충돌 최소화

### 2. 계층 분리 (Layered Architecture)

```
┌─────────────────────────────────┐
│  Presentation Layer (Pages)     │  ← 라우팅, 레이아웃
├─────────────────────────────────┤
│  Component Layer (Modules)      │  ← UI 컴포넌트
├─────────────────────────────────┤
│  Business Logic (Hooks/Stores)  │  ← 상태 관리, 로직
├─────────────────────────────────┤
│  Service Layer (API)            │  ← 네트워크 통신
├─────────────────────────────────┤
│  Infrastructure (HTTP/WS)       │  ← 인프라 레이어
└─────────────────────────────────┘
```

### 3. 상태 관리 전략

**Zustand 사용 이유:**
- Redux보다 간단한 API
- 보일러플레이트 최소화
- TypeScript 지원 우수
- 성능 최적화 내장

**Store 구조:**
```typescript
// chartStore.ts
export const useChartStore = create<ChartState>((set) => ({
  symbol: '005930',
  candles: [],
  setSymbol: (symbol) => set({ symbol }),
  // ...
}));
```

### 4. 네트워크 레이어

**HTTP (Axios):**
- 인터셉터로 토큰 자동 추가
- 401 에러 시 자동 토큰 갱신
- 에러 핸들링 통일

**WebSocket:**
- Context API로 전역 관리
- 토픽 기반 구독/해제
- 자동 재연결 (TODO)

## 데이터 흐름

### 1. 초기 데이터 로드

```
Page Component
    ↓
useChart Hook
    ↓
chartApi.fetchOHLC()
    ↓
httpClient (Axios)
    ↓
Backend API
    ↓
chartStore.setCandles()
    ↓
CandlestickChart Component
```

### 2. 실시간 업데이트

```
WebSocket Server
    ↓
WebSocketProvider
    ↓
subscribe('price:005930')
    ↓
useChart Hook
    ↓
chartStore.updateLastCandle()
    ↓
CandlestickChart Component (자동 리렌더링)
```

### 3. 주문 플로우

```
OrderPanel Component
    ↓
handleSubmit()
    ↓
orderApi.createOrder()
    ↓
httpClient.post()
    ↓
Backend API
    ↓
orderStore.addOrder()
    ↓
OrderHistory Component (자동 업데이트)
```

## 주요 컴포넌트

### CandlestickChart

TradingView Lightweight Charts를 사용한 캔들스틱 차트:

```typescript
// 차트 초기화
const chart = createChart(container, options);
const candleSeries = chart.addCandlestickSeries();

// 데이터 업데이트
candleSeries.setData(chartData);
```

**특징:**
- 고성능 렌더링
- 실시간 업데이트 지원
- 반응형 디자인

### OrderPanel

주문 입력 폼:
- 매수/매도 선택
- 시장가/지정가 선택
- 수량, 가격 입력
- 유효성 검증

### AccountInfo

계좌 정보 표시:
- WebSocket으로 실시간 업데이트
- 30초마다 자동 갱신
- 포맷팅된 금액 표시

## 성능 최적화

### 1. 코드 스플리팅

```typescript
// React.lazy로 페이지 레벨 스플리팅
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
```

### 2. 메모이제이션

```typescript
// useMemo로 비용 높은 계산 캐싱
const chartData = useMemo(() => 
  candles.map(transformToChartData),
  [candles]
);
```

### 3. 가상화 (TODO)

주문 내역이 많을 경우 react-window 사용 고려

## 보안

### 1. 인증

- JWT 토큰 기반
- localStorage에 저장
- 자동 갱신 (Refresh Token)

### 2. XSS 방지

- React의 기본 이스케이핑
- dangerouslySetInnerHTML 사용 금지

### 3. CSRF 방지

- SameSite 쿠키 (백엔드)
- CORS 설정

## 테스트 전략 (TODO)

### 1. 단위 테스트 (Vitest)

```typescript
describe('useChartStore', () => {
  it('should update symbol', () => {
    const { setSymbol } = useChartStore.getState();
    setSymbol('000660');
    expect(useChartStore.getState().symbol).toBe('000660');
  });
});
```

### 2. 통합 테스트 (React Testing Library)

```typescript
test('renders chart with data', async () => {
  render(<CandlestickChart />);
  await waitFor(() => {
    expect(screen.getByText('005930 차트')).toBeInTheDocument();
  });
});
```

### 3. E2E 테스트 (Playwright)

```typescript
test('user can place order', async ({ page }) => {
  await page.goto('/dashboard');
  await page.fill('input[name="quantity"]', '10');
  await page.click('button:has-text("매수 주문")');
  await expect(page.locator('.order-history')).toContainText('submitted');
});
```

## 배포

### 1. 빌드

```bash
npm run build
# dist/ 폴더 생성
```

### 2. Nginx 설정

```nginx
server {
  listen 80;
  server_name hts.example.com;
  
  root /var/www/hts/dist;
  index index.html;
  
  location / {
    try_files $uri $uri/ /index.html;
  }
  
  location /api {
    proxy_pass http://localhost:8000;
  }
  
  location /api/ws {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

## 향후 개선 사항

1. **차트 기능 확장**
   - 기술적 지표 (이동평균, RSI, MACD)
   - 그리기 도구
   - 다중 차트 레이아웃

2. **알림 시스템**
   - 가격 알림
   - 주문 체결 알림
   - 브라우저 푸시 알림

3. **전략 관리 UI**
   - 전략 시작/중지
   - 백테스트 결과 시각화
   - 파라미터 조정

4. **모바일 최적화**
   - 반응형 개선
   - 터치 제스처
   - PWA 지원

5. **다크/라이트 테마**
   - 테마 전환
   - 사용자 설정 저장

## 참고 자료

- [React 공식 문서](https://react.dev/)
- [Zustand 문서](https://github.com/pmndrs/zustand)
- [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/)
- [Vite 문서](https://vitejs.dev/)
