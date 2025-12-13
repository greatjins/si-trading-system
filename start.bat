@echo off
REM HTS 플랫폼 시작 스크립트 (CMD)

echo ========================================
echo    HTS 플랫폼 시작
echo ========================================
echo.

REM 백엔드 시작
echo [1/2] 백엔드 서버 시작 중...
start "HTS Backend" cmd /k "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

REM 잠시 대기
timeout /t 3 /nobreak >nul

REM 프론트엔드 시작
echo [2/2] 프론트엔드 서버 시작 중...
start "HTS Frontend" cmd /k "cd frontend && npm run dev"

REM 잠시 대기 후 브라우저 열기
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    서버 시작 완료!
echo ========================================
echo    - 백엔드: http://localhost:8000
echo    - 프론트엔드: http://localhost:3000
echo    - API 문서: http://localhost:8000/docs
echo ========================================
echo.

REM 브라우저 열기
start http://localhost:3000

echo 브라우저가 열립니다...
echo 종료하려면 각 터미널 창을 닫으세요.
echo.
pause
