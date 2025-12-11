@echo off
echo Starting Construction Time Management System (DEBUG MODE)...
echo.

REM Check if virtual environment exists 
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run run.bat first to create it.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Show current directory
echo Current directory: %CD%
echo.

REM Check for env.ini
if exist env.ini (
    echo [OK] env.ini found
    echo Contents:
    type env.ini
    echo.
) else (
    echo [WARNING] env.ini not found in current directory
    echo.
)

REM Run application with Python unbuffered output
echo Starting application...
echo ============================================================
python -u main.py

pause
