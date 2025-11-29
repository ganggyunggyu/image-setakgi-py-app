@echo off
REM ============================================
REM Image Setakgi - Windows Build Script
REM ============================================

echo ==========================================
echo   Image Setakgi - Windows Build
echo ==========================================

REM 1. Create virtual environment (if not exists)
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment already exists
)

REM 2. Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM 3. Install dependencies
echo [3/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM 4. Build with PyInstaller
echo [4/4] Building app...
pyinstaller ^
    --noconfirm ^
    --windowed ^
    --onefile ^
    --name "ImageSetakgi" ^
    --add-data "app;app" ^
    app/main.py

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo.
echo Executable location: dist\ImageSetakgi.exe
echo.
echo How to run:
echo   Double-click dist\ImageSetakgi.exe
echo ==========================================

pause
