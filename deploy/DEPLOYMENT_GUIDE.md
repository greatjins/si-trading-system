# LS증권 개인화 HTS - AWS 배포 가이드

> 🎯 **목표**: 내 컴퓨터에서 만든 프로그램을 인터넷에 올려서 어디서든 접속할 수 있게 만들기

---

## 📚 용어 설명 (모르면 여기부터!)

| 용어 | 쉬운 설명 |
|------|----------|
| **AWS** | 아마존에서 운영하는 컴퓨터 대여 서비스. 내 컴퓨터 대신 아마존 컴퓨터를 빌려서 사용 |
| **EC2** | AWS에서 빌려주는 컴퓨터 한 대. "가상 서버"라고도 부름 |
| **인스턴스** | EC2 컴퓨터 한 대를 부르는 말 |
| **SSH** | 멀리 있는 컴퓨터에 접속하는 방법. 원격 데스크톱 같은 것 |
| **Docker** | 프로그램을 상자에 담아서 어디서든 똑같이 실행되게 해주는 도구 |
| **키 페어 (.pem 파일)** | AWS 컴퓨터에 접속할 때 필요한 비밀 열쇠 파일 |

---

## 🚀 배포 순서 (총 5단계)

```
1단계: AWS 가입하기
    ↓
2단계: 컴퓨터(EC2) 만들기  
    ↓
3단계: 내 컴퓨터에서 AWS 컴퓨터로 파일 보내기
    ↓
4단계: AWS 컴퓨터에서 프로그램 실행하기
    ↓
5단계: 인터넷으로 접속해보기
```

---

## 1단계: AWS 가입하기

### 1-1. AWS 홈페이지 접속
1. 인터넷 브라우저를 열고 주소창에 입력:
   ```
   https://aws.amazon.com/ko/
   ```

2. 오른쪽 위 **"AWS 계정 생성"** 버튼 클릭

### 1-2. 회원가입
1. 이메일 주소 입력
2. 비밀번호 설정
3. 신용카드 등록 (1년간 무료이지만 카드는 필요함)
4. 휴대폰 인증

> ⚠️ **주의**: 신용카드를 등록해도 프리티어(무료) 범위 내에서는 요금이 나가지 않아요!

---

## 2단계: EC2 컴퓨터 만들기

### 2-1. EC2 페이지로 이동
1. AWS에 로그인
2. 왼쪽 위 검색창에 **"EC2"** 입력
3. **"EC2"** 클릭

### 2-2. 인스턴스 시작 (컴퓨터 만들기)
1. 주황색 **"인스턴스 시작"** 버튼 클릭

2. **이름 입력**:
   ```
   ls-hts-server
   ```

3. **운영체제 선택**:
   - "Ubuntu" 클릭
   - "Ubuntu Server 22.04 LTS" 선택 (프리 티어 사용 가능 표시 확인)

4. **인스턴스 유형 선택**:
   - `t2.micro` 선택 (프리 티어 무료)
   - 또는 `t3.small` 선택 (유료지만 더 빠름, 월 약 2만원)

5. **키 페어 생성** (매우 중요! ⭐):
   - "새 키 페어 생성" 클릭
   - 키 페어 이름: `ls-hts-key`
   - 키 페어 유형: RSA
   - 프라이빗 키 파일 형식: `.pem`
   - **"키 페어 생성"** 클릭
   - 파일이 다운로드됨 → **이 파일 절대 잃어버리면 안 됨!**
   - 다운로드된 `ls-hts-key.pem` 파일을 안전한 곳에 저장
     ```
     예: C:\Users\내이름\aws-keys\ls-hts-key.pem
     ```

6. **네트워크 설정**:
   - "편집" 클릭
   - 아래 항목들 체크:
     - ✅ SSH 트래픽 허용 (포트 22)
     - ✅ 인터넷에서 HTTPS 트래픽 허용 (포트 443)
     - ✅ 인터넷에서 HTTP 트래픽 허용 (포트 80)

7. **스토리지 구성**:
   - `30` GiB로 변경 (프리티어 최대)

8. **인스턴스 시작** 버튼 클릭!

### 2-3. IP 주소 확인하기
1. "인스턴스 보기" 클릭
2. 방금 만든 인스턴스 클릭
3. **"퍼블릭 IPv4 주소"** 확인하고 메모
   ```
   예: 13.125.xxx.xxx
   ```

> 📝 이 IP 주소가 내 AWS 컴퓨터의 주소예요!

---

## 3단계: AWS 컴퓨터에 접속하기

### 3-1. Windows에서 접속하기

1. **PowerShell 열기**:
   - 키보드에서 `Windows 키` 누르기
   - "PowerShell" 입력
   - "Windows PowerShell" 클릭

2. **SSH로 접속**:
   ```powershell
   ssh -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" ubuntu@13.125.xxx.xxx
   ```
   - `C:\Users\내이름\aws-keys\ls-hts-key.pem` → 아까 저장한 키 파일 경로
   - `13.125.xxx.xxx` → 아까 메모한 IP 주소

3. **처음 접속 시 질문이 나오면**:
   ```
   Are you sure you want to continue connecting (yes/no)?
   ```
   `yes` 입력하고 Enter

4. **접속 성공하면 이렇게 보여요**:
   ```
   ubuntu@ip-172-31-xx-xx:~$
   ```

> 🎉 축하해요! AWS 컴퓨터에 접속했어요!

---

## 4단계: 프로그램 설치하고 실행하기

### 4-1. Docker 설치하기

AWS 컴퓨터에 접속한 상태에서 아래 명령어를 **한 줄씩** 입력하고 Enter:

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Docker 권한 설정
sudo usermod -aG docker ubuntu

# 4. Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Git 설치
sudo apt install -y git
```

### 4-2. 재접속하기

```bash
# 접속 종료
exit

