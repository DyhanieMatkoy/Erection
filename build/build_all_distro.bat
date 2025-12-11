@echo off
REM ============================================================================
REM Master Distribution Builder
REM Construction Time Management System
REM ============================================================================

:MENU
cls
echo ========================================
echo Distribution Package Builder
echo Construction Time Management System
echo ========================================
echo.
echo Choose distribution type:
echo.
echo 1. Portable Distribution (Recommended)
echo    - No compilation required
echo    - Requires Python on target machine
echo    - Smaller package size (~150-200 MB)
echo    - Easy to update
echo.
echo 2. Standalone Executables
echo    - Compiled .exe files
echo    - No Python required on target
echo    - Larger package size (~300-400 MB)
echo    - Requires PyInstaller
echo.
echo 3. Complete Offline Package
echo    - Includes Python installer
echo    - Includes all dependencies
echo    - Largest package (~600 MB)
echo    - True offline installation
echo.
echo 4. Exit
echo.
echo ========================================
echo.
set /p "CHOICE=Enter choice (1-4): "
echo.

if "%CHOICE%"=="1" goto PORTABLE
if "%CHOICE%"=="2" goto STANDALONE
if "%CHOICE%"=="3" goto OFFLINE
if "%CHOICE%"=="4" exit
goto MENU

:PORTABLE
echo.
echo Building Portable Distribution...
echo.
call build_portable_distro.bat
goto DONE

:STANDALONE
echo.
echo Building Standalone Executables...
echo.
call build_distro.bat
goto DONE

:OFFLINE
echo.
echo Building Complete Offline Package...
echo.
call prepare_distro.bat
goto DONE

:DONE
echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Distribution package is in: distro\
echo.
echo Next steps:
echo 1. Test the package
echo 2. Create ZIP archive (optional)
echo 3. Distribute to users
echo.
echo Create ZIP archive now? (Y/N)
set /p "CREATE_ZIP="
if /i "%CREATE_ZIP%"=="Y" (
    echo.
    echo Creating ZIP archive...
    powershell -Command "Compress-Archive -Path distro\* -DestinationPath ConstructionTimeManagement-Distro.zip -Force"
    if %errorlevel% equ 0 (
        echo.
        echo ZIP archive created: ConstructionTimeManagement-Distro.zip
    ) else (
        echo.
        echo Failed to create ZIP. You can create it manually.
    )
)
echo.
echo Press any key to return to menu or close window to exit...
pause >nul
goto MENU
