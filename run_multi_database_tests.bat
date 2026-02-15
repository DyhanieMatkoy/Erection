@echo off
REM Multi-Database Synchronization Testing Script
REM This script provides easy access to multi-database sync testing functionality

echo ========================================
echo Multi-Database Synchronization Testing
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if required dependencies are available
echo Checking dependencies...
python -c "import psycopg2, pymysql, sqlite3, alembic" >nul 2>&1
if errorlevel 1 (
    echo Warning: Some database drivers may not be installed
    echo Installing required packages...
    pip install psycopg2-binary pymysql alembic
)

echo.
echo Available test options:
echo 1. Run all test scenarios
echo 2. Run PostgreSQL mixed scenario
echo 3. Run MySQL mixed scenario  
echo 4. Run SQLite + MySQL scenario
echo 5. Run migration tests only
echo 6. List available scenarios
echo 7. Custom scenario
echo 0. Exit
echo.

set /p choice="Select option (0-7): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :all_scenarios
if "%choice%"=="2" goto :postgresql_mixed
if "%choice%"=="3" goto :mysql_mixed
if "%choice%"=="4" goto :sqlite_mysql
if "%choice%"=="5" goto :migration_only
if "%choice%"=="6" goto :list_scenarios
if "%choice%"=="7" goto :custom
goto :invalid_choice

:all_scenarios
echo.
echo Running all test scenarios...
echo This may take 15-20 minutes to complete.
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" goto :end

python test_multi_database_sync.py --all-scenarios --verbose
goto :show_results

:postgresql_mixed
echo.
echo Running PostgreSQL mixed scenario...
echo Server: PostgreSQL, Clients: SQLite + MySQL + MySQL
echo.
python test_multi_database_sync.py --scenario postgresql_mixed --verbose
goto :show_results

:mysql_mixed
echo.
echo Running MySQL mixed scenario...
echo Server: MySQL, Clients: SQLite + SQLite + MySQL
echo.
python test_multi_database_sync.py --scenario mysql_mixed --verbose
goto :show_results

:sqlite_mysql
echo.
echo Running SQLite + MySQL scenario...
echo Server: SQLite, Clients: MySQL + MySQL + MySQL
echo.
python test_multi_database_sync.py --scenario sqlite_mysql --verbose
goto :show_results

:migration_only
echo.
echo Running migration tests only...
echo Using default PostgreSQL mixed scenario for migration testing
echo.
python test_multi_database_sync.py --migration-tests-only --verbose
goto :show_results

:list_scenarios
echo.
python test_multi_database_sync.py --list-scenarios
echo.
pause
goto :end

:custom
echo.
echo Custom scenario options:
echo.
python test_multi_database_sync.py --list-scenarios
echo.
set /p scenario_name="Enter scenario name: "
if "%scenario_name%"=="" goto :end

echo.
set /p migration_only="Migration tests only? (y/N): "
if /i "%migration_only%"=="y" (
    python test_multi_database_sync.py --scenario %scenario_name% --migration-tests-only --verbose
) else (
    python test_multi_database_sync.py --scenario %scenario_name% --verbose
)
goto :show_results

:show_results
echo.
echo ========================================
echo Test Execution Completed
echo ========================================
echo.
echo Reports have been generated in the test_reports/ directory
echo.
echo Opening test reports directory...
if exist "test_reports" (
    explorer test_reports
) else (
    echo No reports directory found. Tests may have failed to complete.
)
echo.
pause
goto :end

:invalid_choice
echo.
echo Invalid choice. Please select a number between 0-7.
echo.
pause
goto :end

:end
echo.
echo Goodbye!
pause