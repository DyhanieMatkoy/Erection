@echo off
chcp 65001 >nul
echo ========================================
echo Просмотр импортированных работ
echo ========================================
echo.

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Виртуальное окружение не найдено!
    pause
    exit /b 1
)

if "%1"=="" (
    echo Показываем все группы работ...
    echo.
    python view_works.py
) else (
    echo Показываем работы группы: %*
    echo.
    python view_works.py --group %*
)

echo.
pause
