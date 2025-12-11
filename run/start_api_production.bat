@echo off
REM Start API Server in Production Mode
echo ========================================
echo Starting API Server (Production Mode)
echo ========================================

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found!
    pause
    exit /b 1
)

REM Check if production env exists
if not exist .env.production (
    echo ERROR: .env.production not found!
    echo Run build_production_api.bat first
    pause
    exit /b 1
)

REM Copy production env to .env
copy /Y .env.production .env

REM Start API server without reload (production mode)
echo.
echo API Server: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Running in PRODUCTION mode (no auto-reload)
echo Press Ctrl+C to stop the server
echo ========================================

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

pause
