# LS증권 API를 통해 시장 데이터 수집
# 사용법: .\scripts\fetch_market_data.ps1

Write-Host "=== LS증권 시장 데이터 수집 ===" -ForegroundColor Cyan

# Python 가상환경 활성화 (있는 경우)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & venv\Scripts\Activate.ps1
}

# 1. KOSPI 대표 종목 일봉 데이터 (1년치)
Write-Host "`n[1/3] Fetching daily data for major KOSPI stocks..." -ForegroundColor Green
python scripts/fetch_ohlc_data.py --interval 1d --days 365

# 2. 삼성전자 분봉 데이터 (최근 5일)
Write-Host "`n[2/3] Fetching minute data for Samsung Electronics..." -ForegroundColor Green
python scripts/fetch_ohlc_data.py --symbol 005930 --interval 1m --days 5

# 3. 주요 종목 5분봉 데이터 (최근 10일)
Write-Host "`n[3/3] Fetching 5-minute data for major stocks..." -ForegroundColor Green
python scripts/fetch_ohlc_data.py --symbols 005930,000660,035720 --interval 5m --days 10

Write-Host "`n=== 데이터 수집 완료 ===" -ForegroundColor Cyan
Write-Host "PostgreSQL에서 데이터를 확인하세요:" -ForegroundColor Yellow
Write-Host "  psql -h localhost -p 5433 -U hts_user -d hts" -ForegroundColor Gray
Write-Host "  SELECT symbol, interval, COUNT(*) FROM ohlc GROUP BY symbol, interval;" -ForegroundColor Gray
