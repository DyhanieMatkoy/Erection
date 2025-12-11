@echo off
REM ============================================================================
REM Offline Distribution Package Creator
REM Construction Time Management System
REM ============================================================================

echo ========================================
echo Creating Offline Distribution Package
echo ========================================
echo.

REM Create directory structure
echo [1/8] Creating directory structure...
if not exist distro mkdir distro
if not exist distro\prerequisites mkdir distro\prerequisites
if not exist distro\python-packages mkdir distro\python-packages
if not exist distro\node-packages mkdir distro\node-packages
if not exist distro\app mkdir distro\app
if not exist distro\docs mkdir distro\docs

REM Download Python packages
echo.
echo [2/8] Downloading Python packages...
echo This will download all required Python packages as wheel files...
python -m pip download -r requirements.txt -d distro\python-packages
if %errorlevel% neq 0 (
    echo ERROR: Failed to download Python packages
    echo Make sure you have internet connection and pip is installed
    pause
    exit /b 1
)

REM Package Node.js dependencies
echo.
echo [3/8] Packaging Node.js dependencies...
if exist web-client\node_modules (
    echo Creating node_modules archive...
    cd web-client
    tar -czf ..\distro\node-packages\node_modules.tar.gz node_modules
    cd ..
    echo Node modules packaged successfully
) else (
    echo WARNING: web-client\node_modules not found
    echo Run 'npm install' in web-client folder first, or skip web client
)

REM Create NPM offline cache
echo.
echo [4/8] Creating NPM offline cache...
if exist web-client\package.json (
    cd web-client
    if not exist ..\distro\node-packages\npm-cache mkdir ..\distro\node-packages\npm-cache
    npm cache add --cache ..\distro\node-packages\npm-cache
    cd ..
    echo NPM cache created
) else (
    echo WARNING: web-client\package.json not found
)

REM Copy application files
echo.
echo [5/8] Copying application files...
echo Copying source code...
xcopy /E /I /Y src distro\app\src
xcopy /E /I /Y api distro\app\api
xcopy /E /I /Y web-client\src distro\app\web-client\src
xcopy /E /I /Y web-client\public distro\app\web-client\public
xcopy /E /I /Y PrnForms distro\app\PrnForms
xcopy /E /I /Y fonts distro\app\fonts

echo Copying configuration files...
copy /Y *.py distro\app\
copy /Y *.bat distro\app\
copy /Y *.txt distro\app\
copy /Y *.ini distro\app\
copy /Y *.md distro\app\
copy /Y .env distro\app\
copy /Y .env.production distro\app\
copy /Y construction.db distro\app\

echo Copying web-client config files...
copy /Y web-client\*.json distro\app\web-client\
copy /Y web-client\*.js distro\app\web-client\
copy /Y web-client\*.ts distro\app\web-client\
copy /Y web-client\.env* distro\app\web-client\
copy /Y web-client\*.html distro\app\web-client\

REM Copy documentation
echo.
echo [6/8] Copying documentation...
xcopy /E /I /Y docs distro\docs

REM Create download instructions for prerequisites
echo.
echo [7/8] Creating prerequisites download guide...
(
echo # Prerequisites Download Guide
echo.
echo Please download these files manually and place them in the `prerequisites` folder:
echo.
echo ## 1. Python 3.11 ^(Latest^)
echo - URL: https://www.python.org/downloads/
echo - File: python-3.11.x-amd64.exe
echo - Direct: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
echo.
echo ## 2. Node.js 20 LTS
echo - URL: https://nodejs.org/
echo - File: node-v20.x.x-x64.msi
echo - Direct: https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi
echo.
echo ## 3. Visual C++ Redistributable
echo - URL: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
echo - File: VC_redist.x64.exe
echo - Direct: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
echo ## 4. MinGW-w64 ^(Optional - for building^)
echo - URL: https://www.mingw-w64.org/downloads/
echo - File: mingw-w64-installer.exe
echo - Alternative: https://github.com/niXman/mingw-builds-binaries/releases
echo - Recommended: x86_64-posix-seh
echo.
echo ## 5. CMake ^(Optional - for building^)
echo - URL: https://cmake.org/download/
echo - File: cmake-x.xx.x-windows-x86_64.msi
echo - Direct: https://github.com/Kitware/CMake/releases/latest
echo.
echo ## Download Checklist
echo - [ ] Python 3.11 installer
echo - [ ] Node.js 20 LTS installer
echo - [ ] Visual C++ Redistributable
echo - [ ] MinGW-w64 ^(if building from source^)
echo - [ ] CMake ^(if building from source^)
echo.
echo After downloading, place all files in: `distro\prerequisites\`
) > distro\prerequisites\DOWNLOAD_INSTRUCTIONS.md

REM Create package info
echo.
echo [8/8] Creating package information...
(
echo # Offline Distribution Package
echo Created: %date% %time%
echo.
echo ## Package Contents
echo - Python packages: distro\python-packages\
echo - Node.js packages: distro\node-packages\
echo - Application files: distro\app\
echo - Documentation: distro\docs\
echo - Prerequisites: distro\prerequisites\ ^(download manually^)
echo.
echo ## Next Steps
echo 1. Read distro\README.md
echo 2. Download prerequisites ^(see distro\prerequisites\DOWNLOAD_INSTRUCTIONS.md^)
echo 3. Follow distro\INSTALLATION_GUIDE.md
echo.
echo ## Package Size
) > distro\PACKAGE_INFO.md

REM Calculate sizes
for /f "tokens=3" %%a in ('dir /s distro\python-packages ^| find "File(s)"') do echo - Python packages: %%a bytes >> distro\PACKAGE_INFO.md
for /f "tokens=3" %%a in ('dir /s distro\node-packages ^| find "File(s)"') do echo - Node packages: %%a bytes >> distro\PACKAGE_INFO.md
for /f "tokens=3" %%a in ('dir /s distro\app ^| find "File(s)"') do echo - Application: %%a bytes >> distro\PACKAGE_INFO.md

echo.
echo ========================================
echo Distribution Package Created!
echo ========================================
echo.
echo Location: distro\
echo.
echo IMPORTANT: Download prerequisites manually
echo See: distro\prerequisites\DOWNLOAD_INSTRUCTIONS.md
echo.
echo Next steps:
echo 1. Download prerequisites from the internet
echo 2. Place them in distro\prerequisites\
echo 3. Copy entire distro\ folder to USB/DVD
echo 4. Follow distro\INSTALLATION_GUIDE.md on target machine
echo.
echo Package is ready for offline distribution!
echo.
pause
