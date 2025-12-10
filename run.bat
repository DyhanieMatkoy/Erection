@echo off
echo Starting Construction Time Management System...

REM Check if virtual environment exists 
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run application .\venv\Scripts\python.exe main.py
echo Starting application...
python main.py

pause