# 다시 접속 (PowerShell에서)
ssh -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" ubuntu@13.125.xxx.xxx
```

### 4-3. 프로젝트 폴더 만들기

```bash
mkdir -p ~/ls-hts
```

---

## 5단계: 내 컴퓨터에서 파일 보내기

### 5-1. 새 PowerShell 창 열기 (내 컴퓨터에서)

AWS 접속한 창은 그대로 두고, **새 PowerShell 창**을 열어요.

### 5-2. 프로젝트 폴더로 이동

```powershell
cd C:\Users\내이름\프로젝트폴더\Si-WebTrading
```

### 5-3. 파일 보내기

```powershell
# 전체 프로젝트 보내기
scp -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" -r * ubuntu@13.125.xxx.xxx:~/ls-hts/
```

> ⏳ 파일이 많으면 시간이 좀 걸려요. 기다려주세요!

---

## 6단계: AWS에서 프로그램 실행하기

### 6-1. AWS 컴퓨터로 돌아가기

아까 SSH 접속한 PowerShell 창으로 돌아가요.

### 6-2. 프로젝트 폴더로 이동

```bash
cd ~/ls-hts
```

### 6-3. 환경 설정 파일 만들기

```bash
# .env 파일 만들기
cat > .env << 'EOF'
JWT_SECRET_KEY=my-super-secret-key-change-this
REDIS_PASSWORD=hts_redis_2024
DATABASE_URL=postgresql://hts_user:hts_password_2024@postgres:5432/hts
ENVIRONMENT=production
EOF

# config.yaml 복사
cp config.yaml.example config.yaml
```

### 6-4. 프로그램 실행!

```bash
docker-compose -f deploy/docker-compose.prod.yml up --build -d
```

> ⏳ 처음 실행할 때는 5~10분 정도 걸려요!

### 6-5. 실행 확인

```bash
# 컨테이너 상태 확인
docker-compose -f deploy/docker-compose.prod.yml ps
```

이렇게 나오면 성공:
```
NAME                STATUS
ls-hts-app          Up
ls-hts-postgres     Up
ls-hts-nginx        Up
```

---

## 7단계: 접속해보기! 🎉

### 웹 브라우저에서 접속

인터넷 브라우저 주소창에 입력:
```
http://13.125.xxx.xxx
```

> 🎊 화면이 나오면 배포 성공!

---

## 🔄 파일 수정 후 다시 배포하기

코드를 수정했을 때 AWS에 다시 올리는 방법이에요.

### 방법 1: 빠른 배포 스크립트 사용 (추천)

```powershell
# 내 컴퓨터 PowerShell에서 실행
.\deploy\quick-deploy.ps1 -AwsIp "13.125.xxx.xxx" -KeyPath "C:\Users\내이름\aws-keys\ls-hts-key.pem"
```

### 방법 2: 특정 파일만 보내기

```powershell
# 1. 파일 보내기
scp -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" api/routes/strategy_builder.py ubuntu@13.125.xxx.xxx:~/ls-hts/api/routes/

# 2. AWS에서 재시작
ssh -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" ubuntu@13.125.xxx.xxx "cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml restart app"
```

### 방법 3: 전체 다시 보내기

```powershell
# 내 컴퓨터에서
cd C:\Users\내이름\프로젝트폴더\Si-WebTrading
scp -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" -r * ubuntu@13.125.xxx.xxx:~/ls-hts/

# AWS에서 재시작
ssh -i "C:\Users\내이름\aws-keys\ls-hts-key.pem" ubuntu@13.125.xxx.xxx "cd ~/ls-hts && docker-compose -f deploy/docker-compose.prod.yml restart app"
```

---

## 🚨 문제가 생겼을 때

### "Permission denied" 오류

키 파일 권한 문제예요:
```powershell
# Windows에서는 이 오류가 나도 보통 접속됨
# 계속 안 되면 키 파일 경로 확인
```

### "Connection refused" 오류

EC2가 아직 시작 안 됐거나 보안 그룹 설정 문제:
1. AWS 콘솔에서 인스턴스 상태가 "실행 중"인지 확인
2. 보안 그룹에서 포트 22, 80, 443이 열려있는지 확인

### 웹페이지가 안 열림

```bash
# AWS에서 로그 확인
cd ~/ls-hts
docker-compose -f deploy/docker-compose.prod.yml logs
```

### 메모리 부족 (t2.micro 사용 시)

```bash
# 스왑 파일 만들기 (가상 메모리)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 💰 비용 안내

### 프리티어 (1년간 무료)
- EC2 t2.micro: 월 750시간 무료
- 스토리지: 30GB 무료
- 데이터 전송: 월 15GB 무료

### 프리티어 끝난 후 예상 비용
- t2.micro: 월 약 1만원
- t3.small: 월 약 2만원
- 스토리지 30GB: 월 약 3천원

> 💡 **팁**: 사용 안 할 때는 인스턴스를 "중지"하면 비용이 거의 안 나가요!

---

## ✅ 체크리스트

배포가 잘 됐는지 확인해보세요:

- [ ] AWS 계정 만들기 완료
- [ ] EC2 인스턴스 만들기 완료
- [ ] 키 파일(.pem) 안전하게 저장
- [ ] SSH로 AWS 접속 성공
- [ ] Docker 설치 완료
- [ ] 프로젝트 파일 전송 완료
- [ ] docker-compose 실행 완료
- [ ] 웹 브라우저로 접속 성공

---

## � 도움이최 필요하면

1. 오류 메시지를 복사해서 검색해보세요
2. AWS 공식 문서: https://docs.aws.amazon.com/ko_kr/
3. 로그 확인: `docker-compose -f deploy/docker-compose.prod.yml logs`
