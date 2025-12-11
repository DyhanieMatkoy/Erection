@echo off
:MENU
cls
echo ========================================
echo Construction Time Management System
echo ========================================
echo.
echo 1. Setup (First time only)
echo 2. Start Desktop Application
echo 3. Start Web Server
echo 4. Start Both
echo 5. Fix PyQt6 Issues
echo 6. Reset Admin Password
echo 7. Check System Status
echo 8. Exit
echo.
echo ========================================
echo.
set /p "CHOICE=Enter choice (1-8): "
echo.

if "%CHOICE%"=="1" call Setup.bat
if "%CHOICE%"=="2" start StartDesktop.bat
if "%CHOICE%"=="3" start StartServer.bat
if "%CHOICE%"=="4" (
    start StartDesktop.bat
    start StartServer.bat
)
if "%CHOICE%"=="5" call FixPyQt6.bat
if "%CHOICE%"=="6" python reset_admin_password.py
if "%CHOICE%"=="7" python check_status.py && pause
if "%CHOICE%"=="8" exit

if not "%CHOICE%"=="8" goto MENU
