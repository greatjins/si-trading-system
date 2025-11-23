# AWS EC2 배포 가이드

## 1단계: EC2 인스턴스 생성

### 1.1 AWS Console 접속
1. https://aws.amazon.com/ko/ 접속
2. 로그인 → EC2 대시보드로 이동
3. "인스턴스 시작" 클릭

### 1.2 인스턴스 설정

#### 이름 및 태그
```
이름: si-trading-system
```

#### AMI (운영체제) 선택
```
Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
아키텍처: 64비트 (x86)
```

#### 인스턴스 유형
```
✅ 프리티어: t2.micro 또는 t3.micro (vCPU 2개, 메모리 1GB) - 무료 (월 750시간)
- 개발/테스트: t3.small (vCPU 2개, 메모리 2GB) - 월 $15
- 프로덕션: t3.medium (vCPU 2개, 메모리 4GB) - 월 $30

⚠️ 프리티어 선택 시:
- "프리 티어 사용 가능" 표시 확인
- t2.micro 또는 t3.micro 선택
- 메모리 1GB로 제한적이지만 테스트용으로 충분
```

#### 키 페어 (로그인)
```
1. "새 키 페어 생성" 클릭
2. 키 페어 이름: ls-hts-key
3. 키 페어 유형: RSA
4. 프라이빗 키 파일 형식: .pem (Mac/Linux) 또는 .ppk (Windows/PuTTY)
5. "키 페어 생성" → 자동 다운로드됨
⚠️ 이 파일은 재다운로드 불가능하니 안전하게 보관!
```

#### 네트워크 설정
```
1. "편집" 클릭
2. VPC: 기본값 유지
3. 서브넷: "기본 설정 없음" 그대로 두기 (자동 선택됨)
4. 퍼블릭 IP 자동 할당: 활성화
5. 방화벽(보안 그룹): "새 보안 그룹 생성"
   - 보안 그룹 이름: ls-hts-sg
   - 설명: LS HTS Security Group
```

#### 보안 그룹 규칙 (인바운드) - 인스턴스 생성 시
```
일단 기본 규칙만 추가:

규칙 1: SSH
- 유형: SSH
- 포트: 22
- 소스: 내 IP (자동 감지) 또는 0.0.0.0/0

규칙 2: HTTP
- 유형: HTTP
- 포트: 80
- 소스: 0.0.0.0/0

규칙 3: HTTPS
- 유형: HTTPS
- 포트: 443
- 소스: 0.0.0.0/0

⚠️ 포트 8000, 8001은 인스턴스 생성 후 추가합니다!
```

#### 스토리지 구성
```
1. 볼륨 크기: 30 GiB (프리티어는 최대 30GB 무료)
2. 볼륨 유형: gp3 (범용 SSD) 또는 gp2
3. 기본 설정 그대로 사용 (종료 시 삭제는 자동 활성화됨)
```

### 1.3 인스턴스 시작
```
1. 오른쪽 "인스턴스 시작" 클릭
2. "인스턴스 시작 중" 메시지 확인
3. "인스턴스 보기" 클릭
```

### 1.4 보안 그룹에 추가 포트 열기
```
1. EC2 대시보드 → 왼쪽 메뉴 "보안 그룹" 클릭
2. "ls-hts-sg" 선택
3. 하단 "인바운드 규칙" 탭 → "인바운드 규칙 편집" 클릭
4. "규칙 추가" 클릭하여 아래 2개 추가:

규칙 4: FastAPI Backend
- 유형: 사용자 지정 TCP
- 포트 범위: 8000
- 소스: 0.0.0.0/0
- 설명: FastAPI Backend

규칙 5: WebSocket
- 유형: 사용자 지정 TCP
- 포트 범위: 8001
- 소스: 0.0.0.0/0
- 설명: WebSocket

5. "규칙 저장" 클릭
```

---

## 2단계: 인스턴스 접속 준비

### 2.1 퍼블릭 IP 확인
```
EC2 대시보드 → 인스턴스 선택 → 세부 정보에서 확인
예: 13.125.123.45
```

### 2.2 키 파일 권한 설정 (Windows)
```powershell
# 다운로드한 .pem 파일 위치로 이동
cd C:\Users\USER\Downloads

# 권한 설정 (Windows에서는 파일 속성에서 수동 설정)
# 파일 우클릭 → 속성 → 보안 → 고급 → 상속 사용 안 함 → 모든 권한 제거 → 본인 계정만 추가
```

### 2.3 SSH 접속 (Windows - PowerShell)
```powershell
ssh -i "ls-hts-key.pem" ubuntu@13.125.123.45
```

### 2.4 SSH 접속 (Windows - PuTTY 사용 시)
```
1. PuTTY 다운로드: https://www.putty.org/
2. PuTTYgen으로 .pem → .ppk 변환
3. PuTTY 실행
   - Host Name: ubuntu@13.125.123.45
   - Port: 22
   - Connection → SSH → Auth → Private key: .ppk 파일 선택
   - Open 클릭
```

---

## 3단계: 서버 초기 설정

### 3.1 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

### 3.2 필수 패키지 설치
```bash
# Python 3.11 설치
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Node.js 20.x 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Git 설치
sudo apt install -y git

# Nginx 설치
sudo apt install -y nginx

# 기타 도구
sudo apt install -y build-essential curl wget vim
```

