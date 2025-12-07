# 프론트엔드 빌드 테스트 전 검토 보고서

## 📋 검토 일시
- 2025-11-30

## 🎯 검토 목적
프론트엔드 빌드 테스트 전 로직 및 UI 일관성 검토

---

## ✅ 1. 프로젝트 구조 분석

### 기술 스택
- **프레임워크**: React 18.3.1 + TypeScript 5.6.2
- **빌드 도구**: Vite 6.0.5
- **라우팅**: React Router DOM 7.1.1
- **상태 관리**: Zustand 5.0.2
- **HTTP 클라이언트**: Axios 1.7.9
- **차트**: Lightweight Charts 4.2.2

### 디렉토리 구조
```
frontend/src/
├── app/
│   ├── providers/     # AppProvider (Router + WebSocket)
│   └── router/        # 라우팅 설정
├── components/
│   ├── Chart/
│   ├── Dashboard/
│   ├── Layout/        # PageLayout (공통 레이아웃)
│   └── AccountSelector.tsx
├── modules/           # 기능별 모듈
│   ├── account/
│   ├── chart/
│   └── trading/
├── pages/             # 페이지 컴포넌트
├── services/          # API 서비스
├── types/             # TypeScript 타입
└── utils/             # 유틸리티
```

---

## 🔍 2. 주요 이슈 및 개선 사항

### 🚨 Critical Issues

#### 1. **App.tsx 미사용 문제**
- **현상**: `main.tsx`에서 `AppProvider`를 직접 사용하지만, `App.tsx`는 Vite 기본 템플릿 그대로 남아있음
- **영향**: 혼란 유발, 불필요한 파일
- **해결**: `App.tsx` 삭제 또는 실제 앱 컴포넌트로 교체

```typescript
// 현재 main.tsx
createRoot(document.getElementById('root')!).render(
  <AppProvider />  // App.tsx를 사용하지 않음
)

// 현재 App.tsx (사용되지 않음)
function App() {
  return <div>Vite + React 템플릿</div>
}
```

**권장 수정**:
```typescript
// main.tsx
import App from './App'
createRoot(document.getElementById('root')!).render(<App />)

// App.tsx
export default function App() {
  return (
    <WebSocketProvider>
      <RouterProvider router={router} />
    </WebSocketProvider>
  )
}
```

#### 2. **StrategyBuilderPage.tsx 파일 크기 과다**
- **현상**: 2,331줄의 단일 파일
- **문제점**:
  - 유지보수 어려움
  - 코드 재사용 불가
  - 성능 저하 가능성
- **해결**: 컴포넌트 분리 필요

**권장 구조**:
```
pages/StrategyBuilderPage/
├── index.tsx                    # 메인 페이지
├── components/
│   ├── StockSelectionTab.tsx    # 종목 선정 탭
│   ├── BuyConditionsTab.tsx     # 매수 조건 탭
│   ├── EntryStrategyTab.tsx     # 진입 전략 탭
│   ├── SellConditionsTab.tsx    # 매도 조건 탭
│   ├── PositionManagementTab.tsx # 포지션 관리 탭
│   ├── ConditionCard.tsx        # 조건 카드
│   ├── PyramidConfig.tsx        # 피라미딩 설정
│   └── TrailingStopConfig.tsx   # 트레일링 스탑 설정
├── hooks/
│   └── useStrategyBuilder.ts    # 전략 빌더 로직
└── types.ts                     # 타입 정의
```

#### 3. **라우터 인증 로직 중복**
- **현상**: 각 라우트마다 `ProtectedRoute` 래퍼 사용
- **문제점**: 코드 중복, 유지보수 어려움
- **해결**: 라우터 레벨에서 인증 처리

**현재**:
```typescript
{
  path: '/dashboard',
  element: <ProtectedRoute><DashboardPage /></ProtectedRoute>
}
```

**권장**:
```typescript
// router/index.tsx
const protectedRoutes = [
  { path: '/dashboard', element: <DashboardPage /> },
  { path: '/backtest', element: <BacktestPage /> },
  // ...
]

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedLayout />,  // 인증 체크 + 공통 레이아웃
    children: protectedRoutes
  }
])
```

---

### ⚠️ Warning Issues

#### 4. **CSS 스타일 관리 문제**
- **현상**: `index.css`에 모든 스타일이 집중 (1,000+ 줄)
- **문제점**:
  - 스타일 충돌 가능성
  - 유지보수 어려움
  - 번들 크기 증가
