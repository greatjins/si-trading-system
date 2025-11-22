# AWS EC2 배포 가이드

## 사전 준비

1. **AWS 계정 생성**
   - https://aws.amazon.com/ko/free/
   - 신용카드 등록 필요 (1년 무료)

2. **GitHub 계정 생성**
   - https://github.com

---

## Step 1: GitHub 저장소 생성

### 1.1 GitHub에서 새 저장소 생성
```
1. GitHub 로그인
2. 우측 상단 '+' → New repository
3. Repository name: ls-hts
4. Private 선택 (또는 Public)
5. Create repository
```

### 1.2 로컬 코드 푸시
```bash
# 프로젝트 루트에서
git init
git add .
git commit -m "Initial commit: LS HTS Platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ls-hts.git
git push -u origin main
```

---

## Step 2: AWS EC2 인스턴스 생성

### 2.1 EC2 대시보드 접속
```
1. AWS 콘솔 로그인
2. 서비스 → EC2
3. 인스턴스 시작 클릭
```

### 2.2 인스턴스 설정
```
이름: ls-hts-server
AMI: Ubuntu Server 22.04 LTS (무료 티어)
인스턴스 유형: t2.micro (무료 티어)
키 페어: 새로 생성 (ls-hts-key.pem 다운로드)
```

### 2.3 네트워크 설정
```
보안 그룹 규칙:
- SSH (22): 내 IP
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- Custom TCP (8000): 0.0.0.0/0 (개발용, 나중에 제거)
```

### 2.4 스토리지
```
30 GB (무료 티어 한도)
```

### 2.5 인스턴스 시작
```
인스턴스 시작 클릭
퍼블릭 IP 주소 확인 (예: 3.34.123.45)
```

---

## Step 3: 서버 접속 및 설정

### 3.1 SSH 접속
```bash
# Windows (PowerShell)
ssh -i ls-hts-key.pem ubuntu@YOUR_EC2_IP

# 권한 에러 시
icacls ls-hts-key.pem /inheritance:r
icacls ls-hts-key.pem /grant:r "%username%:R"
```

### 3.2 자동 설정 스크립트 실행
```bash
# GitHub에서 프로젝트 클론
cd /var/www
sudo mkdir -p /var/www
sudo chown -R ubuntu:ubuntu /var/www
git clone https://github.com/YOUR_USERNAME/ls-hts.git

# 설정 스크립트 실행
cd ls-hts
chmod +x deploy/setup.sh
./deploy/setup.sh
```

### 3.3 환경 변수 설정
```bash
# config.yaml 생성
cp config.yaml.example config.yaml
nano config.yaml
# 필요한 설정 입력 후 저장 (Ctrl+X, Y, Enter)
```

---

## Step 4: 접속 확인

### 4.1 브라우저에서 접속
```
http://YOUR_EC2_IP
```

### 4.2 서비스 상태 확인
```bash
# 백엔드 상태
sudo systemctl status ls-hts-backend

# Nginx 상태
sudo systemctl status nginx

# 로그 확인
sudo journalctl -u ls-hts-backend -f
```

---

## Step 5: 도메인 연결 (선택)

### 5.1 도메인 구매
- Namecheap, GoDaddy 등

### 5.2 DNS 설정
```
A 레코드: @ → YOUR_EC2_IP
A 레코드: www → YOUR_EC2_IP
```

### 5.3 HTTPS 설정 (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 업데이트 방법

### 코드 업데이트
```bash
# 로컬에서
git add .
git commit -m "Update: ..."
git push

# 서버에서
cd /var/www/ls-hts
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
sudo systemctl restart ls-hts-backend
sudo systemctl reload nginx
```

---

## 문제 해결

### 백엔드가 시작 안 됨
```bash
sudo journalctl -u ls-hts-backend -n 50
```

### Nginx 에러
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### 포트 확인
```bash
sudo netstat -tulpn | grep LISTEN
```

---

## 비용 관리

### 무료 티어 한도
- t2.micro: 750시간/월 (1년간)
- 스토리지: 30GB
- 데이터 전송: 15GB/월

### 비용 알림 설정
```
AWS 콘솔 → Billing → Budgets
월 $1 초과 시 알림 설정
```

---

## 보안 권장사항

1. **SSH 키 관리**
   - 키 파일 안전하게 보관
   - 절대 Git에 올리지 말 것

2. **방화벽**
   - 필요한 포트만 열기
   - SSH는 내 IP만 허용

3. **정기 업데이트**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **백업**
   - EC2 스냅샷 정기 생성
   - 데이터베이스 백업

---

## 다음 단계

- [ ] GitHub Actions로 자동 배포 설정
- [ ] 모니터링 도구 설치 (Prometheus, Grafana)
- [ ] 로그 수집 시스템 구축
- [ ] 부하 테스트
- [ ] HTTPS 적용
