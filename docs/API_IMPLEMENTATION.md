# LS증권 API 구현 상세

## 구현된 TR 코드

### 1. t8436 - 주식종목조회 API용
**엔드포인트:** `/stock/etc`  
**용도:** 전체 종목 리스트 조회

```python
# Request
{
    "t8436InBlock": {
        "gubun": "0"  # 0:전체, 1:코스피, 2:코스닥
    }
}

# Response
{
    "t8436OutBlock": [
        {
            "hname": "삼성전자",      # 종목명
            "shcode": "005930",       # 종목코드
            "gubun": "1",             # 1:코스피, 2:코스닥
            "jnilclose": 70000        # 전일가
        }
    ]
}
```

### 2. t1463 - 거래대금상위 ⭐ 핵심
**엔드포인트:** `/stock/high-item`  
**용도:** 거래대금 기준 상위 종목 조회 (필터링 불필요!)

```python
# Request
{
    "t1463InBlock": {
        "gubun": "0",                # 0:전체, 1:코스피, 2:코스닥
        "jnilgubun": "0",            # 0:당일, 1:전일
        "jc_num": "000016778240",    # 대상제외: 거래정지(512)+정리매매(16777216)+불성실공시(2147483648)
        "sprice": 0,                 # 시작가격 (0:전체)
        "eprice": 0,                 # 종료가격 (0:전체)
        "volume": 0,                 # 거래량 (0:전체)
        "idx": 0,                    # IDX (처음 조회시 0)
        "jc_num2": "000000000015",   # 대상제외2: ETF(1)+선박투자(2)+스펙(4)+ETN(8)
        "exchgubun": "U"             # U:통합
    }
}

# jc_num 제외 옵션 (비트 플래그, 합산 가능)
# - 거래정지: 512 (0x00000200)
# - 정리매매: 16777216 (0x01000000)
# - 불성실공시: 2147483648 (0x80000000)
# 예: 거래정지+정리매매+불성실공시 = 512+16777216+2147483648 = 2164260976

# jc_num2 제외 옵션 (비트 플래그, 합산 가능)
# - ETF: 1
# - 선박투자회사: 2
# - 스펙: 4
# - ETN: 8
# 예: 전체 제외 = 1+2+4+8 = 15
}

# Response
{
    "t1463OutBlock1": [
        {
            "hname": "삼성전자",
            "shcode": "005930",
            "price": 70000,
            "value": 1500000,            # 당일 거래대금 (백만원 단위)
            "jnilvalue": 1200000,        # 전일 거래대금 (백만원 단위) ⭐
            "jnilvolume": 15000000       # 전일 거래량
        }
    ]
}

**주의:** `jnilvalue`는 **백만원 단위**로 반환됩니다.
- 예: 1,200,000 → 1,200,000백만원 = 1조 2천억원
- 코드에서 `x 1,000,000`으로 원 단위 변환 필요
```

**장점:**
- 1회 API 호출로 거래대금 상위 200종목 획득
- 전일 거래대금 기준 정렬
- 1000억 필터링 불필요 (상위만 가져오면 됨)

### 3. t8451 - (통합)주식챠트(일주월년) API용
**엔드포인트:** `/stock/chart`  
**용도:** 일봉/주봉/월봉/년봉 데이터 조회

```python
# Request
{
    "t8451InBlock": {
        "shcode": "005930",
        "gubun": "2",                # 2:일, 3:주, 4:월, 5:년
        "qrycnt": 500,               # 최대 500
        "sdate": "20240601",
        "edate": "20241130",
        "cts_date": "",              # 연속조회시 사용
        "comp_yn": "N",              # N:비압축
        "sujung": "N",               # Y:수정주가, N:원주가
        "exchgubun": "K"             # K:KRX
    }
}

# Response
{
    "t8451OutBlock1": [
        {
            "date": "20241130",
            "open": 70000,
            "high": 71000,
            "low": 69500,
            "close": 70500,
            "jdiff_vol": 15234567,      # 거래량
            "value": 1500000000000      # 거래대금
        }
    ]
}
```

**특징:**
- 최대 500개 조회 가능
- 6개월 = 약 120일 → 1회 조회로 충분
- 거래대금(`value`) 포함 (별도 계산 불필요)

