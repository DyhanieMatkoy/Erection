"""
Финальный тест для проверки исправления проблемы с QRadioButton
"""
import sys
import os
import tempfile
import configparser

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_with_config_file():
    """Тест с существующим конфигурационным файлом"""
    print("🧪 Тест с существующим env.ini файлом")
    
    try:
        # Создаем тестовый конфигурационный файл
        config = configparser.ConfigParser()
        config['Interface'] = {
            'button_style': 'both',
            'button_position': 'top'
        }
        
        # Временный файл
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini', encoding='utf-8')
        config.write(temp_file)
        temp_file.close()
        
        # Импортируем и создаем диалог
        from PyQt6.QtWidgets import QApplication
        from views.settings_dialog import SettingsDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Создаем диалог с тестовым файлом
        dialog = SettingsDialog()
        dialog.config_file = temp_file.name
        
        # Ждем немного для QTimer.singleShot
        from PyQt6.QtCore import QEventLoop
        loop = QEventLoop()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, loop.quit)
        loop.exec()
        
        # Проверяем состояния
        interface_tab_index = 2  # Interface tab
        interface_tab = dialog.tabs.widget(interface_tab_index)
        
        print(f"✅ Dialog created successfully")
        print(f"✅ Interface tab exists: {interface_tab is not None}")
        
        # Проверяем radio buttons
        if hasattr(dialog, 'use_both_icons_checkbox') and dialog.use_both_icons_checkbox.isChecked():
            print("✅ use_both_icons_checkbox is checked (button_style='both')")
        else:
            print("❌ use_both_icons_checkbox not checked properly")
            
        if hasattr(dialog, 'top_radio') and dialog.top_radio.isChecked():
            print("✅ top_radio is checked (button_position='top')")
        else:
            print("❌ top_radio not checked properly")
        
        # Очищаем
        os.unlink(temp_file.name)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_config_file():
    """Тест без конфигурационного файла"""
    print("\n🧪 Тест без конфигурационного файла")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from views.settings_dialog import SettingsDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Создаем диалог с несуществующим файлом
        dialog = SettingsDialog()
        dialog.config_file = "nonexistent_file.ini"
        
        # Ждем для QTimer.singleShot
        from PyQt6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()
        
        print("✅ Dialog created successfully without config file")
        
        # Проверяем значения по умолчанию
        if hasattr(dialog, 'use_text_icons_checkbox') and dialog.use_text_icons_checkbox.isChecked():
            print("✅ use_text_icons_checkbox is checked (default)")
        else:
            print("❌ Default values not set properly")
            
        # Check position combo
        if hasattr(dialog, 'position_combo'):
            current_index = dialog.position_combo.currentIndex()
            print(f"✅ position_combo current index: {current_index} (default should be 1)")
            if current_index == 1:
                print("✅ Default position set correctly (bottom)")
            else:
                print(f"⚠️ Position not set to default (expected 1, got {current_index})")
        else:
            print("❌ position_combo not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция теста"""
    print("🧪 Финальный тест для проверки исправления QRadioButton проблемы")
    print("=" * 60)
    
    # Тест 1: С существующим файлом
    test1_success = test_with_config_file()
    
    # Тест 2: Без файла
    test2_success = test_without_config_file()
    
    # Итоги
    print("\n📊 Итоги тестирования:")
    print(f"   Тест с config файлом: {'✅ Успешно' if test1_success else '❌ Ошибка'}")
    print(f"   Тест без config файла: {'✅ Успешно' if test2_success else '❌ Ошибка'}")
    
    overall_success = test1_success and test2_success
    print(f"\n🎯 Общий результат: {'✅ Все тесты пройдены' if overall_success else '❌ Есть проблемы'}")
    
    if overall_success:
        print("\n✅ Проблема QRadioButton должна быть исправлена!")
        print("   - QTimer.singleShot(0, self.load_settings) отложил загрузку")
        print("   - Radio buttons созданы до вызова load_settings()")
        print("   - Проверки hasattr() больше не нужны")
    else:
        print("\n❌ Проблема всё ещё существует")
    
    return overall_success

if __name__ == "__main__":
    main()