@echo off
chcp 65001 > nul
echo Удаление системы управления рабочим временем...
echo.

REM Удаляем ярлыки
del "%USERPROFILE%\Desktop\Система управления рабочим временем.lnk" 2>nul
rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ConstructionTimeManagement" 2>nul

REM Удаляем папку приложения
rmdir /S /Q "%PROGRAMFILES%\ConstructionTimeManagement" 2>nul

echo.
echo Удаление завершено!
echo.
pause
