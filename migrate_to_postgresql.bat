@echo off
REM Migrate database from SQLite to PostgreSQL
REM Usage: migrate_to_postgresql.bat [source_db] [target_config]

setlocal

set SOURCE_DB=%1
set TARGET_CONFIG=%2

if "%SOURCE_DB%"=="" set SOURCE_DB=construction.db
if "%TARGET_CONFIG%"=="" set TARGET_CONFIG=env_postgresql.ini

echo ============================================================
echo Database Migration Tool - SQLite to PostgreSQL
echo ============================================================
echo.
echo Source Database: %SOURCE_DB%
echo Target Config:   %TARGET_CONFIG%
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting migration...
echo.

python migrate_database.py --source %SOURCE_DB% --target-config %TARGET_CONFIG% --verify

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo Migration completed successfully!
    echo ============================================================
    echo.
    echo Next steps:
    echo 1. Test the application: python main.py
    echo 2. Verify all functionality works correctly
    echo 3. Update env.ini to use PostgreSQL permanently
    echo 4. Archive the SQLite database
    echo.
) else (
    echo.
    echo ============================================================
    echo Migration failed or completed with warnings!
    echo ============================================================
    echo.
    echo Please check the output above for errors.
    echo See TROUBLESHOOTING_DATABASE.md for help.
    echo.
)

pause
