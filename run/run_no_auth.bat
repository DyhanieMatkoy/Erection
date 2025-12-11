@echo off
echo ========================================
echo  NO AUTHENTICATION MODE
echo  Login/Password check BYPASSED
echo ========================================
echo.

REM Check if virtual environment exists 
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist venv\Lib\site-packages\PyQt6 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run application without authentication
echo Starting application (No Auth Mode)...
python main_no_auth.py

pause
