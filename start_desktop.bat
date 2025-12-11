@echo off
echo Starting Desktop Application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start application
    pause
)
