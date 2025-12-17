@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Полная установка проекта Erection
echo ========================================

:: Проверяем права администратора
net session >nul 2>&1
if errorlevel 1 (
    echo ВНИМАНИЕ: Рекомендуется запустить от имени администратора
    echo для корректной установки в C:\
    echo.
)

:: Проверяем Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Git не установлен
    echo Скачайте и установите Git с https://git-scm.com/
    pause
    exit /b 1
)

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ВНИМАНИЕ: Python не найден в PATH
    echo Убедитесь что Python установлен
)

:: Устанавливаем переменные
set PROJECT_DIR=C:\Erection
set REPO_URL=https://github.com/DyhanieMatkoy/Erection.git

:: Создаем папку проекта
echo Создаем папку проекта...
if exist "%PROJECT_DIR%" (
    echo Удаляем существующую папку...
    rmdir /s /q "%PROJECT_DIR%"
)

:: Клонируем репозиторий
echo Клонируем проект с GitHub...
git clone "%REPO_URL%" "%PROJECT_DIR%"

if errorlevel 1 (
    echo ОШИБКА: Не удалось клонировать репозиторий
    pause
    exit /b 1
)

:: Переходим в папку проекта
cd /d "%PROJECT_DIR%"

:: Создаем виртуальное окружение Python
echo Создаем виртуальное окружение Python...
python -m venv .venv

if errorlevel 1 (
    echo ВНИМАНИЕ: Не удалось создать виртуальное окружение
    echo Продолжаем без него...
) else (
    echo Активируем виртуальное окружение...
    call .venv\Scripts\activate.bat
)

:: Устанавливаем зависимости
if exist "requirements.txt" (
    echo Устанавливаем зависимости Python...
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo ВНИМАНИЕ: Некоторые зависимости могли не установиться
    )
)

:: Создаем ярлык на рабочем столе
echo Создаем ярлык на рабочем столе...
set DESKTOP=%USERPROFILE%\Desktop
echo @echo off > "%DESKTOP%\Запуск Erection.bat"
echo cd /d "%PROJECT_DIR%" >> "%DESKTOP%\Запуск Erection.bat"
echo call .venv\Scripts\activate.bat >> "%DESKTOP%\Запуск Erection.bat"
echo python main.py >> "%DESKTOP%\Запуск Erection.bat"
echo pause >> "%DESKTOP%\Запуск Erection.bat"

echo.
echo ========================================
echo УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo Проект установлен в: %PROJECT_DIR%
echo Ярлык создан на рабочем столе
echo.
echo Для запуска:
echo 1. Используйте ярлык "Запуск Erection.bat" на рабочем столе
echo 2. Или перейдите в %PROJECT_DIR% и запустите start_app.bat
echo.
echo Дополнительная настройка:
echo - Настройте базу данных в файлах конфигурации
echo - Проверьте файл .env для переменных окружения
echo.
pause