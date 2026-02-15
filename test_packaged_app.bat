@echo off
chcp 65001 > nul
echo ========================================
echo   ТЕСТИРОВАНИЕ УПАКОВАННОГО ПРИЛОЖЕНИЯ
echo ========================================
echo.

if not exist "desktop_package\ConstructionTimeManagement\ConstructionTimeManagement.exe" (
    echo ❌ Упакованное приложение не найдено!
    echo Сначала запустите package_desktop.bat
    pause
    exit /b 1
)

echo ✅ Упакованное приложение найдено
echo 📁 Размер архива:
dir ConstructionTimeManagement_Desktop_v1.0.zip | findstr ".zip"

echo.
echo 🚀 Запуск приложения для тестирования...
echo (Приложение откроется в отдельном окне)
echo.

start "" "desktop_package\ConstructionTimeManagement\ConstructionTimeManagement.exe"

echo ✅ Приложение запущено!
echo.
echo 📋 Проверьте:
echo 1. Окно входа в систему открылось
echo 2. Можно войти с логином: admin, пароль: admin
echo 3. Основное окно приложения работает
echo 4. База данных создается автоматически
echo.
pause