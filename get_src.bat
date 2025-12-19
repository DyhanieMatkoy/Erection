@echo off
echo ========================================
echo Быстрое скачивание src файлов
echo ========================================

:: Проверяем есть ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден, используем batch версию...
    call download_src_files.bat %*
) else (
    echo Используем Python версию для полного скачивания...
    python download_src_files.py %*
)