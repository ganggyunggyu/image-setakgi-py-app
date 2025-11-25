@echo off
REM ============================================
REM Image Setakgi - Windows 빌드 스크립트
REM ============================================

echo ==========================================
echo   Image Setakgi - Windows Build
echo ==========================================

REM 1. 가상환경 생성 (없으면)
if not exist "venv" (
    echo [1/4] 가상환경 생성 중...
    python -m venv venv
) else (
    echo [1/4] 가상환경 이미 존재함
)

REM 2. 가상환경 활성화
echo [2/4] 가상환경 활성화...
call venv\Scripts\activate.bat

REM 3. 의존성 설치
echo [3/4] 의존성 설치 중...
pip install --upgrade pip
pip install -r requirements.txt

REM 4. PyInstaller로 빌드
echo [4/4] 앱 빌드 중...
pyinstaller ^
    --noconfirm ^
    --windowed ^
    --onefile ^
    --name "ImageSetakgi" ^
    --add-data "app;app" ^
    app/main.py

echo.
echo ==========================================
echo   빌드 완료!
echo ==========================================
echo.
echo 실행 파일 위치: dist\ImageSetakgi.exe
echo.
echo 실행 방법:
echo   dist\ImageSetakgi.exe 더블클릭
echo ==========================================

pause
