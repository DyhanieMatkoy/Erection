@echo off
chcp 65001 > nul
echo Установка системы управления рабочим временем...
echo.

REM Создаем папку приложения
if not exist "%PROGRAMFILES%\ConstructionTimeManagement" (
    mkdir "%PROGRAMFILES%\ConstructionTimeManagement"
)

REM Копируем файлы
echo Копирование файлов...
xcopy /E /I /Y "ConstructionTimeManagement" "%PROGRAMFILES%\ConstructionTimeManagement\"

REM Создаем ярлык на рабочем столе
echo Создание ярлыка...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\ConstructionTimeManagement\ConstructionTimeManagement.exe'; $Shortcut.Save()"

REM Создаем ярлык в меню Пуск
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ConstructionTimeManagement" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\ConstructionTimeManagement"
)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\ConstructionTimeManagement\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\ConstructionTimeManagement\ConstructionTimeManagement.exe'; $Shortcut.Save()"

echo.
echo Установка завершена!
echo Ярлык создан на рабочем столе и в меню Пуск.
echo.
pause
