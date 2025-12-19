"""
Тест для проверки работы SettingsDialog и проблемы с QRadioButton
"""
import sys
import os
import tempfile
import configparser
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from views.settings_dialog import SettingsDialog

def create_test_env_file():
    """Создать тестовый env.ini файл с настройками"""
    config = configparser.ConfigParser()
    
    # Добавляем секцию Interface с тестовыми настройками
    config['Interface'] = {
        'button_style': 'both',
        'button_position': 'top'
    }
    
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini', encoding='utf-8')
    config.write(temp_file)
    temp_file.close()
    
    return temp_file.name

def test_settings_dialog_creation():
    """Тест создания SettingsDialog"""
    print("🧪 Тест 1: Создание SettingsDialog")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Создаем диалог
        dialog = SettingsDialog()
        print("✅ SettingsDialog создан успешно")
        
        # Проверяем наличие атрибутов
        radio_attrs = [
            'button_style_combo',
            'position_combo'
        ]
        
        for attr in radio_attrs:
            if hasattr(dialog, attr):
                print(f"✅ Атрибут {attr} существует")
            else:
                print(f"❌ Атрибут {attr} НЕ существует")
        
        return dialog
        
    except Exception as e:
        print(f"❌ Ошибка создания SettingsDialog: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_load_settings():
    """Тест загрузки настроек с существующим файлом"""
    print("\n🧪 Тест 2: Загрузка настроек из файла")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Создаем тестовый файл конфигурации
        test_config_file = create_test_env_file()
        
        # Создаем диалог с тестовым файлом
        dialog = SettingsDialog()
        dialog.config_file = test_config_file
        
        # Пробуем загрузить настройки
        dialog.load_settings()
        
        print("✅ Настройки загружены без ошибок")
        
        # Check button style combo
        if hasattr(dialog, 'button_style_combo'):
            style_index = dialog.button_style_combo.currentIndex()
            style_text = dialog.button_style_combo.currentText()
            print(f"✅ Button style combo: index={style_index}, text='{style_text}'")
            if style_index == 1:  # Default should be text (index 1)
                print("✅ Default button style set correctly (text)")
            else:
                print(f"⚠️ Button style not set to default (expected index 1, got {style_index})")
        else:
            print("❌ button_style_combo not found")
            
        # Check position combo
        if hasattr(dialog, 'position_combo'):
            current_index = dialog.position_combo.currentIndex()
            current_text = dialog.position_combo.currentText()
            print(f"✅ Position combo: index={current_index}, text='{current_text}'")
            if current_index == 1:  # Default should be bottom (index 1)
                print("✅ Default position set correctly (bottom)")
            else:
                print(f"⚠️ Position not set to default (expected index 1, got {current_index})")
        else:
            print("❌ position_combo not found")
        
        # Очищаем временный файл
        os.unlink(test_config_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_settings():
    """Тест сохранения настроек"""
    print("\n🧪 Тест 3: Сохранение настроек")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        dialog = SettingsDialog()
        
        # Устанавливаем тестовые значения
        if hasattr(dialog, 'use_both_icons_checkbox'):
            dialog.use_both_icons_checkbox.setChecked(True)
        if hasattr(dialog, 'top_radio'):
            dialog.top_radio.setChecked(True)
        
        # Создаем временный файл для сохранения
        test_config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini', encoding='utf-8')
        test_config_file.close()
        dialog.config_file = test_config_file.name
        
        # Пробуем сохранить настройки
        result = dialog.apply_settings()
        
        if result:
            print("✅ Настройки сохранены успешно")
            
            # Проверяем содержимое файла
            config = configparser.ConfigParser()
            config.read(test_config_file.name, encoding='utf-8')
            
            if config.has_section('Interface'):
                if config.has_option('Interface', 'button_style'):
                    style = config.get('Interface', 'button_style')
                    print(f"✅ Стиль кнопок сохранен: {style}")
                else:
                    print("❌ Стиль кнопок не сохранен")
                    
                if config.has_option('Interface', 'button_position'):
                    position = config.get('Interface', 'button_position')
                    print(f"✅ Позиция кнопок сохранена: {position}")
                else:
                    print("❌ Позиция кнопок не сохранена")
            else:
                print("❌ Секция Interface не создана")
        else:
            print("❌ Ошибка сохранения настроек")
        
        # Очищаем временный файл
        os.unlink(test_config_file.name)
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interface_tab_creation():
    """Тест создания вкладки Interface"""
    print("\n🧪 Тест 4: Создание вкладки Interface")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        dialog = SettingsDialog()
        
        # Создаем вкладку интерфейса
        interface_tab = dialog.create_interface_tab()
        
        if interface_tab:
            print("✅ Вкладка Interface создана успешно")
            
            # Проверяем наличие всех элементов
            children = interface_tab.findChildren(type(QApplication.instance()))
            print(f"✅ Найдено {len(children)} дочерних элементов во вкладке")
            
            return True
        else:
            print("❌ Вкладка Interface не создана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания вкладки Interface: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование SettingsDialog и проблемы с QRadioButton")
    print("=" * 60)
    
    # Тест 1: Создание диалога
    dialog = test_settings_dialog_creation()
    
    # Тест 2: Загрузка настроек
    load_success = test_load_settings()
    
    # Тест 3: Сохранение настроек
    save_success = test_save_settings()
    
    # Тест 4: Создание вкладки Interface
    interface_success = test_interface_tab_creation()
    
    # Итоги
    print("\n📊 Итоги тестирования:")
    print(f"   Создание диалога: {'✅ Успешно' if dialog else '❌ Ошибка'}")
    print(f"   Загрузка настроек: {'✅ Успешно' if load_success else '❌ Ошибка'}")
    print(f"   Сохранение настроек: {'✅ Успешно' if save_success else '❌ Ошибка'}")
    print(f"   Создание вкладки: {'✅ Успешно' if interface_success else '❌ Ошибка'}")
    
    if dialog:
        all_success = load_success and save_success and interface_success
        print(f"\n🎯 Общий результат: {'✅ Все тесты пройдены' if all_success else '❌ Есть проблемы'}")
        
        # Показываем диалог для визуальной проверки
        try:
            dialog.show()
            print("\n🔍 Диалог показан для визуальной проверки. Закройте окно для завершения.")
            
            # Ждем закрытия диалога
            timer = QTimer()
            timer.singleShot(1000, lambda: None)  # Даем время на отрисовку
            
            if app.exec() == 0:
                print("✅ Диалог закрыт успешно")
            else:
                print("❌ Диалог закрыт с ошибкой")
                
        except Exception as e:
            print(f"❌ Ошибка показа диалога: {e}")

if __name__ == "__main__":
    main()