### 4. t8452 - (통합)주식챠트(N분) API용
**엔드포인트:** `/stock/chart`  
**용도:** 분봉 데이터 조회

```python
# Request
{
    "t8452InBlock": {
        "shcode": "005930",
        "ncnt": 5,                   # 분간격 (1, 5, 10, 30, 60)
        "qrycnt": 500,
        "nday": 1,                   # 조회일수
        "comp_yn": "N",
        "exchgubun": "K"
    }
}

# Response
{
    "t8452OutBlock1": [
        {
            "date": "20241130",
            "time": "0935",             # HHMM
            "open": 70000,
            "high": 70200,
            "low": 69900,
            "close": 70100,
            "jdiff_vol": 123456
        }
    ]
}
```

### 5. t1102 - 주식현재가시세조회
**엔드포인트:** `/stock/market-data`  
**용도:** 실시간 현재가 조회

```python
# Request
{
    "t1102InBlock": {
        "shcode": "005930"
    }
}

# Response
{
    "t1102OutBlock": {
        "hname": "삼성전자",
        "price": 70500,
        "change": 500,
        "drate": 0.71,
        "volume": 15234567,
        "open": 70000,
        "high": 71000,
        "low": 69500,
        "jnilclose": 70000
    }
}
```

---

## 최적화된 데이터 수집 흐름

### 기존 방식 (비효율)
```
1. 전체 종목 조회 (2,300개) → t8436
2. 각 종목 현재가 조회 (2,300회) → t1102
3. 거래대금 계산 및 필터링
4. 선별된 종목 일봉 조회 (200회) → t8451

총 API 호출: 2,501회
```

### 새 방식 (효율) ⭐
```
1. 거래대금 상위 200종목 조회 (1회) → t1463
2. 선별된 종목 일봉 조회 (200회) → t8451

총 API 호출: 201회 (92% 감소!)
```

---

## 구현 코드 위치

### 1. 시세 서비스 (`broker/ls/services/market.py`)
```python
class LSMarketService:
    async def get_all_symbols()           # t8436
    async def get_top_volume_stocks()     # t1463 ⭐
    async def get_current_price()         # t1102
    async def get_daily_ohlc()            # t8451
    async def get_minute_ohlc()           # t8452
```

### 2. 종목 마스터 업데이트 (`scripts/update_stock_master.py`)
```python
# 거래대금 상위 200종목으로 마스터 구축
await update_stock_master_from_top_volume(count=200)
```

### 3. 데이터 수집 (`scripts/fetch_ohlc_data.py`)
```python
# 전략별 유니버스 기반 수집
await fetch_by_universe(strategy_type="mean_reversion", days=180)
```

---

## 실행 방법

### 1. 종목 마스터 업데이트
```bash
# 거래대금 상위 200종목
python scripts/update_stock_master.py --count 200

# 거래대금 상위 500종목
python scripts/update_stock_master.py --count 500
```

### 2. 데이터 수집
```bash
# 평균회귀 전략 (저점 매수)
python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180

# 모멘텀 전략 (추세 추종)
python scripts/fetch_ohlc_data.py --strategy momentum --days 180
```

### 3. 통합 실행
```powershell
.\scripts\collect_market_data.ps1
```

---

## API Rate Limit

- **t8436**: 초당 2건
- **t1463**: 초당 1건
- **t8451**: 초당 1건
- **t8452**: 초당 1건
- **t1102**: 초당 1건

**대응:**
- 각 API 호출 후 `await asyncio.sleep(0.1)` (100ms 대기)
- 200종목 수집 시 약 20초 소요

---

## 데이터 품질

### 거래대금 기준
- **t1463**: 전일 거래대금 (`jnilvalue`)
- 장 마감 후 확정된 값
- 정확한 필터링 가능

### OHLC 데이터
- **t8451**: 원주가 기준 (`sujung="N"`)
- 수정주가 필요시 `sujung="Y"` 설정
- 거래대금 포함 (`value`)

---

## 다음 단계

1. ✅ API 구현 완료
2. ✅ 최적화된 수집 흐름
3. ⏳ 실제 데이터 수집 테스트
4. ⏳ 백테스트 엔진 연동
