@echo off
chcp 65001 >nul
echo ========================================
echo AutoDoor Behavior Tree - DD Build
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python environment...
python --version
if errorlevel 1 (
    echo Error: Python not found!
    pause
    exit /b 1
)

echo.
echo Checking required modules...
python -c "import customtkinter; import pytesseract; import pygame; import PIL; print('All modules OK')"
if errorlevel 1 (
    echo Error: Required modules not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Checking DD64.dll...
if not exist "drivers\DD64.dll" (
    echo Warning: DD64.dll not found in drivers folder!
    echo DD input will not work without this file.
)

echo.
echo Starting PyInstaller build (DD version)...
pyinstaller autodoor_bt_dd.spec --clean

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Output: dist\autodoor-bt-*-game\
echo ========================================
pause
