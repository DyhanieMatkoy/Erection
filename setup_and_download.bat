@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Установка и скачивание проекта Erection
echo ========================================

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен
    echo Установите Python с https://python.org/
    pause
    exit /b 1
)

echo Python найден: 
python --version

:: Проверяем pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: pip не найден
    pause
    exit /b 1
)

:: Проверяем и устанавливаем requests
echo.
echo Проверяем зависимости...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Устанавливаем библиотеку requests...
    pip install requests
    if errorlevel 1 (
        echo ОШИБКА: Не удалось установить requests
        pause
        exit /b 1
    )
) else (
    echo requests уже установлен
)

:: Определяем целевую папку
if "%~1"=="" (
    set TARGET_DIR=%cd%\src
) else (
    set TARGET_DIR=%~1
)

echo.
echo Скачиваем файлы в: %TARGET_DIR%
echo.

:: Запускаем скачивание
python download_src_files.py "%TARGET_DIR%"

if errorlevel 1 (
    echo.
    echo ОШИБКА при скачивании, пробуем batch версию...
    call download_src_files.bat "%TARGET_DIR%"
)

echo.
echo ========================================
echo Готово! Файлы скачаны в: %TARGET_DIR%
echo ========================================
pause