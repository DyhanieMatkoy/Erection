@echo off
REM ============================================================================
REM Build Portable Distribution (No compilation required)
REM Construction Time Management System
REM ============================================================================

echo ========================================
echo Building Portable Distribution
echo ========================================
echo.

REM Create directory structure
echo [1/7] Creating directory structure...
if not exist distro\app mkdir distro\app
if not exist distro\app\python-packages mkdir distro\app\python-packages
if not exist distro\docs mkdir distro\docs

REM Copy application source
echo.
echo [2/7] Copying application source...
xcopy /E /I /Y src distro\app\src
xcopy /E /I /Y api distro\app\api
xcopy /E /I /Y fonts distro\app\fonts
xcopy /E /I /Y PrnForms distro\app\PrnForms

REM Copy Python scripts
echo.
echo [3/7] Copying Python scripts...
copy /Y main.py distro\app\
copy /Y start_server.py distro\app\
copy /Y reset_admin_password.py distro\app\
copy /Y check_status.py distro\app\
copy /Y manage_users.py distro\app\
copy /Y migrate_database.py distro\app\

REM Copy configuration files
echo.
echo [4/7] Copying configuration files...
copy /Y env.ini distro\app\
copy /Y .env.production distro\app\.env
copy /Y construction.db distro\app\
copy /Y requirements.txt distro\app\

REM Build and copy web client
echo.
echo [5/7] Building web client...
if exist web-client (
    call build_web.bat
    if exist web-client\dist (
        xcopy /E /I /Y web-client\dist distro\app\web-client\dist
        echo Web client copied
    )
)

REM Download Python packages
echo.
echo [6/7] Downloading Python packages...
python -m pip download -r requirements.txt -d distro\app\python-packages
if %errorlevel% neq 0 (
    echo WARNING: Failed to download some packages
)
REM Ensure pydantic-settings is downloaded
python -m pip download pydantic-settings -d distro\app\python-packages 2>nul

REM Create launcher scripts
echo.
echo [7/7] Creating launcher scripts...

