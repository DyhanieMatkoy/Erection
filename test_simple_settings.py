"""
Простой тест для отладки QRadioButton проблемы
"""
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import():
    """Тест импорта модулей"""
    print("🧪 Тест импорта...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QRadioButton, QGroupBox, QVBoxLayout
        print("✅ PyQt6 импортирован успешно")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            print("✅ QApplication создан")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта PyQt6: {e}")
        return False

def test_settings_dialog_import():
    """Тест импорта SettingsDialog"""
    print("\n🧪 Тест импорта SettingsDialog...")
    
    try:
        from views.settings_dialog import SettingsDialog
        print("✅ SettingsDialog импортирован успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта SettingsDialog: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings_dialog_creation():
    """Тест создания SettingsDialog"""
    print("\n🧪 Тест создания SettingsDialog...")
    
    try:
        from views.settings_dialog import SettingsDialog
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        dialog = SettingsDialog()
        print("✅ SettingsDialog создан успешно")
        
        # Проверяем атрибуты
        attrs_to_check = [
            'button_style_combo',
            'position_combo'
        ]
        
        for attr in attrs_to_check:
            if hasattr(dialog, attr):
                obj = getattr(dialog, attr)
                print(f"✅ {attr}: {type(obj)} - существует")
            else:
                print(f"❌ {attr}: НЕ существует")
        
        return dialog
        
    except Exception as e:
        print(f"❌ Ошибка создания SettingsDialog: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_interface_tab_creation():
    """Тест создания вкладки Interface"""
    print("\n🧪 Тест создания вкладки Interface...")
    
    try:
        from views.settings_dialog import SettingsDialog
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        dialog = SettingsDialog()
        
        # Пробуем создать вкладку
        interface_tab = dialog.create_interface_tab()
        
        if interface_tab:
            print("✅ Вкладка Interface создана успешно")
            return interface_tab
        else:
            print("❌ Вкладка Interface не создана")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка создания вкладки Interface: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_load_settings_simple():
    """Тест загрузки настроек без файла"""
    print("\n🧪 Тест загрузки настроек без файла...")
    
    try:
        from views.settings_dialog import SettingsDialog
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        dialog = SettingsDialog()
        
        # Устанавливаем несуществующий файл конфигурации
        dialog.config_file = "nonexistent.ini"
        
        # Пробуем загрузить настройки
        dialog.load_settings()
        print("✅ Загрузка настроек без файла выполнена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🧪 Простой тест для отладки QRadioButton проблемы")
    print("=" * 60)
    
    # Тест 1: Импорт
    if not test_import():
        print("❌ PyQt6 не работает, дальнейшие тесты невозможны")
        return
    
    # Тест 2: Импорт SettingsDialog
    if not test_settings_dialog_import():
        print("❌ SettingsDialog не импортируется, дальнейшие тесты невозможны")
        return
    
    # Тест 3: Создание SettingsDialog
    dialog = test_settings_dialog_creation()
    if not dialog:
        print("❌ SettingsDialog не создается, дальнейшие тесты невозможны")
        return
    
    # Тест 4: Создание вкладки
    interface_tab = test_interface_tab_creation()
    
    # Тест 5: Загрузка настроек
    load_success = test_load_settings_simple()
    
    # Итоги
    print("\n📊 Итоги простого теста:")
    print(f"   Импорт PyQt6: ✅ Успешно")
    print(f"   Импорт SettingsDialog: ✅ Успешно")
    print(f"   Создание SettingsDialog: ✅ Успешно")
    print(f"   Создание вкладки: {'✅ Успешно' if interface_tab else '❌ Ошибка'}")
    print(f"   Загрузка настроек: {'✅ Успешно' if load_success else '❌ Ошибка'}")
    
    if interface_tab and load_success:
        print("\n🎯 Простые тесты пройдены! Проблема может быть в:")
        print("   1. Конфликте с существующим env.ini файлом")
        print("   2. Проблеме с жизненным циклом Qt объектов")
        print("   3. Порядке инициализации компонентов")

if __name__ == "__main__":
    main()