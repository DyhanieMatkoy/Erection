@echo off
REM Start Desktop Application (PyQt6)
echo ========================================
echo Starting Desktop Application
echo ========================================

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Start main application
python main.py

pause
