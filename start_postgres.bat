@echo off
echo ========================================
echo PostgreSQL 시작 (Docker)
echo ========================================
echo.

REM Docker가 실행 중인지 확인
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker가 실행되지 않았습니다.
    echo Docker Desktop을 먼저 실행해주세요.
    pause
    exit /b 1
)

echo [1/3] PostgreSQL 컨테이너 시작 중...
docker-compose up -d postgres

echo.
echo [2/3] PostgreSQL 연결 대기 중...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] PostgreSQL 상태 확인...
docker-compose ps postgres

echo.
echo ========================================
echo PostgreSQL 시작 완료!
echo ========================================
echo.
echo 연결 정보:
echo   Host: 127.0.0.1
echo   Port: 5433
echo   Database: hts
echo   User: hts_user
echo   Password: hts_password_2024
echo.
echo 중지: docker-compose down
echo 로그: docker-compose logs -f postgres
echo.
pause
