@echo off
echo Быстрое развертывание проекта Erection...

:: Переходим в корень C:\
cd /d C:\

:: Удаляем старую версию если есть
if exist "C:\Erection" (
    echo Удаляем старую версию...
    rmdir /s /q "C:\Erection"
)

:: Клонируем проект
echo Скачиваем проект с GitHub...
git clone https://github.com/DyhanieMatkoy/Erection.git

if errorlevel 1 (
    echo ОШИБКА: Не удалось скачать проект
    pause
    exit /b 1
)

echo Проект успешно скачан в C:\Erection
echo Переходим в папку проекта...
cd /d "C:\Erection"

echo.
echo Готово! Проект находится в C:\Erection
pause