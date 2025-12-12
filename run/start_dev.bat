@echo off
REM Development mode startup script (API + Client dev server)
echo ========================================
echo Starting Development Environment
echo ========================================

REM Check if virtual environment exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Running setup...
    call setup.bat
    if errorlevel 1 (
        echo Setup failed
        exit /b 1
    )
    call .venv\Scripts\activate.bat
)

echo.
echo Starting API server on http://localhost:8000
echo Starting Web dev server on http://localhost:5173
echo.
echo API docs available at http://localhost:8000/docs
echo Web client available at http://localhost:5173
echo.
echo Press Ctrl+C to stop the servers
echo ========================================
echo.

REM Start both servers in separate windows
start "API Server" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "Web Dev Server" cmd /k "cd web-client && npm run dev"

echo.
echo Servers started in separate windows
echo Close the windows to stop the servers
