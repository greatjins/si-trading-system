# 데이터 수집 가이드

## 개요

스마트 데이터 수집 시스템은 3-Tier 아키텍처로 구성되어 있습니다:

```
Tier 1: 종목 마스터 (전체 종목 메타데이터)
  ↓
Tier 2: 전략별 유니버스 (필터링된 200종목)
  ↓
Tier 3: OHLC 데이터 (6개월 일봉)
```

## 필터링 기준

### 공통 필터
- **거래대금**: 1000억원 이상 (유동성 확보)

### 평균회귀 전략 (Mean Reversion)
- 52주 최고가 대비 **50% 이하** (저점 매수)
- 거래대금 1000억 이상
- 최대 200종목

### 모멘텀 전략 (Momentum)
- 52주 최고가 대비 **70% 이상** (고점 근처)
- 거래대금 1000억 이상
- 최대 200종목

## 데이터 수집 방법

### 1. 통합 스크립트 (추천)

```powershell
# 전체 프로세스 자동 실행
.\scripts\collect_market_data.ps1
```

실행 순서:
1. 종목 마스터 업데이트 (메타데이터)
2. 평균회귀 유니버스 데이터 수집 (6개월)
3. 모멘텀 유니버스 데이터 수집 (6개월)

### 2. 개별 스크립트

#### 종목 마스터 업데이트
```bash
# 기본 종목 (KOSPI 200 대표 20종목)
python scripts/update_stock_master.py

# 특정 종목
python scripts/update_stock_master.py --symbols 005930,000660,035720
```

#### 전략별 데이터 수집
```bash
# 평균회귀 전략 (저점 매수)
python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180

# 모멘텀 전략 (추세 추종)
python scripts/fetch_ohlc_data.py --strategy momentum --days 180
```

#### 특정 종목 데이터 수집
```bash
# 일봉 6개월
python scripts/fetch_ohlc_data.py --symbols 005930,000660 --days 180

# 분봉 1개월
python scripts/fetch_ohlc_data.py --symbols 005930 --interval 5m --days 30
```

## 데이터베이스 스키마

### stock_master (종목 마스터)
```sql
symbol          VARCHAR(20)   -- 종목코드
name            VARCHAR(100)  -- 종목명
market          VARCHAR(20)   -- KOSPI/KOSDAQ
current_price   DECIMAL       -- 현재가
volume_amount   BIGINT        -- 거래대금 (원)
high_52w        DECIMAL       -- 52주 최고가
low_52w         DECIMAL       -- 52주 최저가
price_position  FLOAT         -- 현재가 / 52주 최고가
```

### stock_universe (전략별 유니버스)
```sql
strategy_type   VARCHAR(50)   -- mean_reversion, momentum
symbol          VARCHAR(20)   -- 종목코드
rank            INTEGER       -- 우선순위
score           FLOAT         -- 점수
```

### ohlc_data (OHLC 데이터)
```sql
symbol          VARCHAR(20)   -- 종목코드
interval        VARCHAR(10)   -- 1d, 5m, etc
timestamp       TIMESTAMP     -- 시간
open/high/low/close  DECIMAL  -- OHLC
volume          BIGINT        -- 거래량
```

## 데이터 양 추정

### 전체 수집 (비효율)
- KOSPI+KOSDAQ: 2,300종목
- 3년 일봉: 172MB
- 1개월 5분봉: 358MB

### 스마트 수집 (효율)
- 필터링: 200종목 (91% 감소)
- 6개월 일봉: **5MB** (97% 감소)
- API 호출: 400회 (95% 감소)

## 증분 업데이트

기본적으로 증분 업데이트가 활성화되어 있습니다:
- 마지막 데이터 시점 이후만 수집
- 중복 방지 (UNIQUE 제약)
- API 호출 최소화

```bash
# 증분 업데이트 (기본)
python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180

# 전체 재수집
python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180 --no-incremental
```

## 스케줄링

### 일일 업데이트 (장 마감 후)
```bash
# Windows 작업 스케줄러
# 매일 오후 4시 실행
schtasks /create /tn "HTS_DataCollection" /tr "powershell.exe -File C:\path\to\scripts\collect_market_data.ps1" /sc daily /st 16:00
```

### 주간 전체 재수집
```bash
# 매주 일요일 오전 2시
schtasks /create /tn "HTS_FullRefresh" /tr "python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180 --no-incremental" /sc weekly /d SUN /st 02:00
```

## 문제 해결

### API Rate Limit 초과
- 증상: HTTP 429 에러
- 해결: `asyncio.sleep(0.1)` 조정 (더 길게)

### 토큰 만료
- 증상: HTTP 401 에러
- 해결: `data/ls_token.json` 삭제 후 재실행

### DB 연결 실패
- 증상: Connection refused
- 해결: PostgreSQL 실행 확인 (`docker-compose up -d`)

## 성능 최적화

### 배치 저장
- `save_ohlc_batch()` 사용 (단일 저장보다 10배 빠름)

### 병렬 처리
- 여러 종목 동시 수집 (향후 구현)

### 캐싱
- 메모리 캐시 (향후 구현)

## 다음 단계

1. ✅ 종목 마스터 업데이트
2. ✅ 유니버스 생성
3. ✅ OHLC 데이터 수집
4. ⏳ 백테스트 실행
5. ⏳ 전략 최적화
