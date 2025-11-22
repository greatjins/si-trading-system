# LS HTS 플랫폼 시작 스크립트 (PowerShell)

Write-Host "🚀 LS HTS 플랫폼 시작 중..." -ForegroundColor Green

# 백엔드 시작
Write-Host "`n📡 백엔드 서버 시작 (http://localhost:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

# 잠시 대기 (백엔드 시작 시간)
Start-Sleep -Seconds 3

# 프론트엔드 시작
Write-Host "`n🎨 프론트엔드 서버 시작 (http://localhost:3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

# 잠시 대기 후 브라우저 열기
Start-Sleep -Seconds 5
Write-Host "`n✅ 서버 시작 완료!" -ForegroundColor Green
Write-Host "   - 백엔드: http://localhost:8000" -ForegroundColor Yellow
Write-Host "   - 프론트엔드: http://localhost:3000" -ForegroundColor Yellow
Write-Host "   - API 문서: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "`n🌐 브라우저를 여는 중..." -ForegroundColor Cyan

Start-Process "http://localhost:3000"

Write-Host "`n💡 종료하려면 각 터미널 창을 닫으세요." -ForegroundColor Gray
