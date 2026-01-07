# CI/CD 자동 배포 설정 가이드

## 개요

GitHub Actions를 사용하여 `main` 브랜치에 push하면 자동으로:
1. 테스트 실행
2. Docker 이미지 빌드
3. AWS EC2에 배포

---

## 1단계: GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

### 필수 Secrets

| Secret 이름 | 설명 | 예시 |
|------------|------|------|
| `EC2_HOST` | EC2 퍼블릭 IP 또는 도메인 | `13.125.123.45` |
| `EC2_SSH_KEY` | EC2 접속용 SSH 프라이빗 키 (전체 내용) | `-----BEGIN RSA PRIVATE KEY-----...` |

### SSH 키 등록 방법

```bash
# Windows PowerShell에서 키 내용 복사
Get-Content C:\Users\USER\.ssh\ls-hts-key.pem | Set-Clipboard

# 또는 직접 파일 열어서 전체 복사
# -----BEGIN RSA PRIVATE KEY----- 부터
# -----END RSA PRIVATE KEY----- 까지 전체
```

---

## 2단계: EC2 초기 설정 (최초 1회)

EC2 인스턴스에 SSH 접속 후 실행:

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
rm get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 프로젝트 디렉토리 생성
mkdir -p ~/ls-hts/deploy ~/ls-hts/data

# 환경 변수 파일 생성
cat > ~/ls-hts/.env << 'EOF'
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
REDIS_PASSWORD=hts_redis_2024
DATABASE_URL=postgresql://hts_user:hts_password_2024@postgres:5432/hts
ENVIRONMENT=production
EOF

# config.yaml 복사 (로컬에서 scp로 전송)
# scp -i ~/.ssh/ls-hts-key.pem config.yaml ubuntu@EC2_IP:~/ls-hts/

# 재로그인 (docker 그룹 적용)
exit
```

---

## 3단계: 배포 설정 파일 전송 (최초 1회)

로컬에서 실행:

```powershell
# Windows PowerShell
$EC2_IP = "13.125.123.45"  # 실제 IP로 변경
$KEY_PATH = "C:\Users\USER\.ssh\ls-hts-key.pem"

# deploy 폴더 전송
scp -i $KEY_PATH -r deploy/* ubuntu@${EC2_IP}:~/ls-hts/deploy/

# config.yaml 전송
scp -i $KEY_PATH config.yaml ubuntu@${EC2_IP}:~/ls-hts/
```

---

## 4단계: 자동 배포 테스트

```bash
# main 브랜치에 push
git add .
git commit -m "feat: CI/CD 파이프라인 추가"
git push origin main

# GitHub Actions 탭에서 워크플로우 실행 확인
# https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

---

## 수동 배포 (긴급 시)

### 방법 1: GitHub Actions 수동 실행
1. GitHub → Actions → "Deploy to AWS EC2"
2. "Run workflow" 버튼 클릭

### 방법 2: 로컬에서 직접 배포

```powershell
# Windows PowerShell
$env:AWS_INSTANCE_IP = "13.125.123.45"
$env:AWS_KEY_PATH = "C:\Users\USER\.ssh\ls-hts-key.pem"

# Git Bash 또는 WSL에서 실행
bash deploy/aws-deploy.sh
```

---

## 배포 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐   │
│  │   Test   │───▶│  Build   │───▶│  Deploy to EC2       │   │
│  │          │    │          │    │                      │   │
│  │ - pytest │    │ - Docker │    │ - SSH 접속           │   │
│  │ - npm    │    │   build  │    │ - 이미지 로드        │   │
│  │   test   │    │ - 이미지 │    │ - docker-compose up  │   │
│  │          │    │   저장   │    │ - 헬스 체크          │   │
│  └──────────┘    └──────────┘    └──────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   AWS EC2       │
                    │                 │
                    │  ┌───────────┐  │
                    │  │  Nginx    │  │
                    │  │  :80/443  │  │
                    │  └─────┬─────┘  │
                    │        │        │
                    │  ┌─────▼─────┐  │
                    │  │  FastAPI  │  │
                    │  │  :8000    │  │
                    │  └─────┬─────┘  │
                    │        │        │
                    │  ┌─────▼─────┐  │
                    │  │ Postgres  │  │
                    │  │ + Redis   │  │
                    │  └───────────┘  │
                    └─────────────────┘
```

---

## 환경별 배포

### Production (main 브랜치)
- 자동 배포: main에 push 시
- URL: http://EC2_IP

### Staging (develop 브랜치) - 선택사항
`.github/workflows/deploy.yml` 수정:

```yaml
on:
  push:
    branches: [main, develop]
```

---

## 롤백 방법

```bash
# EC2에 SSH 접속
ssh -i ~/.ssh/ls-hts-key.pem ubuntu@EC2_IP

# 이전 이미지로 롤백
cd ~/ls-hts
docker-compose -f deploy/docker-compose.prod.yml down
docker tag ls-hts:previous ls-hts:latest
docker-compose -f deploy/docker-compose.prod.yml up -d
```

---

## 모니터링

### 로그 확인
```bash
# 전체 로그
docker-compose -f deploy/docker-compose.prod.yml logs -f

# 앱 로그만
docker logs -f ls-hts-app

# Nginx 로그
docker logs -f ls-hts-nginx
```

### 컨테이너 상태
```bash
docker-compose -f deploy/docker-compose.prod.yml ps
docker stats
```

---

## 문제 해결

### 배포 실패 시
1. GitHub Actions 로그 확인
2. EC2 SSH 접속하여 Docker 로그 확인
3. 디스크 공간 확인: `df -h`
4. 메모리 확인: `free -h`

### SSH 연결 실패
- EC2 보안 그룹에서 22번 포트 열려있는지 확인
- 키 파일 권한 확인 (600)
- EC2 인스턴스 상태 확인

### Docker 빌드 실패
- Dockerfile 문법 확인
- 로컬에서 먼저 빌드 테스트: `docker build -t test .`
