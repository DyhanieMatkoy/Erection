@echo off
echo ========================================
echo PyQt6 DLL Issue Fix
echo ========================================
echo.
echo This script will attempt to fix PyQt6 DLL loading issues.
echo.
pause

echo.
echo [Step 1/5] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo [Step 2/5] Completely removing PyQt6...
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-WebEngine 2>nul
echo Done.

echo.
echo [Step 3/5] Clearing pip cache...
pip cache purge 2>nul
echo Done.

echo.
echo [Step 4/5] Reinstalling PyQt6 from local packages...
if exist python-packages (
    pip install --no-cache-dir --no-index --find-links=python-packages PyQt6
) else (
    echo Local packages not found, installing from internet...
    pip install --no-cache-dir PyQt6
)

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed!
    echo.
    echo Please try:
    echo 1. Install Visual C++ Redistributable:
    echo    https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo 2. Restart your computer
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo [Step 5/5] Testing PyQt6...
python -c "import PyQt6.QtWidgets; print('SUCCESS: PyQt6 is working!')"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo PyQt6 Fixed Successfully!
    echo ========================================
    echo.
    echo You can now run StartDesktop.bat
    echo.
) else (
    echo.
    echo ========================================
    echo PyQt6 Still Has Issues
    echo ========================================
    echo.
    echo Additional steps to try:
    echo.
    echo 1. Install Visual C++ Redistributable:
    echo    https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    echo 2. Check Windows version:
    echo    - PyQt6 requires Windows 10 or later
    echo.
    echo 3. Try different Python version:
    echo    - Uninstall current Python
    echo    - Install Python 3.11.x from python.org
    echo    - Make sure to check "Add Python to PATH"
    echo.
    echo 4. Check system PATH:
    echo    - Python installation folder should be in PATH
    echo    - Python\Scripts folder should be in PATH
    echo.
    echo 5. Run as Administrator:
    echo    - Right-click this script
    echo    - Select "Run as administrator"
    echo.
)

pause
