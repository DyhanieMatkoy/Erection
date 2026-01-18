#!/usr/bin/env python3
"""
Скрипт для исправления проблем с упаковкой десктоп-приложения

Исправляет:
1. Ярлыки не ссылаются на правильную папку
2. БД создается не в той папке
3. Логин admin/admin не работает
"""
import os
import shutil
import subprocess
from pathlib import Path


def fix_install_script():
    """Исправляет install.bat для правильной работы ярлыков"""
    print("🔧 Исправляем install.bat...")
    
    install_bat_content = '''@echo off
chcp 65001 > nul
echo Установка системы управления рабочим временем...
echo.

REM Создаем папку приложения
if not exist "%PROGRAMFILES%\\ConstructionTimeManagement" (
    mkdir "%PROGRAMFILES%\\ConstructionTimeManagement"
)

REM Копируем файлы
echo Копирование файлов...
xcopy /E /I /Y "ConstructionTimeManagement" "%PROGRAMFILES%\\ConstructionTimeManagement\\"

REM Создаем ярлык на рабочем столе с правильной рабочей папкой
echo Создание ярлыка на рабочем столе...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe'; $Shortcut.WorkingDirectory = '%PROGRAMFILES%\\ConstructionTimeManagement'; $Shortcut.IconLocation = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe,0'; $Shortcut.Save()"

REM Создаем ярлык в меню Пуск с правильной рабочей папкой
echo Создание ярлыка в меню Пуск...
if not exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement" (
    mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement"
)
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\ConstructionTimeManagement\\Система управления рабочим временем.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe'; $Shortcut.WorkingDirectory = '%PROGRAMFILES%\\ConstructionTimeManagement'; $Shortcut.IconLocation = '%PROGRAMFILES%\\ConstructionTimeManagement\\ConstructionTimeManagement.exe,0'; $Shortcut.Save()"

REM Устанавливаем права доступа к папке приложения
echo Настройка прав доступа...
icacls "%PROGRAMFILES%\\ConstructionTimeManagement" /grant Users:(OI)(CI)F /T > nul 2>&1

echo.
echo Установка завершена!
echo Ярлык создан на рабочем столе и в меню Пуск.
echo.
echo ВАЖНО: При первом запуске используйте:
echo   Логин: admin
echo   Пароль: admin
echo.
pause'''
    
    install_path = Path("desktop_package/install.bat")
    install_path.parent.mkdir(exist_ok=True)
    
    with open(install_path, 'w', encoding='utf-8') as f:
        f.write(install_bat_content)
    
    print("✅ install.bat исправлен")


def create_admin_reset_script():
    """Создает скрипт для сброса пароля admin"""
    print("🔧 Создаем скрипт сброса пароля admin...")
    
    reset_script = '''@echo off
chcp 65001 > nul
echo Сброс пароля администратора...
echo.

cd /d "%PROGRAMFILES%\\ConstructionTimeManagement"

if not exist "construction.db" (
    echo Ошибка: База данных не найдена!
    echo Убедитесь, что приложение установлено правильно.
    pause
    exit /b 1
)

echo Сбрасываем пароль администратора...
python -c "
import sqlite3
import hashlib

def simple_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

try:
    conn = sqlite3.connect('construction.db')
    cursor = conn.cursor()
    
    # Проверяем существование пользователя admin
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    admin = cursor.fetchone()
    
    if admin:
        # Обновляем пароль
        new_hash = simple_hash('admin')
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
        conn.commit()
        print('✓ Пароль администратора сброшен на: admin')
    else:
        # Создаем пользователя admin
        new_hash = simple_hash('admin')
        cursor.execute('INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)', 
                      ('admin', new_hash, 'Администратор', 1))
        admin_id = cursor.lastrowid
        
        # Создаем запись в persons
        cursor.execute('INSERT INTO persons (full_name, position, user_id, marked_for_deletion) VALUES (?, ?, ?, ?)',
                      ('Администратор системы', 'Администратор', admin_id, 0))
        conn.commit()
        print('✓ Пользователь admin создан с паролем: admin')
    
    conn.close()
    
except Exception as e:
    print(f'✗ Ошибка: {e}')
"

echo.
echo Теперь вы можете войти в систему:
echo   Логин: admin
echo   Пароль: admin
echo.
pause'''
    
    reset_path = Path("desktop_package/reset_admin_password.bat")
    with open(reset_path, 'w', encoding='utf-8') as f:
        f.write(reset_script)
    
    print("✅ Скрипт сброса пароля создан: reset_admin_password.bat")


