@echo off
REM ============================================================================
REM Simple Installer Script
REM Construction Time Management System
REM ============================================================================

echo ============================================
echo Construction Time Management System
echo Offline Installer
echo ============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo Some features may not work correctly
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
)

REM Set installation directory
set "INSTALL_DIR=C:\ConstructionTimeManagement"
echo Default installation directory: %INSTALL_DIR%
echo.
set /p "CUSTOM_DIR=Press Enter to use default, or type custom path: "
if not "%CUSTOM_DIR%"=="" set "INSTALL_DIR=%CUSTOM_DIR%"

echo.
echo Installation directory: %INSTALL_DIR%
echo.

REM Check prerequisites
echo [Step 1/5] Checking prerequisites...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python from prerequisites folder first
    echo Run: prerequisites\python-3.11.x-amd64.exe
    pause
    exit /b 1
)
echo [OK] Python found

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Node.js not found!
    echo Web client will not be available
    echo To enable web client, install: prerequisites\node-v20.x.x-x64.msi
    set "SKIP_WEB=1"
) else (
    echo [OK] Node.js found
    set "SKIP_WEB=0"
)

REM Create installation directory
echo.
echo [Step 2/5] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo ERROR: Cannot create directory %INSTALL_DIR%
    echo Check permissions or choose different location
    pause
    exit /b 1
)
echo [OK] Directory created

REM Copy application files
echo.
echo [Step 3/5] Copying application files...
REM Check if we're in distro folder or parent folder
if exist app (
    xcopy /E /I /Y app "%INSTALL_DIR%"
) else if exist ..\app (
    xcopy /E /I /Y ..\app "%INSTALL_DIR%"
) else (
    echo ERROR: Cannot find app folder
    echo Please run this script from the distro folder
    pause
    exit /b 1
)
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy files
    pause
    exit /b 1
)
echo [OK] Files copied

REM Install Python dependencies
echo.
echo [Step 4/5] Installing Python dependencies...
cd "%INSTALL_DIR%"
REM Try offline installation first
if exist python-packages (
    echo Installing from local packages...
    python -m pip install --no-index --find-links=python-packages -r requirements.txt
) else if exist "%~dp0python-packages" (
    echo Installing from distro packages...
    python -m pip install --no-index --find-links="%~dp0python-packages" -r requirements.txt
) else (
    echo WARNING: Local packages not found, installing from internet...
    python -m pip install -r requirements.txt
)
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages
    echo.
    echo Trying alternative installation...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Installation failed
        pause
        exit /b 1
    )
)
echo [OK] Python packages installed

REM Setup web client
if "%SKIP_WEB%"=="0" (
    echo.
    echo [Step 5/5] Setting up web client...
    cd "%INSTALL_DIR%\web-client"
    
    if exist "%~dp0node-packages\node_modules.tar.gz" (
        echo Extracting node_modules...
        tar -xf "%~dp0node-packages\node_modules.tar.gz"
        if %errorlevel% neq 0 (
            echo WARNING: Failed to extract node_modules
            echo You can install manually later with: npm install
        ) else (
            echo [OK] Node modules installed
        )
    ) else (
        echo WARNING: node_modules.tar.gz not found
        echo You can install manually later with: npm install
    )
) else (
    echo.
    echo [Step 5/5] Skipping web client setup (Node.js not installed)
)

REM Create desktop shortcut
echo.
echo Creating desktop shortcut...
cd "%INSTALL_DIR%"
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Construction Time Management.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\run.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Construction Time Management System" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs
echo [OK] Desktop shortcut created

REM Create start menu shortcut
echo Creating start menu shortcut...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\Construction Time Management" mkdir "%START_MENU%\Construction Time Management"
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%START_MENU%\Construction Time Management\Construction Time Management.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\run.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Construction Time Management System" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs
echo [OK] Start menu shortcut created

REM Copy documentation
echo.
echo Copying documentation...
xcopy /E /I /Y docs "%INSTALL_DIR%\docs"
echo [OK] Documentation copied

REM Create uninstaller
echo.
echo Creating uninstaller...
(
echo @echo off
echo echo Uninstalling Construction Time Management System...
echo echo.
echo set /p "CONFIRM=Are you sure you want to uninstall? (Y/N): "
echo if /i not "%%CONFIRM%%"=="Y" exit /b 0
echo.
echo echo Removing files...
echo rd /s /q "%INSTALL_DIR%"
echo del "%%USERPROFILE%%\Desktop\Construction Time Management.lnk"
echo rd /s /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\Construction Time Management"
echo echo.
echo echo Uninstallation complete!
echo pause
) > "%INSTALL_DIR%\uninstall.bat"
echo [OK] Uninstaller created

REM Installation complete
echo.
echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo Installation directory: %INSTALL_DIR%
echo.
echo Desktop shortcut: Created
echo Start menu: Created
echo.
echo To start the application:
echo - Double-click desktop shortcut
echo - Or run: %INSTALL_DIR%\run.bat
echo.
echo Default login:
echo   Username: admin
echo   Password: admin
echo.
echo IMPORTANT: Change the default password after first login!
echo Run: %INSTALL_DIR%\reset_admin_password.bat
echo.
echo Documentation: %INSTALL_DIR%\docs
echo.
echo To uninstall: %INSTALL_DIR%\uninstall.bat
echo.
pause

REM Ask to start application
set /p "START_NOW=Start application now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    cd "%INSTALL_DIR%"
    start run.bat
)
