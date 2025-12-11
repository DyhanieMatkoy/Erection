@echo off
echo Starting Desktop Application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start application
    echo Make sure you ran Setup.bat first
    pause
)
