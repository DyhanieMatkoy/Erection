"""Example of using timesheet export/import functionality"""
import sys
import os
from datetime import date

# Add src to path for example
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def example_timesheet_export_import():
    """Example of timesheet export/import operations"""
    print("📋 Пример использования экспорта/импорта табеля")
    print("=" * 50)
    
    # This is a demonstration of the API - actual usage requires database connection
    from services.timesheet_export_import_service import TimesheetExportImportService
    
    # Create service instance
    service = TimesheetExportImportService()
    
    print("\n1. 📤 Экспорт табеля в Excel:")
    print("   service.export_timesheet_to_excel(timesheet_id=123, file_path='Табель_001.xlsx')")
    print("   ✅ Создается файл Excel с печатной формой")
    
    print("\n2. 📥 Импорт табеля из Excel:")
    print("   success, message = service.import_timesheet_from_excel('Табель_001.xlsx', timesheet_id=123)")
    print("   ✅ Данные импортируются с поиском сотрудников по ФИО")
    
    print("\n3. 📤 Экспорт табеля в JSON:")
    print("   service.export_timesheet_to_json_file(timesheet_id=123, file_path='Табель_001.json')")
    print("   ✅ Создается структурированный JSON файл")
    
    print("\n4. 📥 Импорт табеля из JSON:")
    print("   success, message = service.import_timesheet_from_json_file('Табель_001.json', timesheet_id=123)")
    print("   ✅ Данные импортируются из JSON формата")

def example_user_settings():
    """Example of user settings for delete marked objects"""
    print("\n\n⚙️ Пример использования настроек пользователя")
    print("=" * 50)
    
    from services.user_settings_service import UserSettingsService
    
    # Create service instance
    settings_service = UserSettingsService()
    
    print("\n1. 📖 Получение настроек:")
    print("   settings = settings_service.get_delete_marked_settings(user_id=1)")
    print("   # Возвращает словарь с настройками отображения")
    
    print("\n2. 💾 Сохранение настроек:")
    print("   new_settings = {")
    print("       'show_marked_objects': True,")
    print("       'show_timesheets': True,")
    print("       'show_estimates': False")
    print("   }")
    print("   settings_service.set_delete_marked_settings(user_id=1, settings=new_settings)")
    
    print("\n3. 🔧 Индивидуальная настройка:")
    print("   settings_service.set_setting(user_id=1, key='delete_marked.show_timesheets', value=True)")

def example_delete_marked_dialog():
    """Example of delete marked objects dialog usage"""
    print("\n\n🗑️ Пример использования диалога удаления помеченных объектов")
    print("=" * 50)
    
    print("\n1. 📋 Отображение помеченных табелей:")
    print("   - Табели с marked_for_deletion=True теперь отображаются в списке")
    print("   - Можно настроить отображение через чекбоксы")
    
    print("\n2. ⚙️ Настройки отображения:")
    print("   - 'Отображать помеченные на удаление объекты в списке' - основной переключатель")
    print("   - Индивидуальные настройки для каждого типа объектов")
    print("   - По умолчанию помеченные объекты скрыты")
    
    print("\n3. 🔄 Операции:")
    print("   - Удаление выбранных объектов")
    print("   - Снятие пометки на удаление")
    print("   - Массовые операции с подтверждением")

def main():
    """Run all examples"""
    print("🚀 Примеры использования функциональности табеля")
    print("=" * 60)
    
    try:
        example_timesheet_export_import()
        example_user_settings()
        example_delete_marked_dialog()
        
        print("\n\n📚 Дополнительная информация:")
        print("- Подробная документация: TIMESHEET_FUNCTIONALITY_IMPLEMENTATION_SUMMARY.md")
        print("- Тесты функциональности: test_timesheet_functionality_simple.py")
        print("- Исходный код сервисов: src/services/")
        
        print("\n✅ Все примеры показаны успешно!")
        
    except ImportError as e:
        print(f"\n⚠️ Примечание: Для запуска примеров требуется инициализированная база данных")
        print(f"Ошибка импорта: {e}")
        print("\nЭто нормально - примеры показывают API для использования в приложении")

if __name__ == "__main__":
    main()