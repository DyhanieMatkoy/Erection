@echo off
echo ========================================
echo Скачивание проекта Erection с GitHub
echo ========================================

:: Проверяем наличие git
git --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Git не установлен или не найден в PATH
    echo Установите Git с https://git-scm.com/
    pause
    exit /b 1
)

:: Устанавливаем переменные
set REPO_URL=https://github.com/DyhanieMatkoy/Erection.git
set TARGET_DIR=C:\Erection
set BRANCH=main

echo Репозиторий: %REPO_URL%
echo Целевая папка: %TARGET_DIR%
echo Ветка: %BRANCH%
echo.

:: Проверяем существует ли уже папка
if exist "%TARGET_DIR%" (
    echo Папка %TARGET_DIR% уже существует.
    echo Выберите действие:
    echo 1 - Удалить и клонировать заново
    echo 2 - Обновить существующий репозиторий (git pull)
    echo 3 - Отмена
    set /p choice="Введите номер (1-3): "
    
    if "!choice!"=="1" (
        echo Удаляем существующую папку...
        rmdir /s /q "%TARGET_DIR%"
        goto clone_repo
    ) else if "!choice!"=="2" (
        echo Обновляем существующий репозиторий...
        cd /d "%TARGET_DIR%"
        git pull origin %BRANCH%
        if errorlevel 1 (
            echo ОШИБКА: Не удалось обновить репозиторий
            pause
            exit /b 1
        )
        echo Репозиторий успешно обновлен!
        goto success
    ) else (
        echo Операция отменена
        pause
        exit /b 0
    )
)

:clone_repo
echo Клонируем репозиторий...
git clone -b %BRANCH% "%REPO_URL%" "%TARGET_DIR%"

if errorlevel 1 (
    echo ОШИБКА: Не удалось клонировать репозиторий
    echo Проверьте:
    echo - Подключение к интернету
    echo - Правильность URL репозитория
    echo - Права доступа к папке C:\
    pause
    exit /b 1
)

:success
echo.
echo ========================================
echo УСПЕШНО!
echo ========================================
echo Проект скачан в: %TARGET_DIR%
echo.
echo Следующие шаги:
echo 1. Перейдите в папку: cd /d "%TARGET_DIR%"
echo 2. Установите зависимости Python: pip install -r requirements.txt
echo 3. Настройте базу данных и конфигурацию
echo.
pause