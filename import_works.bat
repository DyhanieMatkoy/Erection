@echo off
chcp 65001 >nul
echo ========================================
echo Импорт работ из CSV
echo ========================================
echo.

if "%1"=="" (
    echo Использование: import_works.bat [путь_к_csv_файлу] [--update]
    echo.
    echo Примеры:
    echo   import_works.bat умелец.csv
    echo   import_works.bat умелец.csv --update
    echo.
    echo Опции:
    echo   --update  Обновлять существующие работы вместо пропуска
    echo.
    pause
    exit /b 1
)

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Виртуальное окружение не найдено!
    pause
    exit /b 1
)

python import_works_from_csv.py %*

echo.
pause
