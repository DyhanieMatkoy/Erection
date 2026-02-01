@echo off
echo ========================================
echo   Система очистки тестовых данных
echo ========================================
echo.

echo Выполняется поиск тестовых данных для удаления...
python test_cleanup_manager.py --dry-run

echo.
echo Хотите продолжить очистку? (y/N)
set /p choice=
if /i "%choice%"=="y" (
    echo.
    echo Выполняется очистка...
    python test_cleanup_manager.py
    echo.
    echo Очистка завершена!
) else (
    echo Очистка отменена.
)

echo.
pause