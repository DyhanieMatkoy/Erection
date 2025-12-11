@echo off
REM Quick deployment script for Windows
REM Construction Time Management System

echo ========================================
echo Production Deployment Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if configuration exists
if not exist deploy_config.ini (
    echo.
    echo Configuration file not found!
    echo Creating from example...
    copy deploy_config.ini.example deploy_config.ini
    echo.
    echo IMPORTANT: Edit deploy_config.ini with your settings before continuing!
    echo.
    echo Press any key to open the configuration file...
    pause >nul
    notepad deploy_config.ini
    echo.
    echo After editing, run this script again.
    pause
    exit /b 0
)

REM Show menu
echo Select deployment option:
echo.
echo 1. Full deployment (all components)
echo 2. Database migration only
echo 3. Build web client only
echo 4. Build desktop app only
echo 5. Build API server only
echo 6. Configure components only
echo 7. Exit
echo.
set /p "CHOICE=Enter choice (1-7): "

if "%CHOICE%"=="1" (
    echo.
    echo Running full deployment...
    python deploy.py --all
) else if "%CHOICE%"=="2" (
    echo.
    echo Running database migration...
    python deploy.py --migrate
) else if "%CHOICE%"=="3" (
    echo.
    echo Building web client...
    python deploy.py --build-web
) else if "%CHOICE%"=="4" (
    echo.
    echo Building desktop application...
    python deploy.py --build-desktop
) else if "%CHOICE%"=="5" (
    echo.
    echo Building API server...
    python deploy.py --build-api
) else if "%CHOICE%"=="6" (
    echo.
    echo Configuring components...
    python deploy.py --configure
) else if "%CHOICE%"=="7" (
    echo.
    echo Exiting...
    exit /b 0
) else (
    echo.
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
echo ========================================
if %errorlevel% equ 0 (
    echo Deployment completed successfully!
    echo.
    echo Output directory: output\
    echo.
    echo Check output\README.md for deployment instructions
) else (
    echo Deployment failed!
    echo.
    echo Check deploy.log for details
)
echo ========================================
echo.
pause
