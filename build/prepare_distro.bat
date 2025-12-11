@echo off
REM ============================================================================
REM Master Distribution Preparation Script
REM Construction Time Management System
REM ============================================================================

echo ============================================
echo Distribution Preparation Wizard
echo Construction Time Management System
echo ============================================
echo.
echo This script will help you create a complete offline distribution package.
echo.
echo Prerequisites:
echo - Internet connection (for downloading packages)
echo - Python installed with pip
echo - Node.js installed with npm
echo.
pause

REM Step 1: Build the application
echo.
echo ============================================
echo Step 1: Building Application
echo ============================================
echo.
echo Building web client...
call build_web.bat
if %errorlevel% neq 0 (
    echo WARNING: Web build failed
    echo Continue anyway? (Y/N)
    set /p "CONTINUE="
    if /i not "%CONTINUE%"=="Y" exit /b 1
)

echo.
echo Building desktop application...
call build.bat
if %errorlevel% neq 0 (
    echo WARNING: Desktop build failed
    echo Continue anyway? (Y/N)
    set /p "CONTINUE="
    if /i not "%CONTINUE%"=="Y" exit /b 1
)

REM Step 2: Create distribution package
echo.
echo ============================================
echo Step 2: Creating Distribution Package
echo ============================================
echo.
call create_offline_distro.bat

REM Step 3: Download prerequisites
echo.
echo ============================================
echo Step 3: Prerequisites Download
echo ============================================
echo.
echo You need to download these files manually:
echo.
echo 1. Python 3.11 installer
echo 2. Node.js 20 LTS installer
echo 3. Visual C++ Redistributable
echo 4. MinGW-w64 (optional)
echo 5. CMake (optional)
echo.
echo See: distro\prerequisites\DOWNLOAD_INSTRUCTIONS.md
echo.
echo Open download instructions now? (Y/N)
set /p "OPEN_INSTRUCTIONS="
if /i "%OPEN_INSTRUCTIONS%"=="Y" (
    start distro\prerequisites\DOWNLOAD_INSTRUCTIONS.md
)

REM Step 4: Create archive
echo.
echo ============================================
echo Step 4: Create Distribution Archive
echo ============================================
echo.
echo After downloading prerequisites, you can create a ZIP archive.
echo.
echo Create ZIP archive now? (Y/N)
echo (Requires 7-Zip or similar tool)
set /p "CREATE_ZIP="
if /i "%CREATE_ZIP%"=="Y" (
    if exist "C:\Program Files\7-Zip\7z.exe" (
        echo Creating archive...
        "C:\Program Files\7-Zip\7z.exe" a -tzip "ConstructionTimeManagement-Offline-Distro.zip" distro\*
        echo.
        echo Archive created: ConstructionTimeManagement-Offline-Distro.zip
    ) else (
        echo 7-Zip not found at default location
        echo Please create ZIP manually from distro\ folder
    )
)

REM Summary
echo.
echo ============================================
echo Distribution Package Ready!
echo ============================================
echo.
echo Package location: distro\
echo.
echo Contents:
echo - Application files: distro\app\
echo - Python packages: distro\python-packages\
echo - Node packages: distro\node-packages\
echo - Documentation: distro\docs\
echo - Prerequisites: distro\prerequisites\ (download manually)
echo.
echo Next steps:
echo 1. Download prerequisites (see DOWNLOAD_INSTRUCTIONS.md)
echo 2. Copy distro\ folder to USB/DVD/Network
echo 3. On target machine, run: distro\create_installer.bat
echo.
echo Quick start guide: distro\QUICK_START.md
echo Full guide: distro\INSTALLATION_GUIDE.md
echo.
pause
