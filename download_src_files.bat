@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Скачивание файлов src с GitHub
echo ========================================

:: Проверяем наличие curl
curl --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: curl не установлен или не найден в PATH
    echo curl обычно входит в состав Windows 10/11
    pause
    exit /b 1
)

:: Устанавливаем переменные
set REPO_OWNER=DyhanieMatkoy
set REPO_NAME=Erection
set BRANCH=main
set SOURCE_PATH=src
set API_URL=https://api.github.com/repos/%REPO_OWNER%/%REPO_NAME%/contents/%SOURCE_PATH%

:: Определяем целевую папку
if "%~1"=="" (
    set TARGET_DIR=%cd%\src
    echo Целевая папка не указана, используется текущая: %TARGET_DIR%
) else (
    set TARGET_DIR=%~1
    echo Целевая папка: %TARGET_DIR%
)

echo Репозиторий: https://github.com/%REPO_OWNER%/%REPO_NAME%
echo Исходная папка: %SOURCE_PATH%
echo Ветка: %BRANCH%
echo.

:: Создаем целевую папку если не существует
if not exist "%TARGET_DIR%" (
    echo Создаем папку: %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

:: Временный файл для списка файлов
set TEMP_FILE=%TEMP%\github_files_list.json

echo Получаем список файлов из GitHub API...
curl -s -o "%TEMP_FILE%" "%API_URL%?ref=%BRANCH%"

if errorlevel 1 (
    echo ОШИБКА: Не удалось получить список файлов
    echo Проверьте подключение к интернету
    pause
    exit /b 1
)

:: Проверяем что файл не пустой
for %%A in ("%TEMP_FILE%") do set FILE_SIZE=%%~zA
if %FILE_SIZE%==0 (
    echo ОШИБКА: Получен пустой ответ от GitHub API
    pause
    exit /b 1
)

echo Обрабатываем список файлов...

:: Используем PowerShell для парсинга JSON и скачивания файлов
powershell -Command "& {
    $jsonContent = Get-Content '%TEMP_FILE%' -Raw | ConvertFrom-Json
    $totalFiles = $jsonContent.Count
    $currentFile = 0
    
    Write-Host \"Найдено файлов: $totalFiles\"
    Write-Host \"\"
    
    foreach ($item in $jsonContent) {
        $currentFile++
        
        if ($item.type -eq 'file') {
            $fileName = $item.name
            $downloadUrl = $item.download_url
            $targetPath = Join-Path '%TARGET_DIR%' $fileName
            
            Write-Host \"[$currentFile/$totalFiles] Скачиваем: $fileName\"
            
            try {
                Invoke-WebRequest -Uri $downloadUrl -OutFile $targetPath -ErrorAction Stop
                Write-Host \"  ✓ Успешно скачан\"
            }
            catch {
                Write-Host \"  ✗ Ошибка: $($_.Exception.Message)\" -ForegroundColor Red
            }
        }
        elseif ($item.type -eq 'dir') {
            Write-Host \"[$currentFile/$totalFiles] Пропускаем папку: $($item.name)\"
        }
    }
    
    Write-Host \"\"
    Write-Host \"Скачивание завершено!\"
}"

:: Удаляем временный файл
if exist "%TEMP_FILE%" del "%TEMP_FILE%"

echo.
echo ========================================
echo ЗАВЕРШЕНО!
echo ========================================
echo Файлы скачаны в: %TARGET_DIR%
echo.

:: Показываем список скачанных файлов
echo Скачанные файлы:
dir /b "%TARGET_DIR%"

echo.
pause