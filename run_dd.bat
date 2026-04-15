@echo off
cd /d "%~dp0"
set AUTODOOR_USE_DD=1
echo Environment variable set: AUTODOOR_USE_DD=1
echo.
echo Checking DD64.dll...
if exist "drivers\DD64.dll" (
    echo DD64.dll found
) else (
    echo Warning: DD64.dll not found
)
echo.
echo Starting application...
python main.py
pause
