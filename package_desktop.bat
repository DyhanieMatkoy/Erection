@echo off
chcp 65001 > nul
echo ========================================
echo   УПАКОВКА ДЕСКТОПНОГО ПРИЛОЖЕНИЯ
echo ========================================
echo.

echo Проверка Python...
python --version
if %errorlevel% neq 0 (
    echo Ошибка: Python не найден!
    echo Установите Python 3.10+ и повторите попытку.
    pause
    exit /b 1
)

echo.
echo Установка зависимостей...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Запуск упаковки...
python package_desktop.py

echo.
echo Готово!
pause