### 3.3 방화벽 설정 (UFW)
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # FastAPI
sudo ufw allow 8001/tcp  # WebSocket
sudo ufw enable
sudo ufw status
```

---

## 4단계: 프로젝트 배포

### 4.1 Git Clone
```bash
cd ~
git clone https://github.com/greatjins/si-trading-system.git
cd si-trading-system
```

### 4.2 Python 가상환경 설정
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 설정 파일 생성
```bash
# config.yaml 생성
cp config.yaml.example config.yaml
vim config.yaml  # LS증권 API 키 입력

# 환경변수 설정
export JWT_SECRET_KEY="your-super-secret-key-change-this"
export DATABASE_URL="sqlite:///./data/hts.db"
```

### 4.4 데이터베이스 초기화
```bash
python scripts/create_test_user.py
python scripts/create_test_data.py
```

### 4.5 Frontend 빌드
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 5단계: 서비스 등록 (자동 시작)

### 5.1 Backend 서비스 생성
```bash
sudo vim /etc/systemd/system/ls-hts-backend.service
```

내용:
```ini
[Unit]
Description=LS HTS Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/si-trading-system
Environment="PATH=/home/ubuntu/si-trading-system/venv/bin"
Environment="JWT_SECRET_KEY=your-super-secret-key-change-this"
ExecStart=/home/ubuntu/si-trading-system/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 서비스 시작
```bash
sudo systemctl daemon-reload
sudo systemctl enable ls-hts-backend
sudo systemctl start ls-hts-backend
sudo systemctl status ls-hts-backend
```

---

## 6단계: Nginx 설정

### 6.1 Nginx 설정 파일
```bash
sudo vim /etc/nginx/sites-available/ls-hts
```

내용:
```nginx
server {
    listen 80;
    server_name 13.125.123.45;  # 실제 IP로 변경

    # Frontend (React)
    location / {
        root /home/ubuntu/si-trading-system/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

### 6.2 Nginx 활성화
```bash
sudo ln -s /etc/nginx/sites-available/ls-hts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7단계: 접속 테스트

### 7.1 브라우저에서 접속
```
http://13.125.123.45
```

### 7.2 API 테스트
```bash
curl http://13.125.123.45/api/health
```

### 7.3 모바일에서 접속
```
안드로이드 브라우저에서:
http://13.125.123.45
```

---

## 8단계: 도메인 연결 (선택사항)

### 8.1 도메인 구매
- 가비아, 호스팅케이알 등에서 도메인 구매
- 예: hts.yourdomain.com

### 8.2 DNS 설정
```
A 레코드 추가:
호스트: hts
값: 13.125.123.45 (EC2 IP)
TTL: 3600
```

### 8.3 SSL 인증서 설치 (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d hts.yourdomain.com
```

---

## 유지보수 명령어

### 로그 확인
```bash
# Backend 로그
sudo journalctl -u ls-hts-backend -f

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 서비스 재시작
```bash
sudo systemctl restart ls-hts-backend
sudo systemctl restart nginx
```

### 코드 업데이트
```bash
cd ~/si-trading-system
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
sudo systemctl restart ls-hts-backend
```

### 디스크 용량 확인
```bash
df -h
du -sh ~/si-trading-system
```

---

## 비용 예상 (월간)

```
✅ 프리티어 (12개월):
- EC2 t2.micro/t3.micro: 무료 (월 750시간)
- 스토리지 30GB: 무료 (EBS 30GB까지)
- 데이터 전송: 무료 (15GB까지)
- 총 비용: $0/월

유료 전환 후:
- EC2 t3.small: $15
- EC2 t3.medium: $30
- 스토리지 30GB: $3
- 총 예상: $18~$33/월
```

---

## 보안 체크리스트

- [ ] SSH 키 안전하게 보관
- [ ] 보안 그룹에서 불필요한 포트 차단
- [ ] JWT_SECRET_KEY 강력한 값으로 변경
- [ ] config.yaml에 실제 API 키 입력 (Git에 커밋 안 됨)
- [ ] 정기적인 시스템 업데이트
- [ ] 백업 설정 (스냅샷)
- [ ] CloudWatch 모니터링 설정

---

## 문제 해결

### 접속이 안 될 때
1. EC2 인스턴스 상태 확인 (실행 중인지)
2. 보안 그룹 규칙 확인
3. 서비스 상태 확인: `sudo systemctl status ls-hts-backend`
4. 방화벽 확인: `sudo ufw status`

### 서비스가 시작 안 될 때
```bash
# 로그 확인
sudo journalctl -u ls-hts-backend -n 50

# 수동 실행으로 에러 확인
cd ~/si-trading-system
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 메모리 부족 (t2.micro/t3.micro 필수!)
```bash
# 스왑 파일 생성 (2GB) - 메모리 1GB 인스턴스에서 필수!
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

**t2.micro/t3.micro 최적화 팁:**
```bash
# npm 빌드 시 메모리 제한 설정
cd frontend
NODE_OPTIONS="--max-old-space-size=512" npm run build

# Python 프로세스 워커 수 줄이기 (uvicorn)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```
