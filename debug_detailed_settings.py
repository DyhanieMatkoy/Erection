"""
Детальный тест для воспроизведения проблемы QRadioButton
"""
import sys
import os
import traceback

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_settings_creation():
    """Детальная отладка создания SettingsDialog"""
    print("🔍 Детальная отладка создания SettingsDialog")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 импортирован")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            print("✅ QApplication создан")
        
        # Отслеживаем каждый шаг создания
        print("\n🔧 Шаг 1: Импорт SettingsDialog")
        from views.settings_dialog import SettingsDialog
        print("✅ SettingsDialog импортирован")
        
        print("\n🔧 Шаг 2: Создание экземпляра")
        dialog = SettingsDialog()
        print("✅ SettingsDialog создан")
        
        print("\n🔧 Шаг 3: Проверка атрибутов")
        attrs_to_check = [
            'button_style_combo',
            'position_combo'
        ]
        
        for attr in attrs_to_check:
            if hasattr(dialog, attr):
                obj = getattr(dialog, attr)
                obj_type = type(obj).__name__
                print(f"✅ {attr}: {obj_type}")
                
                # Проверяем, что это действительно QRadioButton
                try:
                    if hasattr(obj, 'isChecked'):
                        is_checked = obj.isChecked()
                        print(f"   - isChecked(): {is_checked}")
                    if hasattr(obj, 'setChecked'):
                        print(f"   - has setChecked(): True")
                except Exception as e:
                    print(f"   - Ошибка доступа к методам: {e}")
            else:
                print(f"❌ {attr}: НЕ существует")
        
        print("\n🔧 Шаг 4: Проверка метода load_settings")
        if hasattr(dialog, 'load_settings'):
            print("✅ load_settings метод существует")
            
            try:
                print("   Попытка вызвать load_settings()...")
                dialog.load_settings()
                print("✅ load_settings() выполнен без ошибок")
            except Exception as e:
                print(f"❌ Ошибка в load_settings(): {e}")
                print(f"   Тип ошибки: {type(e).__name__}")
                traceback.print_exc()
        else:
            print("❌ load_settings метод НЕ существует")
        
        print("\n🔧 Шаг 5: Показ диалога")
        try:
            dialog.show()
            print("✅ Dialog показан")
            
            # Небольшая задержка для отрисовки
            from PyQt6.QtCore import QTimer
            from PyQt6.QtCore import QEventLoop
            
            loop = QEventLoop()
            QTimer.singleShot(2000, loop.quit)  # 2 секунды
            print("   Диалог будет показан 2 секунды...")
            
            if loop.exec():
                print("✅ Диалог закрыт пользователем")
            else:
                print("✅ Диалог закрыт по таймеру")
                
        except Exception as e:
            print(f"❌ Ошибка показа диалога: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()
        return False

def test_with_real_env_file():
    """Тест с реальным env.ini файлом"""
    print("\n🔍 Тест с реальным env.ini файлом")
    print("=" * 40)
    
    try:
        # Проверяем наличие env.ini
        env_path = os.path.join(os.getcwd(), 'env.ini')
        if os.path.exists(env_path):
            print(f"✅ env.ini найден: {env_path}")
            
            # Читаем содержимое
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("📄 Содержимое env.ini:")
                print(content)
                
            # Тестируем с реальным файлом
            from PyQt6.QtWidgets import QApplication
            from views.settings_dialog import SettingsDialog
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            dialog = SettingsDialog()
            dialog.config_file = env_path
            
            print("\n🔧 Попытка загрузки реального env.ini...")
            try:
                # Ждем немного для QTimer
                from PyQt6.QtCore import QEventLoop, QTimer
                loop = QEventLoop()
                QTimer.singleShot(500, loop.quit)
                loop.exec()
                
                print("✅ Реальный env.ini загружен без ошибок")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка загрузки реального env.ini: {e}")
                traceback.print_exc()
                return False
        else:
            print("❌ env.ini не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста с реальным файлом: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🔍 Детальная отладка проблемы QRadioButton")
    print("=" * 80)
    
    # Тест 1: Детальное создание
    debug_success = debug_settings_creation()
    
    # Тест 2: С реальным env.ini
    real_file_success = test_with_real_env_file()
    
    # Итоги
    print("\n📊 Итоги детальной отладки:")
    print(f"   Детальное создание: {'✅ Успешно' if debug_success else '❌ Ошибка'}")
    print(f"   Тест с env.ini: {'✅ Успешно' if real_file_success else '❌ Ошибка'}")
    
    if debug_success and real_file_success:
        print("\n🎯 Все тесты пройдены! Проблема может быть:")
        print("   1. В специфической версии PyQt6")
        print("   2. В окружении/конфигурации системы")
        print("   3. В многопоточном доступе к Qt объектам")
        print("   4. В конфликте с другими компонентами")
    else:
        print("\n❌ Проблема воспроизведена в тестах")

if __name__ == "__main__":
    main()