@echo off
setlocal EnableDelayedExpansion

echo ===================================================
echo PREPARING PRODUCTION BUILD
echo ===================================================

REM --- 1. Cleanup ---
echo [1/5] Cleaning up old builds...
if exist "distro" rmdir /s /q "distro"
if exist "build" rmdir /s /q "build"
if exist "web-client\dist" rmdir /s /q "web-client\dist"
if exist "deploy-to-prod\output" rmdir /s /q "deploy-to-prod\output"

REM --- 2. Build Web Client ---
echo [2/5] Building Web Client...
cd web-client
call npm install
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo Error building web client!
    exit /b 1
)
cd ..

REM --- 3. Prepare Directory Structure ---
echo [3/5] Creating directory structure...
set DIST_DIR=distro\server
mkdir "%DIST_DIR%"
mkdir "%DIST_DIR%\api"
mkdir "%DIST_DIR%\src"
mkdir "%DIST_DIR%\PrnForms"
mkdir "%DIST_DIR%\web-client"
mkdir "%DIST_DIR%\alembic"

REM --- 4. Copy Files ---
echo [4/5] Copying files...

REM Backend Code
xcopy /E /I /Y "api" "%DIST_DIR%\api"
xcopy /E /I /Y "src" "%DIST_DIR%\src"

REM Data & Config
xcopy /E /I /Y "PrnForms" "%DIST_DIR%\PrnForms"
xcopy /E /I /Y "alembic" "%DIST_DIR%\alembic"
copy /Y "env.ini" "%DIST_DIR%\"
copy /Y "alembic.ini" "%DIST_DIR%\"
copy /Y "requirements.txt" "%DIST_DIR%\"
copy /Y "construction.db" "%DIST_DIR%\"

REM Frontend Build
xcopy /E /I /Y "web-client\dist" "%DIST_DIR%\web-client\dist"

REM --- 5. Create Start Script ---
echo [5/5] Creating start script...
(
echo @echo off
echo echo Starting Construction Time Management Server...
echo.
echo REM Check for Python
echo python --version ^>nul 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo Python is not installed or not in PATH.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Install dependencies if needed
echo if not exist "venv" ^(
echo     echo Creating virtual environment...
echo     python -m venv venv
echo     call venv\Scripts\activate
echo     echo Installing dependencies...
echo     pip install -r requirements.txt
echo ^) else ^(
echo     call venv\Scripts\activate
echo ^)
echo.
echo REM Start API Server
echo echo Starting API on port 8000...
echo python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
echo.
echo pause
) > "%DIST_DIR%\start_server.bat"

echo.
echo ===================================================
echo BUILD COMPLETE
echo ===================================================
echo Production files are located in: %DIST_DIR%
echo.
echo To deploy:
echo 1. Copy the contents of '%DIST_DIR%' to your server (e.g., C:\app).
echo 2. Configure Nginx to point to C:\app\web-client\dist
echo 3. Run 'start_server.bat' on the server.
echo.
pause
