@echo off
chcp 65001 >nul
echo ================================================================
echo Запуск Desktop приложения "Система управления рабочим временем"
echo ================================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python с https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Проверка наличия виртуального окружения
if exist ".venv\Scripts\activate.bat" (
    echo ✅ Виртуальное окружение найдено
    echo Активация виртуального окружения...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  Виртуальное окружение не найдено
    echo Используется системный Python
)

echo.

REM Проверка наличия конфигурации базы данных
if exist "env.ini" (
    echo ✅ Найден файл конфигурации базы данных (env.ini)
    echo Приложение будет использовать настройки из env.ini
) else (
    if exist "construction.db" (
        echo ✅ Найдена локальная база данных SQLite (construction.db)
        echo Приложение будет использовать локальную базу данных
    ) else (
        echo ❌ Не найдена база данных или конфигурация
        echo.
        echo Для настройки сетевого подключения запустите:
        echo   setup_network_client.bat
        echo.
        echo Или создайте локальную базу данных:
        echo   python -c "from src.data.database_manager import DatabaseManager; dm = DatabaseManager(); dm.initialize('construction.db')"
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ================================================================
echo Запуск приложения...
echo ================================================================
echo.

REM Запуск Desktop приложения
python main.py

REM Проверка кода завершения
if errorlevel 1 (
    echo.
    echo ❌ Приложение завершилось с ошибкой
    echo.
    echo Возможные причины:
    echo - Отсутствуют зависимости (запустите: pip install -r requirements.txt)
    echo - Проблемы с подключением к базе данных
    echo - Неверная конфигурация в env.ini
    echo.
    pause
) else (
    echo.
    echo ✅ Приложение завершено успешно
)