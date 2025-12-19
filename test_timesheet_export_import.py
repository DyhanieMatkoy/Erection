"""Test timesheet export/import functionality and delete marked objects dialog"""
import sys
import os
import tempfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Timesheet, TimesheetLine, Person, Object, Estimate
from src.services.timesheet_export_import_service import TimesheetExportImportService
from src.services.user_settings_service import UserSettingsService
from src.views.delete_marked_dialog import DeleteMarkedDialog


def test_delete_marked_dialog():
    """Test delete marked objects dialog with timesheet support"""
    print("🧪 Тестирование диалога удаления помеченных объектов...")
    
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    try:
        with db_manager.get_session() as session:
            # Create test timesheet and mark it for deletion
            test_timesheet = Timesheet(
                number="TEST-001",
                date=date.today(),
                month_year="12.2024",
                marked_for_deletion=True
            )
            session.add(test_timesheet)
            session.commit()
            
            print(f"✓ Создан тестовый табель ID: {test_timesheet.id}")
            
            # Test dialog
            dialog = DeleteMarkedDialog()
            
            # Check if timesheet appears in the list
            dialog.load_marked_objects()
            
            found_timesheet = False
            for row in range(dialog.table.rowCount()):
                type_item = dialog.table.item(row, 1)
                if type_item and type_item.text() == "Табель":
                    name_item = dialog.table.item(row, 2)
                    if name_item and name_item.text() == "TEST-001":
                        found_timesheet = True
                        break
            
            if found_timesheet:
                print("✓ Табель отображается в списке помеченных объектов")
            else:
                print("❌ Табель НЕ отображается в списке помеченных объектов")
            
            # Test settings
            settings_service = UserSettingsService()
            test_settings = {
                'show_marked_objects': True,
                'show_timesheets': True,
                'show_estimates': False
            }
            
            success = settings_service.set_delete_marked_settings(1, test_settings)
            if success:
                print("✓ Настройки сохранены")
            
            loaded_settings = settings_service.get_delete_marked_settings(1)
            if loaded_settings['show_marked_objects'] and loaded_settings['show_timesheets']:
                print("✓ Настройки загружены корректно")
            
            # Clean up
            session.delete(test_timesheet)
            session.commit()
            print("✓ Тестовые данные очищены")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    
    return True


def test_timesheet_export_import():
    """Test timesheet export/import functionality"""
    print("\n🧪 Тестирование экспорта/импорта табеля...")
    
    db_manager = DatabaseManager()
    export_service = TimesheetExportImportService()
    
    try:
        with db_manager.get_session() as session:
            # Create test data
            test_person = Person(
                full_name="Тестовый Сотрудник",
                position="Рабочий"
            )
            session.add(test_person)
            session.flush()
            
            test_timesheet = Timesheet(
                number="EXPORT-001",
                date=date.today(),
                month_year="12.2024",
                is_posted=False
            )
            session.add(test_timesheet)
            session.flush()
            
            # Add timesheet line
            test_line = TimesheetLine(
                timesheet_id=test_timesheet.id,
                line_number=1,
                employee_id=test_person.id,
                hourly_rate=500.0,
                day_01=8.0,
                day_02=8.0,
                total_hours=16.0,
                total_amount=8000.0
            )
            session.add(test_line)
            session.commit()
            
            print(f"✓ Создан тестовый табель ID: {test_timesheet.id}")
            
            # Test JSON export
            json_data = export_service.export_timesheet_to_json(test_timesheet.id)
            if json_data:
                print("✓ JSON экспорт работает")
                print(f"  - Номер документа: {json_data['document_info']['number']}")
                print(f"  - Количество строк: {len(json_data['lines'])}")
            else:
                print("❌ JSON экспорт не работает")
            
            # Test Excel export
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
                excel_path = tmp_file.name
            
            excel_success = export_service.export_timesheet_to_excel(test_timesheet.id, excel_path)
            if excel_success and os.path.exists(excel_path):
                print("✓ Excel экспорт работает")
                print(f"  - Файл создан: {excel_path}")
                
                # Test Excel import
                # First clear existing lines
                session.delete(test_line)
                session.commit()
                
                import_success, import_message = export_service.import_timesheet_from_excel(excel_path, test_timesheet.id)
                if import_success:
                    print("✓ Excel импорт работает")
                    print(f"  - {import_message}")
                else:
                    print(f"❌ Excel импорт не работает: {import_message}")
                
                # Clean up temp file
                os.unlink(excel_path)
            else:
                print("❌ Excel экспорт не работает")
            
            # Test JSON file export/import
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
                json_path = tmp_file.name
            
            json_file_success = export_service.export_timesheet_to_json_file(test_timesheet.id, json_path)
            if json_file_success:
                print("✓ JSON файл экспорт работает")
                
                # Clear lines for import test
                for line in session.query(TimesheetLine).filter_by(timesheet_id=test_timesheet.id).all():
                    session.delete(line)
                session.commit()
                
                # Test JSON import
                json_import_success, json_import_message = export_service.import_timesheet_from_json_file(json_path, test_timesheet.id)
                if json_import_success:
                    print("✓ JSON файл импорт работает")
                    print(f"  - {json_import_message}")
                else:
                    print(f"❌ JSON файл импорт не работает: {json_import_message}")
                
                # Clean up temp file
                os.unlink(json_path)
            else:
                print("❌ JSON файл экспорт не работает")
            
            # Clean up test data
            session.delete(test_timesheet)
            session.delete(test_person)
            session.commit()
            print("✓ Тестовые данные очищены")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("🚀 Запуск тестов функциональности табеля...")
    
    # Test 1: Delete marked objects dialog
    test1_success = test_delete_marked_dialog()
    
    # Test 2: Export/import functionality
    test2_success = test_timesheet_export_import()
    
    print("\n📊 Результаты тестирования:")
    print(f"  - Диалог удаления помеченных объектов: {'✅ ПРОЙДЕН' if test1_success else '❌ ПРОВАЛЕН'}")
    print(f"  - Экспорт/импорт табеля: {'✅ ПРОЙДЕН' if test2_success else '❌ ПРОВАЛЕН'}")
    
    if test1_success and test2_success:
        print("\n🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("\n💥 Некоторые тесты провалены!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)