- **해결**: CSS Modules 또는 Styled Components 도입

**권장 구조**:
```
styles/
├── global.css           # 전역 스타일
├── variables.css        # CSS 변수
├── components/
│   ├── button.module.css
│   ├── form.module.css
│   └── table.module.css
└── pages/
    ├── dashboard.module.css
    └── backtest.module.css
```

#### 5. **타입 안정성 부족**
- **현상**: 여러 곳에서 `any` 타입 사용
- **위치**:
  - `BacktestPage.tsx`: `err: any`
  - `StrategyBuilderPage.tsx`: 여러 곳
- **해결**: 명시적 타입 정의

```typescript
// types/api.ts
export interface ApiError {
  detail: string
  status: number
}

// 사용
catch (err) {
  const error = err as AxiosError<ApiError>
  setError(error.response?.data?.detail || '요청 실패')
}
```

#### 6. **환경 변수 관리**
- **현상**: `.env` 파일이 5개 존재
  - `.env`, `.env.development`, `.env.local`, `.env.production`, `.env.example`
- **문제점**: 혼란 유발, 우선순위 불명확
- **해결**: 필요한 파일만 유지

**권장**:
```
.env.example          # 템플릿 (Git 추적)
.env.local           # 로컬 개발용 (Git 무시)
.env.production      # 프로덕션용 (배포 시 주입)
```

---

### 💡 Improvement Suggestions

#### 7. **API 엔드포인트 관리 개선**
- **현재**: `endpoints.ts`에 하드코딩
- **개선**: 환경 변수 활용

```typescript
// config.ts
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  wsURL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
}

// endpoints.ts
export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REFRESH: '/api/auth/refresh'
  },
  // ...
} as const
```

#### 8. **에러 처리 표준화**
- **현상**: 각 컴포넌트마다 다른 에러 처리 방식
- **개선**: 공통 에러 핸들러 및 토스트 시스템

```typescript
// hooks/useToast.ts
export function useToast() {
  return {
    success: (message: string) => { /* ... */ },
    error: (message: string) => { /* ... */ },
    warning: (message: string) => { /* ... */ }
  }
}

// 사용
const toast = useToast()
try {
  await api.call()
  toast.success('성공!')
} catch (err) {
  toast.error(getErrorMessage(err))
}
```

#### 9. **로딩 상태 관리 개선**
- **현상**: 각 컴포넌트마다 `isLoading` 상태 관리
- **개선**: 공통 로딩 훅 사용

```typescript
// hooks/useAsync.ts
export function useAsync<T>(asyncFn: () => Promise<T>) {
  const [state, setState] = useState({
    data: null as T | null,
    loading: false,
    error: null as Error | null
  })
  
  const execute = async () => {
    setState({ data: null, loading: true, error: null })
    try {
      const data = await asyncFn()
      setState({ data, loading: false, error: null })
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error })
    }
  }
  
  return { ...state, execute }
}
```

#### 10. **DataCollection 페이지 스타일 누락**
- **현상**: `DataCollection.tsx`에서 사용하는 CSS 클래스가 `index.css`에 없음
  - `.data-collection-content`
  - `.stats-grid`, `.stat-card`
  - `.progress-section`, `.progress-bar`
  - `.log-container`, `.log-line`
  - `.data-table`
- **해결**: 스타일 추가 필요

---

## 🎨 3. UI/UX 일관성 검토

### ✅ 일관성 있는 부분
1. **컬러 시스템**: CSS 변수로 통일된 색상 관리
2. **버튼 스타일**: `.btn`, `.btn-primary`, `.btn-danger` 등 일관된 클래스
3. **폼 요소**: `.form-input`, `.form-select` 등 통일된 스타일
4. **레이아웃**: `PageLayout` 컴포넌트로 공통 구조 유지

### ⚠️ 개선 필요 부분
1. **간격(Spacing)**: 일부 페이지에서 `margin`, `padding` 값이 불규칙
2. **반응형**: 일부 컴포넌트에서 모바일 대응 부족
3. **접근성**: ARIA 속성 부족, 키보드 네비게이션 미흡

---

## 🧪 4. 빌드 테스트 체크리스트

