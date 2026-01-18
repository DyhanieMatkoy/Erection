#!/usr/bin/env python3
"""
Тестирование исправлений упаковки десктоп-приложения
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path


def test_admin_user_creation():
    """Тестирует создание пользователя admin"""
    print("🧪 Тестируем создание пользователя admin...")
    
    try:
        # Создаем временную БД
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        # Инициализируем БД
        from src.data.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # Сбрасываем singleton для чистого теста
        DatabaseManager._instance = None
        db_manager = DatabaseManager()
        
        success = db_manager.initialize(test_db_path)
        if not success:
            print("❌ Не удалось инициализировать БД")
            return False
        
        # Проверяем, что пользователь admin создан
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            username, role = admin_user
            print(f"✅ Пользователь admin найден: {username}, роль: {role}")
            
            # Проверяем пароль
            cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
            password_hash = cursor.fetchone()[0]
            
            # Проверяем хеш
            import hashlib
            expected_hash = hashlib.sha256("admin".encode('utf-8')).hexdigest()
            
            if password_hash == expected_hash:
                print("✅ Пароль admin корректный")
            else:
                print(f"❌ Неправильный хеш пароля: {password_hash[:20]}...")
                print(f"   Ожидался: {expected_hash[:20]}...")
            
            # Проверяем запись в persons
            cursor.execute("SELECT full_name FROM persons WHERE user_id = (SELECT id FROM users WHERE username = 'admin')")
            person = cursor.fetchone()
            
            if person:
                print(f"✅ Запись в persons создана: {person[0]}")
            else:
                print("❌ Запись в persons не найдена")
            
        else:
            print("❌ Пользователь admin не найден")
            return False
        
        conn.close()
        
        # Очищаем
        os.unlink(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def test_auth_service():
    """Тестирует аутентификацию"""
    print("\n🧪 Тестируем аутентификацию...")
    
    try:
        # Создаем временную БД
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        # Инициализируем БД
        from src.data.database_manager import DatabaseManager
        DatabaseManager._instance = None
        db_manager = DatabaseManager()
        db_manager.initialize(test_db_path)
        
        # Тестируем аутентификацию
        from src.services.auth_service import AuthService
        auth_service = AuthService()
        
        # Пытаемся войти
        user = auth_service.login("admin", "admin")
        
        if user:
            print(f"✅ Аутентификация успешна: {user.username}, роль: {user.role}")
            
            # Проверяем права
            if auth_service.has_permission("create", "estimate"):
                print("✅ Права администратора работают")
            else:
                print("❌ Права администратора не работают")
                
        else:
            print("❌ Аутентификация не удалась")
            return False
        
        # Очищаем
        os.unlink(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования аутентификации: {e}")
        return False


def test_working_directory_fix():
    """Тестирует исправление рабочей директории"""
    print("\n🧪 Тестируем исправление рабочей директории...")
    
    try:
        # Проверяем main.py
        with open("main.py", 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        if "os.chdir" in main_content and "_MEIPASS" in main_content:
            print("✅ main.py содержит исправление рабочей директории")
        else:
            print("❌ main.py не содержит исправление рабочей директории")
            return False
        
        # Проверяем install.bat
        install_path = Path("desktop_package/install.bat")
        if install_path.exists():
            with open(install_path, 'r', encoding='utf-8') as f:
                install_content = f.read()
            
            if "WorkingDirectory" in install_content:
                print("✅ install.bat содержит исправление WorkingDirectory")
            else:
                print("❌ install.bat не содержит исправление WorkingDirectory")
                return False
        else:
            print("❌ install.bat не найден")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки файлов: {e}")
        return False


def test_package_structure():
    """Проверяет структуру пакета"""
    print("\n🧪 Проверяем структуру пакета...")
    
    required_files = [
        "desktop_package/install.bat",
        "desktop_package/uninstall.bat", 
        "desktop_package/README.txt",
        "src/data/initial_data.py"
    ]
    
    all_good = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - отсутствует")
            all_good = False
    
    # Проверяем содержимое initial_data.py
    try:
        from src.data.initial_data import ensure_admin_user_exists, create_initial_admin_user
        print("✅ Модуль initial_data импортируется корректно")
    except ImportError as e:
        print(f"❌ Ошибка импорта initial_data: {e}")
        all_good = False
    
    return all_good


def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование исправлений упаковки десктоп-приложения")
    print("=" * 60)
    
    tests = [
        ("Структура пакета", test_package_structure),
        ("Создание пользователя admin", test_admin_user_creation),
        ("Аутентификация", test_auth_service),
        ("Исправление рабочей директории", test_working_directory_fix),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name}: НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"💥 {test_name}: ОШИБКА - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    print("=" * 60)
    
    if passed == total:
        print("🎉 Все тесты пройдены! Исправления работают корректно.")
        print("\nМожно приступать к упаковке:")
        print("python package_desktop.py")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте исправления.")
        print("\nДля исправления проблем запустите:")
        print("python fix_desktop_packaging.py")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)