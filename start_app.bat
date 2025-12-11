@echo off
echo ========================================
echo Starting Application (Backend + Frontend)
echo ========================================
echo.

REM Kill processes using port 8000 (Backend)
echo Stopping processes on port 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000
    taskkill /F /PID %%a 2>nul
)

REM Kill processes using port 5173 (Frontend - Vite default)
echo Stopping processes on port 5173 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo Killing process %%a on port 5173
    taskkill /F /PID %%a 2>nul
)

REM Kill processes using port 3000 (Frontend - alternative)
echo Stopping processes on port 3000 (Frontend alternative)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 3000
    taskkill /F /PID %%a 2>nul
)

echo.
echo Ports cleared. Starting servers...
echo.

REM Start Backend
echo Starting Backend Server (Port 8000)...
start "Backend Server" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a bit for backend to initialize
timeout /t 3 /nobreak >nul

REM Start Frontend
echo Starting Frontend Server (Port 5173)...
start "Frontend Server" cmd /k "cd /d %~dp0web-client && npm run dev"

echo.
echo ========================================
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to exit this window (servers will continue running)
pause >nul