### 빌드 전 확인 사항
- [ ] TypeScript 컴파일 에러 확인: `npm run type-check`
- [ ] ESLint 에러 확인: `npx eslint src`
- [ ] 사용하지 않는 import 제거
- [ ] Console.log 제거 (프로덕션)
- [ ] 환경 변수 설정 확인

### 빌드 명령어
```bash
# 개발 서버
npm run dev

# 타입 체크
npm run type-check

# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

### 빌드 후 확인 사항
- [ ] 번들 크기 확인 (dist 폴더)
- [ ] 청크 분할 확인 (react-vendor, chart-vendor, state-vendor)
- [ ] 소스맵 생성 확인
- [ ] 정적 파일 복사 확인 (public 폴더)

---

## 📊 5. 성능 최적화 권장 사항

### 코드 스플리팅
```typescript
// router/index.tsx
import { lazy } from 'react'

const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const BacktestPage = lazy(() => import('../pages/BacktestPage'))
const StrategyBuilderPage = lazy(() => import('../pages/StrategyBuilderPage'))

// Suspense로 감싸기
<Suspense fallback={<LoadingSpinner />}>
  <Outlet />
</Suspense>
```

### 이미지 최적화
- SVG 아이콘을 컴포넌트로 변환
- 이미지 lazy loading 적용

### 메모이제이션
```typescript
// 무거운 계산이 있는 컴포넌트
const MemoizedChart = memo(CandlestickChart)

// 콜백 최적화
const handleSubmit = useCallback(() => {
  // ...
}, [dependencies])
```

---

## 🔧 6. 즉시 수정 필요 항목 (Priority)

### 🔴 High Priority
1. **App.tsx 정리** - 혼란 제거
2. **DataCollection 스타일 추가** - 페이지 깨짐 방지
3. **TypeScript 에러 수정** - 빌드 실패 방지

### 🟡 Medium Priority
4. **StrategyBuilderPage 리팩토링** - 유지보수성 향상
5. **에러 처리 표준화** - 사용자 경험 개선
6. **환경 변수 정리** - 배포 안정성

### 🟢 Low Priority
7. **CSS 모듈화** - 장기적 유지보수
8. **접근성 개선** - 사용자 경험
9. **성능 최적화** - 로딩 속도

---

## 📝 7. 수정 권장 파일 목록

### 즉시 수정
```
frontend/src/
├── App.tsx                          # 삭제 또는 재작성
├── index.css                        # DataCollection 스타일 추가
└── pages/
    └── StrategyBuilderPage.tsx      # any 타입 제거
```

### 단계적 개선
```
frontend/src/
├── app/
│   └── router/index.tsx             # 인증 로직 개선
├── pages/
│   └── StrategyBuilderPage/         # 컴포넌트 분리
└── styles/                          # CSS 모듈화
```

---

## ✅ 8. 결론 및 권장 사항

### 현재 상태
- **빌드 가능 여부**: ⚠️ 조건부 가능 (스타일 누락 이슈)
- **프로덕션 준비도**: 🟡 60% (개선 필요)
- **코드 품질**: 🟡 중간 (리팩토링 필요)

### 빌드 테스트 전 필수 작업
1. DataCollection 페이지 스타일 추가
2. TypeScript 컴파일 에러 확인 및 수정
3. App.tsx 정리

### 빌드 테스트 후 작업
1. StrategyBuilderPage 컴포넌트 분리
2. 에러 처리 및 로딩 상태 표준화
3. CSS 모듈화 및 성능 최적화

### 다음 단계
```bash
# 1. 스타일 추가
# 2. 타입 체크
npm run type-check

# 3. 빌드 테스트
npm run build

# 4. 로컬 테스트
npm run preview

# 5. 통합 테스트
# - 로그인 플로우
# - 페이지 네비게이션
# - API 연동
# - WebSocket 연결
```

---

## 📌 참고 사항

### Vite 빌드 설정
- **청크 분할**: react-vendor, chart-vendor, state-vendor
- **프록시**: `/api` → `http://localhost:8000`
- **WebSocket**: 프록시 지원 (`ws: true`)

### 브라우저 지원
- Chrome/Edge: 최신 2개 버전
- Firefox: 최신 2개 버전
- Safari: 최신 2개 버전

### 배포 고려사항
- 환경 변수 주입 방법
- API 엔드포인트 설정
- CORS 설정 확인
- WebSocket 연결 설정
