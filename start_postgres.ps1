#!/usr/bin/env pwsh
# PostgreSQL 시작 스크립트 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 시작 (Docker)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Docker 실행 확인
try {
    docker info | Out-Null
} catch {
    Write-Host "[ERROR] Docker가 실행되지 않았습니다." -ForegroundColor Red
    Write-Host "Docker Desktop을 먼저 실행해주세요." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] PostgreSQL 컨테이너 시작 중..." -ForegroundColor Green
docker-compose up -d postgres

Write-Host ""
Write-Host "[2/3] PostgreSQL 연결 대기 중..." -ForegroundColor Green
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "[3/3] PostgreSQL 상태 확인..." -ForegroundColor Green
docker-compose ps postgres

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 시작 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "연결 정보:" -ForegroundColor Yellow
Write-Host "  Host: 127.0.0.1"
Write-Host "  Port: 5433"
Write-Host "  Database: hts"
Write-Host "  User: hts_user"
Write-Host "  Password: hts_password_2024"
Write-Host ""
Write-Host "중지: docker-compose down" -ForegroundColor Cyan
Write-Host "로그: docker-compose logs -f postgres" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
