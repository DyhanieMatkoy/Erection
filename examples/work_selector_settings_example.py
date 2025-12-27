"""
Пример использования настроек селектора работ
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.user_settings_service import UserSettingsService


def demonstrate_work_selector_settings():
    """Демонстрация работы с настройками селектора работ"""
    print("🔧 Демонстрация настроек селектора работ")
    print("=" * 50)
    
    # Создаем сервис
    settings_service = UserSettingsService()
    user_id = 4  # Тестовый пользователь
    
    # 1. Получаем текущие настройки
    print("1. Получение текущих настроек:")
    current_settings = settings_service.get_work_selector_settings(user_id)
    print(f"   Текущие настройки: {current_settings}")
    
    # 2. Изменяем настройки на немодальный режим
    print("\n2. Переключение на немодальный режим:")
    new_settings = {
        'open_modal': False,
        'default_hierarchy_mode': 'flat',
        'show_hierarchy_controls': True,
        'auto_expand_groups': False
    }
    
    success = settings_service.set_work_selector_settings(user_id, new_settings)
    if success:
        print("   ✅ Настройки успешно сохранены")
        
        # Проверяем, что настройки сохранились
        updated_settings = settings_service.get_work_selector_settings(user_id)
        print(f"   Обновленные настройки: {updated_settings}")
    else:
        print("   ❌ Ошибка сохранения настроек")
    
    # 3. Демонстрация различных режимов иерархии
    print("\n3. Демонстрация режимов иерархии:")
    hierarchy_modes = ['flat', 'tree', 'breadcrumb']
    
    for mode in hierarchy_modes:
        print(f"   Установка режима '{mode}'...")
        mode_settings = {
            'open_modal': True,
            'default_hierarchy_mode': mode,
            'show_hierarchy_controls': True,
            'auto_expand_groups': True
        }
        
        success = settings_service.set_work_selector_settings(user_id, mode_settings)
        if success:
            retrieved = settings_service.get_work_selector_settings(user_id)
            print(f"   ✅ Режим '{mode}' установлен: {retrieved['default_hierarchy_mode']}")
        else:
            print(f"   ❌ Ошибка установки режима '{mode}'")
    
    # 4. Возврат к настройкам по умолчанию
    print("\n4. Возврат к настройкам по умолчанию:")
    default_settings = {
        'open_modal': True,
        'default_hierarchy_mode': 'tree',
        'show_hierarchy_controls': True,
        'auto_expand_groups': True
    }
    
    success = settings_service.set_work_selector_settings(user_id, default_settings)
    if success:
        print("   ✅ Настройки по умолчанию восстановлены")
        final_settings = settings_service.get_work_selector_settings(user_id)
        print(f"   Финальные настройки: {final_settings}")
    else:
        print("   ❌ Ошибка восстановления настроек по умолчанию")
    
    print("\n" + "=" * 50)
    print("✅ Демонстрация завершена")


def demonstrate_settings_scenarios():
    """Демонстрация различных сценариев использования"""
    print("\n🎯 Сценарии использования настроек")
    print("=" * 50)
    
    settings_service = UserSettingsService()
    user_id = 4
    
    # Сценарий 1: Пользователь предпочитает работать в отдельном окне
    print("Сценарий 1: Работа в отдельном окне")
    window_settings = {
        'open_modal': False,
        'default_hierarchy_mode': 'tree',
        'show_hierarchy_controls': True,
        'auto_expand_groups': True
    }
    settings_service.set_work_selector_settings(user_id, window_settings)
    print("   ✅ Селектор будет открываться в отдельном окне")
    
    # Сценарий 2: Пользователь работает с большими списками работ
    print("\nСценарий 2: Работа с большими списками")
    performance_settings = {
        'open_modal': True,
        'default_hierarchy_mode': 'flat',
        'show_hierarchy_controls': False,
        'auto_expand_groups': False
    }
    settings_service.set_work_selector_settings(user_id, performance_settings)
    print("   ✅ Оптимизированы настройки для больших списков")
    
    # Сценарий 3: Пользователь часто работает с иерархией
    print("\nСценарий 3: Работа с иерархией работ")
    hierarchy_settings = {
        'open_modal': True,
        'default_hierarchy_mode': 'breadcrumb',
        'show_hierarchy_controls': True,
        'auto_expand_groups': True
    }
    settings_service.set_work_selector_settings(user_id, hierarchy_settings)
    print("   ✅ Настроены расширенные возможности иерархии")
    
    print("\n" + "=" * 50)
    print("✅ Все сценарии продемонстрированы")


if __name__ == "__main__":
    try:
        demonstrate_work_selector_settings()
        demonstrate_settings_scenarios()
    except Exception as e:
        print(f"❌ Ошибка выполнения примера: {e}")
        sys.exit(1)