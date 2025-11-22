# LS HTS 플랫폼 재시작 스크립트

Write-Host "🔄 LS HTS 플랫폼 재시작 중..." -ForegroundColor Yellow

# 기존 프로세스 종료
Write-Host "`n⏹️  기존 프로세스 종료 중..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*uvicorn*" -or $_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*vite*"} | Stop-Process -Force

Start-Sleep -Seconds 2

# 백엔드 시작
Write-Host "`n📡 백엔드 서버 시작 (http://localhost:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# 프론트엔드 시작
Write-Host "`n🎨 프론트엔드 서버 시작 (http://localhost:3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Start-Sleep -Seconds 5

Write-Host "`n✅ 재시작 완료!" -ForegroundColor Green
Write-Host "   - 백엔드: http://localhost:8000" -ForegroundColor Yellow
Write-Host "   - 프론트엔드: http://localhost:3000" -ForegroundColor Yellow
Write-Host "   - API 문서: http://localhost:8000/docs" -ForegroundColor Yellow

Start-Process "http://localhost:3000"
