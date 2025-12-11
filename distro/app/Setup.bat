@echo off
echo ========================================
echo Setup - Construction Time Management
echo ========================================
echo.
echo This will install Python dependencies...
echo.
pause

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.11 or later
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies from local packages...
pip install --no-index --find-links=python-packages -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Setup Complete!
    echo ========================================
    echo.
    echo You can now run the application:
    echo   - Desktop: StartDesktop.bat
    echo   - Web Server: StartServer.bat
    echo.
) else (
    echo.
    echo ERROR: Installation failed!
    echo Try installing from internet: pip install -r requirements.txt
    echo.
)
pause
