# ClaraCS 애플리케이션 실행 스크립트 (PowerShell)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "ClaraCS Application Starter" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 가상환경 활성화
Write-Host "[1/3] 가상환경 활성화 중..." -ForegroundColor Yellow
if (Test-Path "..\clara-venv\Scripts\Activate.ps1") {
    & ..\clara-venv\Scripts\Activate.ps1
    Write-Host "✅ 가상환경 활성화 완료" -ForegroundColor Green
} else {
    Write-Host "❌ 가상환경을 찾을 수 없습니다: ..\clara-venv" -ForegroundColor Red
    Write-Host "가상환경을 먼저 생성하세요:" -ForegroundColor Yellow
    Write-Host "  python -m venv ..\clara-venv" -ForegroundColor White
    exit 1
}

Write-Host ""

# 환경 변수 확인
Write-Host "[2/3] 환경 설정 확인 중..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env 파일 존재" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env 파일이 없습니다. 기본 설정으로 실행됩니다." -ForegroundColor Yellow
}

Write-Host ""

# Flask 앱 실행
Write-Host "[3/3] Flask 서버 시작 중..." -ForegroundColor Yellow
Write-Host "서버 주소: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "종료: Ctrl + C" -ForegroundColor Cyan
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

python app.py

