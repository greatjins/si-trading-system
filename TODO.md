# LS HTS 개발 TODO

## ✅ 완료된 작업 (2025-11-22)

### 인프라
- [x] AWS EC2 인스턴스 생성 (t2.micro, 프리티어)
- [x] 보안 그룹 설정 (SSH, HTTP, HTTPS, 8000, 8001)
- [x] GitHub 저장소 연결 (https://github.com/greatjins/si-trading-system.git)
- [x] 서버 환경 구축 (Python 3.11, Node.js 20, Nginx)
- [x] Systemd 서비스 등록 (자동 시작)
- [x] Nginx 리버스 프록시 설정

### 애플리케이션
- [x] Backend API 배포 (FastAPI + WebSocket)
- [x] Frontend 빌드 및 배포 (React + Vite)
- [x] 테스트 유저 생성 (testuser/testpass)
- [x] 테스트 데이터 생성 (삼성전자, SK하이닉스)
- [x] PC/모바일 접속 확인

### 접속 정보
- 서버 주소: http://3.26.44.24
- 로그인: testuser / testpass
- SSH: ssh -i "ls-hts-key.pem" ubuntu@3.26.44.24

---

## 📋 다음 작업 (우선순위)

### 1. LS증권 API 실연동 🔴 HIGH
- [ ] config.yaml에 실제 LS증권 API 키 입력
- [ ] 모의투자 계좌로 테스트
- [ ] 실시간 시세 수신 확인
- [ ] 주문 실행 테스트 (소액)
- [ ] 계좌 정보 조회 확인

**파일 위치:**
- `config.yaml` (서버: ~/si-trading-system/config.yaml)
- `broker/ls/adapter.py` (LS API 연동 코드)

---

### 2. 전략 개발 및 백테스트 🟡 MEDIUM
- [ ] 기존 MA Cross 전략 백테스트 실행
- [ ] 새로운 전략 추가 (RSI, Bollinger Bands 등)
- [ ] 백테스트 결과 분석 및 최적화
- [ ] Strategy Builder로 노코드 전략 생성 테스트

**참고:**
- `core/strategy/examples/ma_cross.py` (예제 전략)
- `docs/strategy_builder_advanced_plan.md` (고급 기능 계획)
- `utils/indicators.py` (기술적 지표)

---

### 3. Frontend 타입 에러 수정 🟡 MEDIUM
- [ ] TypeScript 타입 에러 수정
- [ ] CandlestickChart time 타입 문제 해결
- [ ] import.meta.env 타입 정의 추가
- [ ] vite-env.d.ts 업데이트

**에러 파일:**
- `frontend/src/modules/chart/components/CandlestickChart.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/services/endpoints.ts`
- `frontend/vite-env.d.ts`

---

### 4. 보안 강화 🟠 IMPORTANT
- [ ] JWT_SECRET_KEY 강력한 값으로 변경
- [ ] SSH 포트 변경 (22 → 다른 포트)
- [ ] 보안 그룹에서 SSH를 본인 IP만 허용
- [ ] config.yaml 암호화 또는 환경변수로 관리
- [ ] 정기 백업 설정 (EC2 스냅샷)

**보안 체크리스트:**
- [ ] ls-hts-key.pem 파일 안전하게 보관
- [ ] 불필요한 포트 차단
- [ ] 정기적인 시스템 업데이트

---

### 5. 모니터링 및 로깅 🟢 LOW
- [ ] CloudWatch 알람 설정
- [ ] 로그 수집 및 분석 시스템
- [ ] 에러 알림 (이메일/슬랙)
- [ ] 성능 모니터링 대시보드

---

### 6. 도메인 및 SSL (선택사항) 🔵 OPTIONAL
- [ ] 도메인 구매 (예: hts.yourdomain.com)
- [ ] DNS A 레코드 설정
- [ ] Let's Encrypt SSL 인증서 설치
- [ ] HTTPS 리다이렉트 설정

---

## 🛠️ 유용한 명령어

### 서버 접속
```bash
ssh -i "ls-hts-key.pem" ubuntu@3.26.44.24
```

### 서비스 관리
```bash
# 로그 확인
sudo journalctl -u ls-hts-backend -f

# 서비스 재시작
sudo systemctl restart ls-hts-backend
sudo systemctl restart nginx

# 상태 확인
sudo systemctl status ls-hts-backend
```

### 코드 업데이트
```bash
cd ~/si-trading-system
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend
NODE_OPTIONS="--max-old-space-size=512" npx vite build
cd ..
sudo systemctl restart ls-hts-backend
```

### 로컬 개발
```bash
# Backend
python -m uvicorn api.main:app --reload

# Frontend
cd frontend
npm run dev
```

---

## 📝 참고 문서

- AWS 배포 가이드: `deploy/AWS_SETUP_GUIDE.md`
- 전략 빌더 계획: `docs/strategy_builder_advanced_plan.md`
- 프로젝트 진행상황: `PROGRESS.md`
- README: `README.md`

---

## 🐛 알려진 이슈

1. **TypeScript 빌드 에러**
   - 현재: `npx vite build`로 타입 체크 스킵하여 빌드
   - 해결 필요: 타입 정의 수정

2. **메모리 제한 (t2.micro)**
   - 현재: 스왑 파일 2GB 설정으로 해결
   - 향후: 트래픽 증가 시 인스턴스 업그레이드 고려

3. **LS증권 API 미연동**
   - 현재: Mock 데이터 사용
   - 해결 필요: 실제 API 키 입력 및 테스트

---

## 💡 개선 아이디어

- [ ] 다크 모드 지원
- [ ] 모바일 최적화 UI
- [ ] 푸시 알림 (주문 체결, 손익 알림)
- [ ] 전략 성과 리포트 자동 생성
- [ ] 다중 계좌 지원
- [ ] 타 증권사 Adapter 추가 (키움, 한국투자 등)
- [ ] 백테스트 병렬 처리
- [ ] AutoML 전략 자동 탐색

---

## 📞 문제 발생 시

1. 서버 로그 확인: `sudo journalctl -u ls-hts-backend -n 100`
2. Nginx 로그 확인: `sudo tail -f /var/log/nginx/error.log`
3. 서비스 재시작: `sudo systemctl restart ls-hts-backend nginx`
4. 디스크 용량 확인: `df -h`
5. 메모리 확인: `free -h`

---

**마지막 업데이트:** 2025-11-22
**다음 작업일:** 2025-11-23
