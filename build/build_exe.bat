@echo off
REM ============================================================================
REM Build Standalone Executables for Distribution
REM Construction Time Management System
REM ============================================================================

echo ========================================
echo Building Standalone Executables
echo ========================================
echo.

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

REM Install PyInstaller if not present
echo [1/5] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Create build directory
echo.
echo [2/5] Creating build directories...
if not exist distro mkdir distro
if not exist distro\app mkdir distro\app

REM Build Desktop Application
echo.
echo [3/5] Building Desktop Application...
pyinstaller --name="ConstructionTimeManagement" ^
    --onefile ^
    --windowed ^
    --icon=fonts/icon.ico ^
    --add-data="fonts;fonts" ^
    --add-data="PrnForms;PrnForms" ^
    --add-data="construction.db;." ^
    --hidden-import=PyQt6 ^
    --hidden-import=openpyxl ^
    --hidden-import=reportlab ^
    --hidden-import=sqlalchemy ^
    --hidden-import=psycopg2 ^
    --hidden-import=pyodbc ^
    main.py

if %errorlevel% neq 0 (
    echo ERROR: Desktop application build failed!
    pause
    exit /b 1
)

REM Build API Server
echo.
echo [4/5] Building API Server...
pyinstaller --name="ConstructionTimeAPI" ^
    --onefile ^
    --console ^
    --add-data="api;api" ^
    --add-data="src/data;src/data" ^
    --add-data="src/services;src/services" ^
    --add-data=".env.production;." ^
    --hidden-import=fastapi ^
    --hidden-import=uvicorn ^
    --hidden-import=sqlalchemy ^
    --hidden-import=psycopg2 ^
    --hidden-import=pyodbc ^
    --hidden-import=jose ^
    --hidden-import=passlib ^
    start_server.py

if %errorlevel% neq 0 (
    echo ERROR: API server build failed!
    pause
    exit /b 1
)

REM Copy executables to distro
echo.
echo [5/5] Copying files to distro...
copy dist\ConstructionTimeManagement.exe distro\app\
copy dist\ConstructionTimeAPI.exe distro\app\

REM Copy configuration files
copy env.ini distro\app\
copy .env.production distro\app\.env
copy construction.db distro\app\

REM Copy support files
xcopy /E /I /Y fonts distro\app\fonts
xcopy /E /I /Y PrnForms distro\app\PrnForms

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executables created in: distro\app\
echo   - ConstructionTimeManagement.exe (Desktop App)
echo   - ConstructionTimeAPI.exe (API Server)
echo.
echo Configuration files copied:
echo   - env.ini (Desktop configuration)
echo   - .env (API configuration)
echo   - construction.db (Database)
echo.
pause
