@echo off
echo ========================================
echo Construction Time Management - Web Server
echo ========================================
echo.
echo Starting server...
echo.
echo API Server: http://localhost:8000
echo Web Client: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
python start_server.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start server
    echo Make sure you ran Setup.bat first
    pause
)
