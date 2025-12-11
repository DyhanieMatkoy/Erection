@echo off
REM Startup script for web application (API + Client)
echo ========================================
echo Starting Construction Management System
echo ========================================

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Running setup...
    call setup.bat
    if errorlevel 1 (
        echo Setup failed
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if web client is built
if not exist "web-client\dist\index.html" (
    echo Web client not built. Building...
    call build_web.bat
    if errorlevel 1 (
        echo Build failed
        exit /b 1
    )
)

echo.
echo Starting API server on http://localhost:8000
echo Web client will be served at http://localhost:8000
echo API docs available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the API server with static file serving
python start_server.py
