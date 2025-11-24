# PostgreSQL Setup Script
# Encoding: UTF-8

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Migration Start" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Docker not installed" -ForegroundColor Red
    Write-Host "  Install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}
Write-Host "OK Docker installed: $dockerVersion" -ForegroundColor Green
Write-Host ""

# Step 2: Install Python packages
Write-Host "[2/5] Installing Python packages..." -ForegroundColor Yellow
pip install psycopg2-binary alembic pyyaml -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Packages installed" -ForegroundColor Green
} else {
    Write-Host "X Package installation failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Start Docker Compose
Write-Host "[3/5] Starting PostgreSQL container..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Container started" -ForegroundColor Green
} else {
    Write-Host "X Container start failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Wait for PostgreSQL
Write-Host "[4/5] Waiting for PostgreSQL..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0
$ready = $false

while ($retryCount -lt $maxRetries) {
    $healthCheck = docker exec hts-postgres pg_isready -U hts_user -d hts 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    $retryCount++
    Write-Host "  Waiting... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($ready) {
    Write-Host "OK PostgreSQL ready" -ForegroundColor Green
} else {
    Write-Host "X PostgreSQL timeout" -ForegroundColor Red
    Write-Host "  Check logs: docker-compose logs postgres" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 5: Migrate data
Write-Host "[5/5] Running data migration..." -ForegroundColor Yellow
if (Test-Path "data/hts.db") {
    python scripts/migrate_to_postgres.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK Migration completed" -ForegroundColor Green
    } else {
        Write-Host "X Migration failed" -ForegroundColor Red
        Write-Host "  Check logs for details" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  No SQLite database found. Creating new tables..." -ForegroundColor Yellow
    python -c 'from api.dependencies import engine; from data.models import Base; Base.metadata.create_all(engine)'
    Write-Host "OK Tables created" -ForegroundColor Green
}
Write-Host ""

# Done
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "OK PostgreSQL setup completed!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart server: .\restart.ps1" -ForegroundColor White
Write-Host "2. Open web UI: http://localhost:3000" -ForegroundColor White
Write-Host "3. Connect to PostgreSQL: docker exec -it hts-postgres psql -U hts_user -d hts" -ForegroundColor White
Write-Host ""
Write-Host "Docker management:" -ForegroundColor Yellow
Write-Host "- Stop: docker-compose stop" -ForegroundColor White
Write-Host "- Start: docker-compose start" -ForegroundColor White
Write-Host "- Logs: docker-compose logs -f" -ForegroundColor White
Write-Host ""
