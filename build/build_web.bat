@echo off
REM Build script for web client
echo ========================================
echo Building Web Client
echo ========================================

cd web-client

REM Check if node_modules exists or if dependencies need updating
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install dependencies
        cd ..
        exit /b 1
    )
) else (
    echo Checking dependencies...
    call npm install --no-save >nul 2>&1
)

REM Build the web client
echo Building production bundle...
call npm run build
if errorlevel 1 (
    echo Build failed
    cd ..
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Output: web-client\dist
echo ========================================

cd ..
