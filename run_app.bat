@echo off
REM ClaraCS 애플리케이션 실행 스크립트 (CMD)

echo ==================================
echo ClaraCS Application Starter
echo ==================================
echo.

REM 가상환경 활성화
echo [1/3] 가상환경 활성화 중...
if exist ..\clara-venv\Scripts\activate.bat (
    call ..\clara-venv\Scripts\activate.bat
    echo ✅ 가상환경 활성화 완료
) else (
    echo ❌ 가상환경을 찾을 수 없습니다: ..\clara-venv
    echo 가상환경을 먼저 생성하세요:
    echo   python -m venv ..\clara-venv
    exit /b 1
)

echo.

REM 환경 변수 확인
echo [2/3] 환경 설정 확인 중...
if exist .env (
    echo ✅ .env 파일 존재
) else (
    echo ⚠️  .env 파일이 없습니다. 기본 설정으로 실행됩니다.
)

echo.

REM Flask 앱 실행
echo [3/3] Flask 서버 시작 중...
echo 서버 주소: http://127.0.0.1:5000
echo 종료: Ctrl + C
echo.
echo ==================================
echo.

python app.py