REM Setup script
(
echo @echo off
echo echo ========================================
echo echo Setup - Construction Time Management
echo echo ========================================
echo echo.
echo echo This will install Python dependencies...
echo echo.
echo pause
echo.
echo REM Check if Python is installed
echo python --version ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 (
echo     echo ERROR: Python is not installed!
echo     echo Please install Python 3.11 or later
echo     echo Download from: https://www.python.org/downloads/
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Installing dependencies from local packages...
echo pip install --no-index --find-links=python-packages -r requirements.txt
echo.
echo if %%errorlevel%% equ 0 (
echo     echo.
echo     echo ========================================
echo     echo Setup Complete!
echo     echo ========================================
echo     echo.
echo     echo You can now run the application:
echo     echo   - Desktop: StartDesktop.bat
echo     echo   - Web Server: StartServer.bat
echo     echo.
echo ^) else (
echo     echo.
echo     echo ERROR: Installation failed!
echo     echo Try installing from internet: pip install -r requirements.txt
echo     echo.
echo ^)
echo pause
) > distro\app\Setup.bat

REM Desktop launcher
(
echo @echo off
echo echo Starting Desktop Application...
echo python main.py
echo if %%errorlevel%% neq 0 (
echo     echo.
echo     echo ERROR: Failed to start application
echo     echo Make sure you ran Setup.bat first
echo     pause
echo ^)
) > distro\app\StartDesktop.bat

REM Server launcher
(
echo @echo off
echo echo ========================================
echo echo Construction Time Management - Web Server
echo echo ========================================
echo echo.
echo echo Starting server...
echo echo.
echo echo API Server: http://localhost:8000
echo echo Web Client: http://localhost:8000
echo echo API Docs: http://localhost:8000/docs
echo echo.
echo echo Press Ctrl+C to stop the server
echo echo.
echo python start_server.py
echo.
echo if %%errorlevel%% neq 0 (
echo     echo.
echo     echo ERROR: Failed to start server
echo     echo Make sure you ran Setup.bat first
echo     pause
echo ^)
) > distro\app\StartServer.bat

REM Main launcher
(
echo @echo off
echo :MENU
echo cls
echo ========================================
echo Construction Time Management System
echo ========================================
echo.
echo 1. Setup (First time only)
echo 2. Start Desktop Application
echo 3. Start Web Server
echo 4. Start Both
echo 5. Reset Admin Password
echo 6. Check System Status
echo 7. Exit
echo.
echo ========================================
echo.
echo set /p "CHOICE=Enter choice (1-7): "
echo.
echo if "%%CHOICE%%"=="1" call Setup.bat
echo if "%%CHOICE%%"=="2" start StartDesktop.bat
echo if "%%CHOICE%%"=="3" start StartServer.bat
echo if "%%CHOICE%%"=="4" (
echo     start StartDesktop.bat
echo     start StartServer.bat
echo ^)
echo if "%%CHOICE%%"=="5" python reset_admin_password.py
echo if "%%CHOICE%%"=="6" python check_status.py ^&^& pause
echo if "%%CHOICE%%"=="7" exit
echo.
echo if not "%%CHOICE%%"=="7" goto MENU
) > distro\app\Start.bat

REM Copy documentation
echo.
echo Copying documentation...
if exist docs xcopy /E /I /Y docs distro\docs

REM Create main README
(
echo # Construction Time Management System - Portable Distribution
echo.
echo ## Quick Start
echo.
echo ### First Time Setup
echo.
echo 1. Ensure Python 3.11+ is installed
echo    - Download from: https://www.python.org/downloads/
echo    - During installation, check "Add Python to PATH"
echo.
echo 2. Run `Setup.bat` to install dependencies
echo.
echo 3. Start the application:
echo    - Run `Start.bat` for menu
echo    - Or run `StartDesktop.bat` for desktop app
echo    - Or run `StartServer.bat` for web server
echo.
echo ## What's Included
echo.
echo - **Desktop Application**: Full-featured PyQt6 desktop interface
echo - **Web Server**: FastAPI server with Vue.js web client
echo - **Database**: SQLite database (can be configured for PostgreSQL/MSSQL)
echo - **Python Packages**: All dependencies included offline
echo.
echo ## Launchers
echo.
echo - `Start.bat` - Main menu launcher
echo - `Setup.bat` - Install dependencies (run once)
echo - `StartDesktop.bat` - Launch desktop application
echo - `StartServer.bat` - Launch web server
echo.
echo ## Configuration
echo.
echo ### Desktop Application
echo Edit `env.ini`:
echo ```ini
echo [Database]
echo type = sqlite
echo path = construction.db
echo ```
echo.
echo ### Web/API Server
echo Edit `.env`:
echo ```
echo DATABASE_TYPE=sqlite
echo DATABASE_PATH=construction.db
echo JWT_SECRET_KEY=your-secret-key-here
echo CORS_ORIGINS=http://localhost:8000
echo ```
echo.
echo ## Default Credentials
echo.
echo - **Username**: admin
echo - **Password**: admin
echo.
echo **IMPORTANT**: Change the password after first login!
echo Use option 5 in Start.bat menu to reset password.
echo.
echo ## System Requirements
echo.
echo - Windows 10/11 (64-bit)
echo - Python 3.11 or later
echo - 2 GB RAM minimum
echo - 500 MB disk space
echo.
echo ## Database Options
echo.
echo ### SQLite (Default)
echo - No additional setup required
echo - Included database file: `construction.db`
echo - Good for single-user or small teams
echo.
echo ### PostgreSQL
echo 1. Install PostgreSQL server
echo 2. Create database
echo 3. Update configuration files
echo 4. Run: `python migrate_database.py`
echo.
echo ### MS SQL Server
echo 1. Install SQL Server
echo 2. Create database
echo 3. Update configuration files
echo 4. Run: `python migrate_database.py`
echo.
echo ## Utilities
echo.
echo - `reset_admin_password.py` - Reset admin password
echo - `check_status.py` - Check system status
echo - `manage_users.py` - Manage users
echo - `migrate_database.py` - Migrate to different database
echo.
echo ## Troubleshooting
echo.
echo ### Python not found
echo - Install Python from https://www.python.org/downloads/
echo - Make sure "Add Python to PATH" was checked during installation
echo - Restart command prompt after installation
echo.
echo ### Dependencies installation fails
echo - Check internet connection
echo - Try: `pip install -r requirements.txt`
echo - Or install from local packages: `pip install --no-index --find-links=python-packages -r requirements.txt`
echo.
echo ### Desktop app won't start
echo - Run Setup.bat first
echo - Check env.ini configuration
echo - Ensure construction.db exists
echo.
echo ### Web server won't start
echo - Check if port 8000 is available
echo - Check .env configuration
echo - Look for error messages in console
echo.
echo ### Database errors
echo - Verify database file exists
echo - Check database connection settings
echo - Ensure proper file permissions
echo.
echo ## Support
echo.
echo For detailed documentation, see the `docs` folder:
echo - `docs/START_HERE.md` - Getting started guide
echo - `docs/DATABASE_AND_CONFIG_GUIDE.md` - Configuration guide
echo - `docs/TROUBLESHOOTING_DATABASE.md` - Database troubleshooting
echo.
echo ## File Structure
echo.
echo ```
echo app/
echo ├── Start.bat                    # Main launcher
echo ├── Setup.bat                    # Dependency installer
echo ├── StartDesktop.bat             # Desktop launcher
echo ├── StartServer.bat              # Server launcher
echo ├── main.py                      # Desktop app entry point
echo ├── start_server.py              # Server entry point
echo ├── env.ini                      # Desktop configuration
echo ├── .env                         # Server configuration
echo ├── construction.db              # SQLite database
echo ├── requirements.txt             # Python dependencies
echo ├── python-packages/             # Offline Python packages
echo ├── src/                         # Application source code
echo ├── api/                         # API source code
echo ├── web-client/dist/             # Web client files
echo ├── fonts/                       # Application fonts
echo ├── PrnForms/                    # Print templates
echo └── README.md                    # This file
echo ```
echo.
echo ## License
echo.
echo Construction Time Management System
echo Copyright (c) 2024
echo.
) > distro\app\README.md

REM Create installation guide
(
echo # Installation Guide
echo.
echo ## Prerequisites
echo.
echo Before installing, ensure you have:
echo - Windows 10 or 11 (64-bit)
echo - Administrator rights (for Python installation)
echo - 500 MB free disk space
echo.
echo ## Step 1: Install Python
echo.
echo 1. Download Python 3.11 or later from https://www.python.org/downloads/
echo 2. Run the installer
echo 3. **IMPORTANT**: Check "Add Python to PATH"
echo 4. Click "Install Now"
echo 5. Wait for installation to complete
echo 6. Restart your computer (recommended)
echo.
echo ## Step 2: Extract Application
echo.
echo 1. Copy the `app` folder to your desired location
echo    Example: `C:\ConstructionTimeManagement\`
echo 2. Do not use paths with spaces or special characters
echo.
echo ## Step 3: Run Setup
echo.
echo 1. Open the `app` folder
echo 2. Double-click `Setup.bat`
echo 3. Wait for dependencies to install
echo 4. Press any key when complete
echo.
echo ## Step 4: Start Application
echo.
echo ### Option A: Use Main Menu
echo 1. Double-click `Start.bat`
echo 2. Choose option 2 for Desktop or 3 for Web Server
echo.
echo ### Option B: Direct Launch
echo - Desktop: Double-click `StartDesktop.bat`
echo - Web Server: Double-click `StartServer.bat`
echo.
echo ## Step 5: First Login
echo.
echo 1. Use default credentials:
echo    - Username: admin
echo    - Password: admin
echo.
echo 2. **IMPORTANT**: Change password immediately!
echo    - Desktop: Settings ^> Change Password
echo    - Web: Profile ^> Change Password
echo    - Or use: `Start.bat` ^> Option 5
echo.
echo ## Verification
echo.
echo ### Desktop Application
echo - Main window should open
echo - You should see the login screen
echo - After login, main interface appears
echo.
echo ### Web Server
echo - Console shows "Application startup complete"
echo - Open browser to http://localhost:8000
echo - Login page should appear
echo.
echo ## Next Steps
echo.
echo 1. Read `README.md` for usage instructions
echo 2. Configure database if needed (see `docs/DATABASE_AND_CONFIG_GUIDE.md`)
echo 3. Create user accounts
echo 4. Start entering data
echo.
echo ## Troubleshooting
echo.
echo See `README.md` troubleshooting section or `docs/TROUBLESHOOTING_DATABASE.md`
echo.
) > distro\INSTALLATION_GUIDE.md

echo.
echo ========================================
echo Portable Distribution Complete!
echo ========================================
echo.
echo Location: distro\app\
echo.
echo Package Contents:
echo   - Application source code
echo   - Python packages (offline)
echo   - Web client (built)
echo   - Configuration files
echo   - Database file
echo   - Launcher scripts
echo   - Documentation
echo.
echo Package Size: ~150-200 MB
echo.
echo This package can be:
echo   - Copied to USB drive
echo   - Shared via network
echo   - Distributed as ZIP file
echo.
echo Requirements on target machine:
echo   - Python 3.11+ installed
echo   - Run Setup.bat once
echo.
echo Ready for distribution!
echo.
pause
