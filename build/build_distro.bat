@echo off
REM ============================================================================
REM Complete Distribution Package Builder
REM Construction Time Management System
REM ============================================================================

echo ========================================
echo Building Complete Distribution Package
echo ========================================
echo.

REM Step 1: Build Web Client
echo [1/4] Building Web Client...
call build_web.bat
if %errorlevel% neq 0 (
    echo WARNING: Web client build failed
    echo Continue anyway? (Y/N)
    set /p "CONTINUE="
    if /i not "%CONTINUE%"=="Y" exit /b 1
)

REM Step 2: Build Executables
echo.
echo [2/4] Building Executables...
call build_exe.bat
if %errorlevel% neq 0 (
    echo ERROR: Executable build failed!
    pause
    exit /b 1
)

REM Step 3: Copy Web Client
echo.
echo [3/4] Copying Web Client...
if exist web-client\dist (
    if not exist distro\app\web-client mkdir distro\app\web-client
    xcopy /E /I /Y web-client\dist distro\app\web-client\dist
    echo Web client copied successfully
) else (
    echo WARNING: Web client dist not found
)

REM Step 4: Create launcher scripts
echo.
echo [4/4] Creating launcher scripts...

REM Desktop launcher
(
echo @echo off
echo echo Starting Construction Time Management System...
echo start ConstructionTimeManagement.exe
) > distro\app\StartDesktop.bat

REM API Server launcher
(
echo @echo off
echo echo Starting API Server...
echo echo.
echo echo API will be available at: http://localhost:8000
echo echo Web Client: http://localhost:8000
echo echo API Docs: http://localhost:8000/docs
echo echo.
echo echo Press Ctrl+C to stop the server
echo echo.
echo ConstructionTimeAPI.exe
echo pause
) > distro\app\StartServer.bat

REM Combined launcher
(
echo @echo off
echo echo ========================================
echo echo Construction Time Management System
echo echo ========================================
echo echo.
echo echo Choose an option:
echo echo 1. Start Desktop Application
echo echo 2. Start Web Server
echo echo 3. Start Both
echo echo 4. Exit
echo echo.
echo set /p "CHOICE=Enter choice (1-4): "
echo.
echo if "%%CHOICE%%"=="1" (
echo     start ConstructionTimeManagement.exe
echo     echo Desktop application started
echo ^)
echo if "%%CHOICE%%"=="2" (
echo     start StartServer.bat
echo     echo Web server started
echo ^)
echo if "%%CHOICE%%"=="3" (
echo     start ConstructionTimeManagement.exe
echo     start StartServer.bat
echo     echo Both applications started
echo ^)
echo.
echo pause
) > distro\app\Start.bat

REM Create README
(
echo # Construction Time Management System
echo.
echo ## Quick Start
echo.
echo ### Desktop Application
echo Run: `StartDesktop.bat` or `ConstructionTimeManagement.exe`
echo.
echo ### Web Application
echo 1. Run: `StartServer.bat` or `ConstructionTimeAPI.exe`
echo 2. Open browser: http://localhost:8000
echo.
echo ### Both Applications
echo Run: `Start.bat` and choose option 3
echo.
echo ## Configuration
echo.
echo ### Desktop Application
echo Edit `env.ini` to configure:
echo - Database connection
echo - Application settings
echo.
echo ### Web/API Server
echo Edit `.env` to configure:
echo - Database connection
echo - JWT secret key
echo - CORS origins
echo - API settings
echo.
echo ## Default Credentials
echo - Username: admin
echo - Password: admin
echo.
echo **IMPORTANT:** Change the default password after first login!
echo.
echo ## Database
echo.
echo Default database: `construction.db` (SQLite)
echo.
echo To use PostgreSQL or MS SQL Server, edit the configuration files.
echo.
echo ## Support Files
echo - `fonts/` - Application fonts
echo - `PrnForms/` - Print templates
echo - `web-client/dist/` - Web client files
echo.
echo ## Troubleshooting
echo.
echo ### Desktop app won't start
echo - Check `env.ini` configuration
echo - Ensure `construction.db` exists
echo - Check Windows Event Viewer for errors
echo.
echo ### Web server won't start
echo - Check if port 8000 is available
echo - Check `.env` configuration
echo - Look for error messages in console
echo.
echo ### Database errors
echo - Verify database file exists
echo - Check database connection settings
echo - Ensure proper permissions
echo.
echo For more help, see the documentation in the `docs` folder.
) > distro\app\README.md

echo.
echo ========================================
echo Distribution Package Complete!
echo ========================================
echo.
echo Location: distro\app\
echo.
echo Contents:
echo   Executables:
echo     - ConstructionTimeManagement.exe (Desktop)
echo     - ConstructionTimeAPI.exe (Web Server)
echo.
echo   Launchers:
echo     - Start.bat (Main launcher)
echo     - StartDesktop.bat (Desktop only)
echo     - StartServer.bat (Server only)
echo.
echo   Configuration:
echo     - env.ini (Desktop config)
echo     - .env (API config)
echo     - construction.db (Database)
echo.
echo   Support Files:
echo     - fonts/ (Fonts)
echo     - PrnForms/ (Print templates)
echo     - web-client/dist/ (Web client)
echo     - README.md (Quick start guide)
echo.
echo Ready for distribution!
echo.
pause
