# 프론트엔드 빠른 시작 가이드

## 1. 설치

```bash
cd frontend
npm install --legacy-peer-deps
```

## 2. 환경 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 내용:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 3. 백엔드 실행

프론트엔드를 실행하기 전에 백엔드 API 서버가 실행 중이어야 합니다:

```bash
# 프로젝트 루트에서
uvicorn api.main:app --reload
```

## 4. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속

## 5. 로그인

기본 테스트 계정:
- **사용자명**: `testuser`
- **비밀번호**: `testpass`

## 6. 주요 기능 테스트

### 6.1 차트 확인

1. 대시보드에서 차트가 표시되는지 확인
2. 종목 코드 변경 (예: 005930 → 000660)
3. 시간 간격 변경 (1일 → 1시간)

### 6.2 주문 테스트

1. 우측 주문 패널에서:
   - 매수/매도 선택
   - 시장가/지정가 선택
   - 수량 입력
   - 주문 버튼 클릭

2. 하단 주문 내역에서 주문 확인

### 6.3 WebSocket 연결 확인

브라우저 개발자 도구 → 네트워크 → WS 탭에서:
- WebSocket 연결 상태 확인
- 메시지 송수신 확인

## 7. 개발 팁

### Hot Module Replacement (HMR)

파일 저장 시 자동으로 브라우저가 업데이트됩니다.

### TypeScript 에러 확인

```bash
npm run type-check
```

### 빌드 테스트

```bash
npm run build
npm run preview
```

## 8. 문제 해결

### 포트 충돌

Vite 기본 포트(5173)가 사용 중인 경우:

```bash
npm run dev -- --port 3000
```

### WebSocket 연결 실패

1. 백엔드가 실행 중인지 확인
2. `.env` 파일의 `VITE_WS_URL` 확인
3. 브라우저 콘솔에서 에러 메시지 확인

### 차트가 표시되지 않음

1. 백엔드 API가 정상 응답하는지 확인:
   ```bash
   curl http://localhost:8000/api/price/005930/ohlc?interval=1d
   ```

2. 브라우저 콘솔에서 에러 확인

### 로그인 실패

1. 백엔드 인증 API 확인:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass"}'
   ```

2. 응답에서 `access_token` 확인

## 9. 디버깅

### React DevTools

Chrome 확장 프로그램 설치:
- React Developer Tools
- Redux DevTools (Zustand 지원)

### 네트워크 모니터링

브라우저 개발자 도구 → 네트워크 탭:
- API 요청/응답 확인
- WebSocket 메시지 확인

### 상태 확인

Zustand DevTools:

```typescript
// 브라우저 콘솔에서
window.__ZUSTAND_DEVTOOLS__
```

## 10. 다음 단계

- [프론트엔드 아키텍처](./frontend_architecture.md) 문서 읽기
- 새 기능 추가해보기
- 테스트 작성하기

## 참고

- Vite 개발 서버는 기본적으로 `0.0.0.0:5173`에서 실행됩니다
- 프로덕션 빌드는 `dist/` 폴더에 생성됩니다
- 환경 변수는 `VITE_` 접두사가 필요합니다
