"""
Пример использования настроек селектора работ в desktop версии
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def demonstrate_settings_dialog():
    """Демонстрация диалога настроек"""
    print("🔧 Демонстрация диалога настроек селектора работ")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.dialogs.work_selector_settings_dialog import WorkSelectorSettingsDialog
        from src.services.user_settings_service import UserSettingsService
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_id = 4  # Test user
        settings_service = UserSettingsService()
        
        print("1. Создание диалога настроек...")
        dialog = WorkSelectorSettingsDialog(user_id=user_id)
        print("   ✅ Диалог создан успешно")
        
        print("\n2. Загрузка текущих настроек...")
        current_settings = settings_service.get_work_selector_settings(user_id)
        print(f"   Текущие настройки: {current_settings}")
        
        print("\n3. Демонстрация различных конфигураций...")
        
        # Конфигурация для опытных пользователей
        expert_settings = {
            'open_modal': False,
            'default_hierarchy_mode': 'flat',
            'show_hierarchy_controls': True,
            'auto_expand_groups': False,
            'remember_last_position': True
        }
        
        print("   Настройки для опытных пользователей:")
        print("   - Немодальное окно (не блокирует работу)")
        print("   - Плоский список (все работы сразу)")
        print("   - Показывать элементы управления")
        print("   - Не разворачивать группы автоматически")
        print("   - Запоминать последнюю позицию")
        
        success = settings_service.set_work_selector_settings(user_id, expert_settings)
        if success:
            print("   ✅ Настройки для экспертов применены")
        
        # Конфигурация для новичков
        beginner_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True,
            'remember_last_position': True
        }
        
        print("\n   Настройки для новичков:")
        print("   - Модальное окно (фокус на выборе)")
        print("   - Иерархическое дерево (навигация по группам)")
        print("   - Показывать элементы управления")
        print("   - Автоматически разворачивать группы")
        print("   - Запоминать последнюю позицию")
        
        success = settings_service.set_work_selector_settings(user_id, beginner_settings)
        if success:
            print("   ✅ Настройки для новичков применены")
        
        # Конфигурация для работы с большими списками
        performance_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'breadcrumb',
            'show_hierarchy_controls': False,
            'auto_expand_groups': False,
            'remember_last_position': True
        }
        
        print("\n   Настройки для больших списков:")
        print("   - Модальное окно")
        print("   - Режим с путями (показывать полный путь)")
        print("   - Скрыть лишние элементы управления")
        print("   - Не разворачивать группы (экономия памяти)")
        print("   - Запоминать последнюю позицию")
        
        success = settings_service.set_work_selector_settings(user_id, performance_settings)
        if success:
            print("   ✅ Настройки для производительности применены")
        
        # Возврат к настройкам по умолчанию
        default_settings = {
            'open_modal': True,
            'default_hierarchy_mode': 'tree',
            'show_hierarchy_controls': True,
            'auto_expand_groups': True,
            'remember_last_position': True
        }
        
        settings_service.set_work_selector_settings(user_id, default_settings)
        print("\n   ✅ Настройки возвращены к значениям по умолчанию")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации диалога настроек: {e}")
        return False


def demonstrate_enhanced_selector():
    """Демонстрация улучшенного селектора работ"""
    print("\n🚀 Демонстрация улучшенного селектора работ")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.dialogs.enhanced_work_selector_dialog import EnhancedWorkSelectorDialog
        from src.services.user_settings_service import UserSettingsService
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        user_id = 4
        settings_service = UserSettingsService()
        
        print("1. Создание улучшенного селектора...")
        dialog = EnhancedWorkSelectorDialog(user_id=user_id)
        print("   ✅ Селектор создан успешно")
        
        print("\n2. Тестирование различных режимов иерархии...")
        
        for mode in ['flat', 'tree', 'breadcrumb']:
            print(f"   Переключение в режим '{mode}'...")
            dialog.set_hierarchy_mode(mode)
            current_mode = dialog.settings.get('default_hierarchy_mode')
            if current_mode == mode:
                print(f"   ✅ Режим '{mode}' активирован")
            else:
                print(f"   ❌ Ошибка переключения в режим '{mode}'")
        
        print("\n3. Тестирование настроек видимости...")
        
        # Скрыть элементы управления
        dialog.settings['show_hierarchy_controls'] = False
        dialog.update_controls_visibility()
        print("   ✅ Элементы управления скрыты")
        
        # Показать элементы управления
        dialog.settings['show_hierarchy_controls'] = True
        dialog.update_controls_visibility()
        print("   ✅ Элементы управления показаны")
        
        print("\n4. Тестирование модального/немодального режима...")
        
        # Тест модального режима
        dialog.settings['open_modal'] = True
        dialog.apply_settings()
        if dialog.isModal():
            print("   ✅ Модальный режим активирован")
        else:
            print("   ❌ Ошибка активации модального режима")
        
        # Тест немодального режима
        dialog.settings['open_modal'] = False
        dialog.apply_settings()
        if not dialog.isModal():
            print("   ✅ Немодальный режим активирован")
        else:
            print("   ❌ Ошибка активации немодального режима")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации улучшенного селектора: {e}")
        return False


def demonstrate_integration():
    """Демонстрация интеграции с формой сметы"""
    print("\n🔗 Демонстрация интеграции с формой сметы")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.views.estimate_document_form import EstimateDocumentForm
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("1. Создание формы сметы...")
        form = EstimateDocumentForm(0)  # Новая смета
        print("   ✅ Форма сметы создана")
        
        print("\n2. Проверка интеграции настроек...")
        
        # Проверка наличия кнопки настроек
        if hasattr(form, 'work_selector_settings_button'):
            print("   ✅ Кнопка настроек селектора найдена")
            
            # Проверка метода обработки
            if hasattr(form, 'on_work_selector_settings'):
                print("   ✅ Метод обработки настроек найден")
            else:
                print("   ❌ Метод обработки настроек не найден")
                return False
        else:
            print("   ❌ Кнопка настроек селектора не найдена")
            return False
        
        print("\n3. Проверка использования улучшенного селектора...")
        
        # Проверка метода выбора работы
        if hasattr(form, 'on_select_work'):
            print("   ✅ Метод выбора работы найден")
            
            # Проверка, что используется EnhancedWorkSelectorDialog
            import inspect
            source = inspect.getsource(form.on_select_work)
            if 'EnhancedWorkSelectorDialog' in source:
                print("   ✅ Используется улучшенный селектор работ")
            else:
                print("   ❌ Не используется улучшенный селектор работ")
                return False
        else:
            print("   ❌ Метод выбора работы не найден")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации интеграции: {e}")
        return False


def main():
    """Запуск всех демонстраций"""
    print("🎯 Демонстрация настроек селектора работ для Desktop версии")
    print("=" * 70)
    
    success1 = demonstrate_settings_dialog()
    success2 = demonstrate_enhanced_selector()
    success3 = demonstrate_integration()
    
    print("\n" + "=" * 70)
    if success1 and success2 and success3:
        print("✅ Все демонстрации прошли успешно!")
        print("\nВозможности:")
        print("• Настройка модального/немодального режима")
        print("• Выбор режима отображения иерархии (плоский/дерево/пути)")
        print("• Управление видимостью элементов интерфейса")
        print("• Автоматическое разворачивание групп")
        print("• Запоминание последней позиции")
        print("• Интеграция с формой сметы")
        print("• Сохранение персональных настроек")
        return True
    else:
        print("❌ Некоторые демонстрации не прошли!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)