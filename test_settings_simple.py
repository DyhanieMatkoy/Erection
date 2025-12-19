"""
Простой тест для проверки SettingsDialog без ошибок импорта
"""
import sys
import os

def test_settings_directly():
    """Тестируем SettingsDialog напрямую"""
    try:
        # Устанавливаем правильный PYTHONPATH
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(current_dir, 'src')
        
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        print("🔍 PYTHONPATH:", sys.path[:3])
        
        # Импортируем Qt
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Импортируем SettingsDialog напрямую
        import views.settings_dialog
        SettingsDialog = views.settings_dialog.SettingsDialog
        print("✅ SettingsDialog импортирован")
        
        # Создаем диалог
        print("🔧 Создание SettingsDialog...")
        dialog = SettingsDialog()
        print("✅ SettingsDialog создан без ошибок")
        
        # Проверяем атрибуты
        radio_attrs = ['use_font_icons_checkbox', 'use_text_icons_checkbox', 
                      'use_both_icons_checkbox', 'top_radio', 'bottom_radio', 'both_radio']
        
        all_exist = True
        for attr in radio_attrs:
            if hasattr(dialog, attr):
                obj = getattr(dialog, attr)
                print(f"✅ {attr}: {type(obj).__name__}")
            else:
                print(f"❌ {attr}: НЕ существует")
                all_exist = False
        
        if all_exist:
            print("🎯 Все radio buttons существуют!")
            
            # Пробуем загрузить настройки
            try:
                print("🔧 Загрузка настроек...")
                dialog.load_settings()
                print("✅ Настройки загружены без ошибок")
                return True
            except Exception as e:
                print(f"❌ Ошибка загрузки настроек: {e}")
                return False
        else:
            print("❌ Не все radio buttons созданы")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Тест SettingsDialog без проблем импорта")
    print("=" * 60)
    
    success = test_settings_directly()
    
    if success:
        print("\n🎯 SettingsDialog работает корректно!")
        print("   - Все radio buttons созданы")
        print("   - Настройки загружаются без ошибок")
        print("   - Проблема QRadioButton решена")
    else:
        print("\n❌ Проблема всё ещё существует")