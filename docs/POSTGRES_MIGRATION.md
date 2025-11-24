# PostgreSQL 마이그레이션 가이드

## 개요
SQLite에서 PostgreSQL로 마이그레이션하여 실시간 트레이딩과 데이터 수집의 동시 실행을 지원합니다.

## 마이그레이션 이유
- ✅ 동시 쓰기 지원 (실시간 트레이딩 + 데이터 수집)
- ✅ 트랜잭션 안정성
- ✅ 확장성 보장
- ✅ 성능 향상

## 사전 준비

### 1. Docker 설치 확인
```powershell
docker --version
docker-compose --version
```

Docker가 없다면: https://www.docker.com/products/docker-desktop

### 2. Python 패키지 설치
```powershell
pip install -r requirements.txt
```

## 마이그레이션 단계

### Step 1: PostgreSQL 시작
```powershell
# Docker Compose로 PostgreSQL + Redis 시작
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs postgres
```

### Step 2: 데이터베이스 연결 확인
```powershell
# PostgreSQL 접속 테스트
docker exec -it hts-postgres psql -U hts_user -d hts

# psql 프롬프트에서
\l          # 데이터베이스 목록
\dt         # 테이블 목록 (아직 비어있음)
\q          # 종료
```

### Step 3: 데이터 마이그레이션 실행
```powershell
# 마이그레이션 스크립트 실행
python scripts/migrate_to_postgres.py
```

**출력 예시**:
```
============================================================
SQLite → PostgreSQL Migration
============================================================
✓ Backup created: data/hts.db.backup_20251123_180000
Connecting to databases...
✓ PostgreSQL connected: PostgreSQL 15.5
Creating PostgreSQL tables...
✓ Tables created
Starting data migration...
Migrating users...
✓ Migrated 2 records from users
Migrating accounts...
✓ Migrated 1 records from accounts
✓ Data migration completed
Verifying migration...
Users - SQLite: 2, PostgreSQL: 2
✓ Verification passed
============================================================
✓ Migration completed successfully!
============================================================
```

### Step 4: 애플리케이션 재시작
```powershell
# 서버 재시작 (자동으로 PostgreSQL 사용)
.\restart.ps1
```

## 확인 사항

### 1. 데이터베이스 연결 확인
로그에서 다음 메시지 확인:
```
INFO - Database connected: postgresql://hts_user:***@localhost:5432/hts
```

### 2. 데이터 확인
```powershell
# PostgreSQL 접속
docker exec -it hts-postgres psql -U hts_user -d hts

# 데이터 확인
SELECT * FROM users;
SELECT * FROM accounts;
```

### 3. 웹 UI 확인
- http://localhost:3000 접속
- 로그인 테스트
- 계좌 정보 조회 테스트

## 롤백 (문제 발생 시)

### Option 1: SQLite로 되돌리기
```yaml
# config.yaml 수정
database:
  type: "sqlite"
  path: "data/hts.db"
```

### Option 2: 백업에서 복원
```powershell
# 백업 파일 확인
dir data\hts.db.backup_*

# 복원
copy data\hts.db.backup_20251123_180000 data\hts.db
```

## Docker 관리 명령어

### 시작/중지
```powershell
# 시작
docker-compose up -d

# 중지
docker-compose stop

# 완전 삭제 (데이터 포함)
docker-compose down -v
```

### 로그 확인
```powershell
# 전체 로그
docker-compose logs

# PostgreSQL 로그만
docker-compose logs postgres

# 실시간 로그
docker-compose logs -f
```

### 데이터 백업
```powershell
# PostgreSQL 덤프
docker exec hts-postgres pg_dump -U hts_user hts > backup.sql

# 복원
docker exec -i hts-postgres psql -U hts_user hts < backup.sql
```

## 성능 최적화

### 인덱스 추가 (필요시)
```sql
-- 종목 코드 인덱스
CREATE INDEX idx_stock_symbol ON stock_info(symbol);

-- 거래 날짜 인덱스
CREATE INDEX idx_trade_timestamp ON trades(timestamp);

-- 백테스트 날짜 인덱스
CREATE INDEX idx_backtest_date ON backtest_results(created_at);
```

### 연결 풀 설정
`api/dependencies.py`에서 이미 설정됨:
- pool_size: 10
- max_overflow: 20
- pool_recycle: 3600 (1시간)

## 문제 해결

### 1. "connection refused" 오류
```powershell
# PostgreSQL 상태 확인
docker-compose ps

# 재시작
docker-compose restart postgres
```

### 2. "password authentication failed" 오류
- `config.yaml`의 비밀번호 확인
- `docker-compose.yml`의 비밀번호와 일치하는지 확인

### 3. "database does not exist" 오류
```powershell
# 데이터베이스 재생성
docker-compose down
docker-compose up -d
```

## 참고 자료
- PostgreSQL 공식 문서: https://www.postgresql.org/docs/
- SQLAlchemy 문서: https://docs.sqlalchemy.org/
- Docker Compose 문서: https://docs.docker.com/compose/
