@echo off
REM Build Production API Server
echo ========================================
echo Building Production API Server
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

REM Check if production environment file exists
if not exist .env.production (
    echo.
    echo WARNING: .env.production not found!
    echo Creating from .env template...
    copy .env .env.production
    echo.
    echo IMPORTANT: Edit .env.production and set:
    echo   - JWT_SECRET_KEY to a secure random value
    echo   - CORS_ORIGINS to your production domain
    echo.
    pause
)

REM Install/update dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Run tests if they exist
if exist api\testsx (
    echo.
    echo Running API tests...
    python -m pytest api/tests -v
    if errorlevel 1 (
        echo.
        echo Tests failed! Fix errors before deploying to production.
        pause
        exit /b 1
    )
)

REM Create production build info
echo.
echo Creating build info...
echo Build Date: %date% %time% > api_build_info.txt
echo Python Version: >> api_build_info.txt
python --version >> api_build_info.txt

echo.
echo ========================================
echo Production API Build Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review .env.production settings
echo 2. Test with: start_api_production.bat
echo 3. Deploy api/ folder and dependencies
echo.
echo To start production server:
echo   start_api_production.bat
echo.
pause
