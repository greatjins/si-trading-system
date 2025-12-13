# 데이터베이스 설정 가이드

## 📊 데이터베이스 선택

### SQLite (기본, 간편)
- **장점**: 설치 불필요, 파일 기반, 간단
- **단점**: 동시 쓰기 제한, 대용량 데이터 처리 느림
- **추천**: 개발 환경, 소규모 데이터

### PostgreSQL (프로덕션)
- **장점**: 고성능, 동시성, 대용량 처리
- **단점**: 별도 설치 필요
- **추천**: 프로덕션 환경, 대규모 데이터

---

## 🚀 PostgreSQL 설정 (Docker)

### 1. Docker 설치
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- 설치 후 Docker Desktop 실행

### 2. PostgreSQL 시작
```bash
# CMD
start_postgres.bat

# PowerShell
.\start_postgres.ps1

# 또는 직접
docker-compose up -d postgres
```

### 3. 연결 확인
```bash
# 로그 확인
docker-compose logs -f postgres

# 상태 확인
docker-compose ps
```

### 4. config.yaml 설정
```yaml
database:
  type: "postgresql"
  host: "127.0.0.1"
  port: 5433
  database: "hts"
  user: "hts_user"
  password: "hts_password_2024"
```

### 5. 마이그레이션 (재무 정보 필드 추가)
```bash
python scripts/migrate_add_financial_fields.py
```

### 6. PostgreSQL 중지
```bash
# CMD
stop_postgres.bat

# 또는 직접
docker-compose down
```

---

## 💾 SQLite 설정

### 1. config.yaml 설정
```yaml
database:
  type: "sqlite"
  path: "data/hts.db"
```

### 2. 마이그레이션 (재무 정보 필드 추가)
```bash
python scripts/migrate_add_financial_fields.py
```

---

## 🔄 데이터베이스 전환

### PostgreSQL → SQLite
```yaml
# config.yaml
database:
  type: "sqlite"
  path: "data/hts.db"
```

### SQLite → PostgreSQL
```yaml
# config.yaml
database:
  type: "postgresql"
  host: "127.0.0.1"
  port: 5433
  database: "hts"
  user: "hts_user"
  password: "hts_password_2024"
```

**주의**: 데이터는 자동으로 마이그레이션되지 않습니다. 필요 시 수동 백업/복원 필요.

---

## 🛠️ 문제 해결

### PostgreSQL 연결 실패
```
ConnectionRefusedError: 대상 컴퓨터에서 연결을 거부했으므로 연결하지 못했습니다
```

**해결 방법:**
1. Docker Desktop이 실행 중인지 확인
2. PostgreSQL 컨테이너 시작: `docker-compose up -d postgres`
3. 포트 충돌 확인: `netstat -ano | findstr :5433`
4. 임시로 SQLite 사용

### 포트 충돌 (5433)
```bash
# 다른 포트로 변경
# docker-compose.yml
ports:
  - "5434:5432"  # 5433 → 5434

# config.yaml
database:
  port: 5434
```

### 데이터 초기화
```bash
# PostgreSQL 데이터 삭제
docker-compose down -v
rm -rf data/postgres

# SQLite 데이터 삭제
rm data/hts.db
```

---

## 📈 성능 비교

| 항목 | SQLite | PostgreSQL |
|------|--------|------------|
| 설치 | 불필요 | Docker 필요 |
| 시작 시간 | 즉시 | 5초 |
| 쓰기 성능 | 보통 | 빠름 |
| 읽기 성능 | 빠름 | 매우 빠름 |
| 동시 접속 | 제한적 | 우수 |
| 데이터 크기 | ~100MB | ~10GB+ |

---

## 🎯 권장 사항

### 개발 환경
```yaml
database:
  type: "sqlite"
  path: "data/hts.db"
```

### 프로덕션 환경
```yaml
database:
  type: "postgresql"
  host: "127.0.0.1"
  port: 5433
  database: "hts"
  user: "hts_user"
  password: "hts_password_2024"
```

### 백테스트 (대량 데이터)
- PostgreSQL 권장
- 인덱스 최적화 필요

### 실시간 트레이딩
- PostgreSQL 권장
- 동시성 처리 우수
