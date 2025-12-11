@echo off
REM Start API Server Only
echo ========================================
echo Starting API Server
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

REM Start API server using uvicorn directly
echo.
echo API Server: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause
