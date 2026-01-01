# Windows용 빠른 배포 스크립트
# 사용법: .\deploy\quick-deploy.ps1 -AwsIp "1.2.3.4" -KeyPath "C:\keys\my-key.pem"

param(
    [Parameter(Mandatory=$true)]
    [string]$AwsIp,
    
    [Parameter(Mandatory=$true)]
    [string]$KeyPath,
    
    [string]$RemoteUser = "ubuntu",
    
    [string]$RemotePath = "~/ls-hts",
    
    [string[]]$Files,
    
    [switch]$All,
    
    [switch]$NoRestart
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "🚀 LS증권 HTS 빠른 배포" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# SSH 연결 테스트
Write-Host "🔗 SSH 연결 테스트..." -ForegroundColor Yellow
try {
    $result = ssh -i $KeyPath -o ConnectTimeout=10 $RemoteUser@$AwsIp "echo 'connected'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH 연결 실패"
    }
    Write-Host "✅ SSH 연결 성공" -ForegroundColor Green
} catch {
    Write-Host "❌ SSH 연결 실패. 키 파일과 IP 주소를 확인하세요." -ForegroundColor Red
    exit 1
}

if ($All) {
    # 전체 프로젝트 동기화
    Write-Host ""
    Write-Host "📦 전체 프로젝트 동기화 중..." -ForegroundColor Yellow
    
    # rsync가 없으면 scp 사용
    $hasRsync = Get-Command rsync -ErrorAction SilentlyContinue
    
    if ($hasRsync) {
        rsync -avz --delete `
            -e "ssh -i $KeyPath" `
            --exclude='.git' `
            --exclude='node_modules' `
            --exclude='__pycache__' `
            --exclude='.pytest_cache' `
            --exclude='data/postgres' `
            --exclude='data/redis' `
            --exclude='frontend/node_modules' `
            --exclude='*.pyc' `
            --exclude='.env' `
            ./ $RemoteUser@${AwsIp}:${RemotePath}/
    } else {
        Write-Host "⚠️  rsync가 없어 주요 폴더만 전송합니다." -ForegroundColor Yellow
        
        # 주요 폴더 전송
        $folders = @("api", "core", "broker", "data", "utils", "deploy")
        foreach ($folder in $folders) {
            if (Test-Path $folder) {
                Write-Host "  📤 $folder/" -ForegroundColor Gray
                scp -i $KeyPath -r $folder $RemoteUser@${AwsIp}:${RemotePath}/
            }
        }
        
        # 루트 파일 전송
        $rootFiles = @("requirements.txt", "pyproject.toml", "Dockerfile")
        foreach ($file in $rootFiles) {
            if (Test-Path $file) {
                Write-Host "  📤 $file" -ForegroundColor Gray
                scp -i $KeyPath $file $RemoteUser@${AwsIp}:${RemotePath}/
            }
        }
    }
    
    Write-Host "✅ 전체 동기화 완료" -ForegroundColor Green
    
} elseif ($Files -and $Files.Count -gt 0) {
    # 지정된 파일만 배포
    Write-Host ""
    Write-Host "📤 파일 배포 중..." -ForegroundColor Yellow
    
    foreach ($file in $Files) {
        if (Test-Path $file) {
            $targetPath = "$RemotePath/" + (Split-Path $file -Parent).Replace("\", "/")
            Write-Host "  📄 $file -> $targetPath/" -ForegroundColor Gray
            scp -i $KeyPath $file $RemoteUser@${AwsIp}:$targetPath/
        } else {
            Write-Host "  ⚠️  파일 없음: $file" -ForegroundColor Yellow
        }
    }
    
    Write-Host "✅ 파일 배포 완료" -ForegroundColor Green
    
} else {
    # 기본: 자주 수정되는 파일들
    Write-Host ""
    Write-Host "📤 기본 파일 배포 중..." -ForegroundColor Yellow
    
    $defaultFiles = @(
        "api/routes/strategy_builder.py",
        "api/routes/backtest.py",
        "api/routes/backtest_results.py",
        "core/backtest/engine.py",
        "core/backtest/metrics.py"
    )
    
    foreach ($file in $defaultFiles) {
        if (Test-Path $file) {
            $targetPath = "$RemotePath/" + (Split-Path $file -Parent).Replace("\", "/")
            Write-Host "  📄 $file" -ForegroundColor Gray
            scp -i $KeyPath $file $RemoteUser@${AwsIp}:$targetPath/
        }
    }
    
    Write-Host "✅ 기본 파일 배포 완료" -ForegroundColor Green
}

# 앱 재시작
if (-not $NoRestart) {
    Write-Host ""
    Write-Host "🔄 앱 재시작 중..." -ForegroundColor Yellow
    ssh -i $KeyPath $RemoteUser@$AwsIp "cd $RemotePath && docker-compose -f deploy/docker-compose.prod.yml restart app"
    Write-Host "✅ 앱 재시작 완료" -ForegroundColor Green
}

# 헬스 체크
Write-Host ""
Write-Host "🏥 헬스 체크 중..." -ForegroundColor Yellow

$maxRetries = 10
$retryCount = 0
$isHealthy = $false

while ($retryCount -lt $maxRetries) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://$AwsIp/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $isHealthy = $true
            break
        }
    } catch {
        Write-Host -NoNewline "." -ForegroundColor Gray
    }
    $retryCount++
}

Write-Host ""

if ($isHealthy) {
    Write-Host "✅ 서비스 정상 작동 중" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 배포 완료!" -ForegroundColor Cyan
    Write-Host "🌐 접속: http://$AwsIp" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "⚠️  헬스 체크 실패 (Timeout) - 잠시 후 다시 확인하거나 로그를 확인하세요" -ForegroundColor Red
    exit 1
}
