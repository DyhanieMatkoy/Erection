@echo off
echo Testing env.ini reading...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the test script
python test_env_ini.py

echo.
pause
