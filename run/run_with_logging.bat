@echo off
echo Starting application with detailed logging...
echo.
echo If you see errors, they will be displayed below:
echo ============================================================
python main.py 2>&1
echo ============================================================
echo.
pause
