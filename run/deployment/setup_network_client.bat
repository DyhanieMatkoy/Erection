@echo off
chcp 65001 >nul
echo ================================================================
echo Настройка Desktop клиента для работы по сети
echo ================================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python с https://python.org
    pause
    exit /b 1
)

REM Проверка наличия pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip не найден. Переустановите Python с включенным pip
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены
echo.

REM Запуск скрипта настройки
echo Запуск мастера настройки...
python setup_network_client.py

echo.
echo ================================================================
echo Настройка завершена!
echo ================================================================
echo.
echo Для запуска приложения используйте:
echo   python main.py
echo.
echo Или запустите start_app.bat
echo.
pause