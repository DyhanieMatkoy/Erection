@echo off
echo ========================================
echo Construction Time Management - Web Server
echo ========================================
echo.
echo Starting server...
echo.
echo API Server: http://localhost:8000/api
echo Web Client: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop.
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
