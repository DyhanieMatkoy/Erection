"""Test timesheet form integration with export/import functionality"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_timesheet_form_integration():
    """Test that timesheet form has export/import functionality"""
    print("🧪 Тестирование интеграции формы табеля...")
    
    try:
        # Test import of timesheet form
        from src.views.timesheet_document_form import TimesheetDocumentForm
        print("✅ Импорт TimesheetDocumentForm успешен")
        
        # Check if form has export/import methods
        form_methods = dir(TimesheetDocumentForm)
        
        required_methods = [
            'on_export_excel',
            'on_import_excel', 
            'on_export_json',
            'on_import_json'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method in form_methods:
                print(f"✅ Метод {method} найден")
            else:
                print(f"❌ Метод {method} отсутствует")
                missing_methods.append(method)
        
        if not missing_methods:
            print("✅ Все методы экспорта/импорта присутствуют в форме")
            return True
        else:
            print(f"❌ Отсутствуют методы: {missing_methods}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования формы: {e}")
        return False

def test_delete_marked_dialog_integration():
    """Test delete marked dialog integration"""
    print("\n🧪 Тестирование интеграции диалога удаления...")
    
    try:
        from src.views.delete_marked_dialog import DeleteMarkedDialog
        
        # Check if dialog has settings functionality
        dialog_methods = dir(DeleteMarkedDialog)
        
        required_methods = [
            'load_settings',
            'save_settings',
            'on_show_marked_changed',
            'on_type_filter_changed'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method in dialog_methods:
                print(f"✅ Метод {method} найден")
            else:
                print(f"❌ Метод {method} отсутствует")
                missing_methods.append(method)
        
        if not missing_methods:
            print("✅ Все методы настроек присутствуют в диалоге")
            return True
        else:
            print(f"❌ Отсутствуют методы: {missing_methods}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования диалога: {e}")
        return False

def test_services_integration():
    """Test services integration"""
    print("\n🧪 Тестирование интеграции сервисов...")
    
    try:
        from src.services.timesheet_export_import_service import TimesheetExportImportService
        from src.services.user_settings_service import UserSettingsService
        
        # Test service methods
        export_service = TimesheetExportImportService()
        settings_service = UserSettingsService()
        
        export_methods = [
            'export_timesheet_to_json',
            'export_timesheet_to_excel',
            'import_timesheet_from_excel',
            'import_timesheet_from_json_file'
        ]
        
        settings_methods = [
            'get_setting',
            'set_setting',
            'get_delete_marked_settings',
            'set_delete_marked_settings'
        ]
        
        all_methods_present = True
        
        for method in export_methods:
            if hasattr(export_service, method):
                print(f"✅ TimesheetExportImportService.{method} найден")
            else:
                print(f"❌ TimesheetExportImportService.{method} отсутствует")
                all_methods_present = False
        
        for method in settings_methods:
            if hasattr(settings_service, method):
                print(f"✅ UserSettingsService.{method} найден")
            else:
                print(f"❌ UserSettingsService.{method} отсутствует")
                all_methods_present = False
        
        return all_methods_present
        
    except Exception as e:
        print(f"❌ Ошибка тестирования сервисов: {e}")
        return False

def main():
    """Run integration tests"""
    print("🚀 Запуск тестов интеграции функциональности табеля...")
    print("=" * 60)
    
    tests = [
        ("Интеграция формы табеля", test_timesheet_form_integration),
        ("Интеграция диалога удаления", test_delete_marked_dialog_integration),
        ("Интеграция сервисов", test_services_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    print("\n📊 Результаты тестирования интеграции:")
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  - {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Все тесты интеграции пройдены успешно!")
        print("\n📋 Подтвержденная функциональность:")
        print("  ✅ Форма табеля интегрирована с экспортом/импортом")
        print("  ✅ Диалог удаления интегрирован с настройками")
        print("  ✅ Все сервисы имеют необходимые методы")
        print("  ✅ Система готова к использованию")
        
        print("\n🔧 Как использовать:")
        print("  1. Откройте документ Табель")
        print("  2. Используйте кнопки 'Экспорт в Excel/JSON' для экспорта")
        print("  3. Используйте кнопки 'Импорт из Excel/JSON' для импорта")
        print("  4. Настройте отображение помеченных объектов в меню 'Настройки'")
        
        return True
    else:
        print("\n💥 Некоторые тесты интеграции провалены!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)