# 시장 데이터 수집 통합 스크립트
# 
# 실행 순서:
# 1. 종목 마스터 업데이트 (메타데이터)
# 2. 평균회귀 유니버스 데이터 수집
# 3. 모멘텀 유니버스 데이터 수집

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  시장 데이터 수집 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: 종목 마스터 업데이트
Write-Host "[1/3] 종목 마스터 업데이트 중..." -ForegroundColor Yellow
python scripts/update_stock_master.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "종목 마스터 업데이트 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 종목 마스터 업데이트 완료" -ForegroundColor Green
Write-Host ""

# Step 2: 평균회귀 전략 유니버스 수집
Write-Host "[2/3] 평균회귀 전략 데이터 수집 중..." -ForegroundColor Yellow
python scripts/fetch_ohlc_data.py --strategy mean_reversion --days 180

if ($LASTEXITCODE -ne 0) {
    Write-Host "평균회귀 데이터 수집 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 평균회귀 데이터 수집 완료" -ForegroundColor Green
Write-Host ""

# Step 3: 모멘텀 전략 유니버스 수집
Write-Host "[3/3] 모멘텀 전략 데이터 수집 중..." -ForegroundColor Yellow
python scripts/fetch_ohlc_data.py --strategy momentum --days 180

if ($LASTEXITCODE -ne 0) {
    Write-Host "모멘텀 데이터 수집 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 모멘텀 데이터 수집 완료" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  데이터 수집 완료!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
