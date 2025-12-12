@echo off
REM Start API and Web Client (Built for Production-like usage)
echo ========================================
echo Starting Client + Server
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

REM Build Web Client if needed or forced
if "%1"=="--rebuild" (
    echo Rebuilding Web Client...
    cd web-client
    call npm install
    call npm run build
    cd ..
) else if not exist "web-client\dist\index.html" (
    echo Web client build not found. Building...
    cd web-client
    call npm install
    call npm run build
    cd ..
)

echo.
echo Starting Server on http://localhost:8000...
echo.

python start_server.py

pause