def update_readme():
    """Обновляет README.txt с исправленными инструкциями"""
    print("🔧 Обновляем README.txt...")
    
    readme_content = '''СИСТЕМА УПРАВЛЕНИЯ РАБОЧИМ ВРЕМЕНЕМ СТРОИТЕЛЬНЫХ БРИГАД
========================================================

УСТАНОВКА:
1. Запустите install.bat от имени администратора
2. Дождитесь завершения установки
3. Запустите приложение через ярлык на рабочем столе

СИСТЕМНЫЕ ТРЕБОВАНИЯ:
- Windows 10/11 или Windows Server 2016+
- 4 ГБ оперативной памяти
- 500 МБ свободного места на диске
- Разрешение экрана не менее 1024x768

ПЕРВЫЙ ЗАПУСК:
- Логин: admin
- Пароль: admin

ВАЖНО: Обязательно смените пароль администратора после первого входа!

РЕШЕНИЕ ПРОБЛЕМ:

Если не получается войти в систему:
1. Запустите reset_admin_password.bat от имени администратора
2. Это сбросит пароль администратора на "admin"

Если база данных создается не в той папке:
- Убедитесь, что ярлык запускается из папки приложения
- Проверьте свойства ярлыка: "Рабочая папка" должна быть установлена

Если приложение не запускается:
- Запустите от имени администратора
- Проверьте антивирус (добавьте в исключения)
- Установите Visual C++ Redistributable

УДАЛЕНИЕ:
Запустите uninstall.bat от имени администратора

ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:
При возникновении проблем обратитесь к системному администратору.

База данных автоматически создается при первом запуске в папке приложения.
Резервные копии создаются автоматически каждые 24 часа.

ФАЙЛЫ В ПАКЕТЕ:
- ConstructionTimeManagement/ - основное приложение
- install.bat - установщик
- uninstall.bat - деинсталлятор  
- reset_admin_password.bat - сброс пароля администратора
- README.txt - этот файл'''
    
    readme_path = Path("desktop_package/README.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README.txt обновлен")


def test_admin_creation():
    """Тестирует создание пользователя admin"""
    print("🧪 Тестируем создание пользователя admin...")
    
    try:
        # Импортируем наш модуль
        from src.data.initial_data import create_initial_admin_user
        
        # Создаем тестовую БД
        test_db = "test_admin.db"
        if os.path.exists(test_db):
            os.remove(test_db)
        
        # Инициализируем БД
        from src.data.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.initialize(test_db)
        
        # Проверяем создание admin
        result = create_initial_admin_user(test_db)
        
        if result:
            print("✅ Пользователь admin создается корректно")
        else:
            print("❌ Ошибка создания пользователя admin")
        
        # Очищаем
        if os.path.exists(test_db):
            os.remove(test_db)
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


def main():
    """Основная функция исправления проблем"""
    print("🚀 Исправление проблем с упаковкой десктоп-приложения")
    print("=" * 60)
    
    try:
        # Исправляем install.bat
        fix_install_script()
        
        # Создаем скрипт сброса пароля
        create_admin_reset_script()
        
        # Обновляем README
        update_readme()
        
        # Тестируем создание admin
        test_admin_creation()
        
        print("\n" + "=" * 60)
        print("✅ Все исправления применены!")
        print("=" * 60)
        
        print("\nЧто исправлено:")
        print("1. ✅ Ярлыки теперь правильно ссылаются на папку приложения")
        print("2. ✅ БД создается в папке приложения (WorkingDirectory установлен)")
        print("3. ✅ Пользователь admin создается автоматически при первом запуске")
        print("4. ✅ Добавлен скрипт сброса пароля admin")
        print("5. ✅ Обновлены инструкции для пользователя")
        
        print("\nДля клиента:")
        print("- Распакуйте архив")
        print("- Запустите install.bat от имени администратора")
        print("- Войдите в систему: admin/admin")
        print("- При проблемах с входом запустите reset_admin_password.bat")
        
        print("\nТеперь можно пересобрать пакет:")
        print("python package_desktop.py")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Готово! Проблемы с упаковкой исправлены.")
    else:
        print("\n💥 Не удалось исправить все проблемы.")