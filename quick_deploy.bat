@echo off
echo Быстрое развертывание проекта CTM...

:: Переходим в корень C:\
cd /d C:\

:: Удаляем старую версию если есть
if exist "C:\CTM" (
    echo Удаляем старую версию...
    rmdir /s /q "C:\CTM"
)

:: Клонируем проект
echo Скачиваем проект с GitHub...
git clone https://github.com/DyhanieMatkoy/CTM.git

if errorlevel 1 (
    echo ОШИБКА: Не удалось скачать проект
    pause
    exit /b 1
)

echo Проект успешно скачан в C:\CTM
echo Переходим в папку проекта...
cd /d "C:\CTM"

echo.
echo Готово! Проект находится в C:\CTM
pause