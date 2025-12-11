@echo off
REM Start both backend and frontend servers for E2E testing

echo Starting E2E test servers...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Check if Node is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    exit /b 1
)

echo Setting up test database...
cd ..
python api\tests\setup_test_db.py
if errorlevel 1 (
    echo ERROR: Failed to setup test database
    exit /b 1
)

echo.
echo Starting backend API server on port 8000...
start "Backend API" cmd /k "python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting frontend dev server on port 5173...
cd web-client
start "Frontend Dev" cmd /k "npm run dev"

echo.
echo ========================================
echo E2E Test Servers Started
echo ========================================
echo Backend API: http://localhost:8000
echo Frontend:    http://localhost:5173
echo API Docs:    http://localhost:8000/docs
echo.
echo To run E2E tests, open a new terminal and run:
echo   cd web-client
echo   npm run test:e2e
echo.
echo Press any key to stop servers...
pause >nul

echo Stopping servers...
taskkill /FI "WindowTitle eq Backend API*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend Dev*" /T /F >nul 2>&1

echo Servers stopped.
